# app/api/detection.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict
import base64
import json
from datetime import datetime

from app.services.detection_service import DetectionService
from app.services.s3_service import upload_image_to_s3
from app.services.openai_service import analyze_image 
from app.core.database import guardar_alerta
from app.services.telegram_bot import enviar_telegram

router = APIRouter(prefix="/api/detection", tags=["deteccion"])

active_sessions: Dict[str, DetectionService] = {}

class FrameRequest(BaseModel):
    image: str

class FrameResponse(BaseModel):
    detected: bool
    message: str
    confidence: Optional[float] = None
    distance: Optional[int] = None
    state: Optional[str] = None
    alert_id: Optional[int] = None

# Tipos peligrosos que activan Telegram
TIPOS_PELIGROSOS = ["arrebato", "asalto", "sospechoso"]

@router.post("/detect", response_model=FrameResponse)
async def detect_frame(request: FrameRequest):
    try:
        detection_service = DetectionService()
        result = detection_service.procesar_frame(request.image)
        
        alert_id = None
        if result.get("detected") and result.get("frame_bytes"):
            try:
                image_url = upload_image_to_s3(result["frame_bytes"])
                
                if image_url:
                    # Analizar con GPT
                    analysis = analyze_image(image_url)
                    print(f"🤖 GPT: {analysis}")
                    
                    # Guardar en BD con análisis
                    alert_id = guardar_alerta(
                        foto1_url=image_url,
                        foto2_url=image_url,
                        confianza=result.get("confidence", 0.5),
                        distancia=result.get("distance", 0),
                        tipo_evento=analysis.get("tipo_evento", "normal"),
                        arma_utilizada=analysis.get("arma_utilizada", "ninguna"),
                        testigos=analysis.get("testigos", 0),
                        descripcion=analysis.get("descripcion", "")
                    )
                    
                    # Solo enviar Telegram si es tipo peligroso
                    if analysis.get("tipo_evento") in TIPOS_PELIGROSOS:
                        enviar_telegram(
                            foto1_url=image_url,
                            foto2_url=image_url,
                            distancia=result.get("distance", 0),
                            confianza=result.get("confidence", 0),
                            tipo_evento=analysis.get("tipo_evento"),
                            arma_utilizada=analysis.get("arma_utilizada"),
                            analisis=analysis.get("descripcion")
                        )
                        print(f"✅ ALERTA ENVIADA A TELEGRAM - ID: {alert_id} | Tipo: {analysis.get('tipo_evento')}")
                    else:
                        print(f"📝 Alerta guardada sin Telegram - Tipo: {analysis.get('tipo_evento')}")
                else:
                    print("❌ Error subiendo a S3")
            except Exception as e:
                print(f"Error guardando alerta: {e}")
        
        return FrameResponse(
            detected=result.get("detected", False),
            message=result.get("message", "Procesado"),
            confidence=result.get("confidence"),
            distance=result.get("distance"),
            state=result.get("state"),
            alert_id=alert_id
        )
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{session_id}")
async def websocket_detect(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"🔌 WebSocket conectado: {session_id}")
    
    if session_id not in active_sessions:
        active_sessions[session_id] = DetectionService()
    
    detector = active_sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            frame_base64 = frame_data.get("frame")
            
            result = detector.procesar_frame(frame_base64)
            
            print(f"🔍 Resultado: detected={result.get('detected')}")
            
            alert_id = None
            if result.get("detected") and result.get("frame_bytes"):
                try:
                    print(f"💾 Subiendo a S3...")
                    image_url = upload_image_to_s3(result["frame_bytes"])
                    
                    if image_url:
                        # Analizar con GPT
                        analysis = analyze_image(image_url)
                        print(f"🤖 GPT: {analysis}")
                        
                        # Guardar en BD con análisis
                        alert_id = guardar_alerta(
                            foto1_url=image_url,
                            foto2_url=image_url,
                            confianza=result.get("confidence", 0.5),
                            distancia=result.get("distance", 0),
                            tipo_evento=analysis.get("tipo_evento", "normal"),
                            arma_utilizada=analysis.get("arma_utilizada", "ninguna"),
                            testigos=analysis.get("testigos", 0),
                            descripcion=analysis.get("descripcion", "")
                        )
                        
                        # Solo enviar Telegram si es tipo peligroso
                        if analysis.get("tipo_evento") in TIPOS_PELIGROSOS:
                            enviar_telegram(
                                image_url, image_url,
                                result.get("distance", 0),
                                result.get("confidence", 0),
                                analysis.get("descripcion", "")
                            )
                            print(f"✅ ALERTA ENVIADA A TELEGRAM - ID: {alert_id} | Tipo: {analysis.get('tipo_evento')}")
                        else:
                            print(f"📝 Alerta guardada sin Telegram - Tipo: {analysis.get('tipo_evento')}")
                        
                        result["alert_id"] = alert_id
                    else:
                        print("❌ Error subiendo a S3")
                        
                except Exception as e:
                    print(f"❌ Error guardando alerta: {e}")
            
            await websocket.send_json({
                "detected": result.get("detected", False),
                "message": result.get("message", "Procesado"),
                "confidence": result.get("confidence"),
                "distance": result.get("distance"),
                "state": result.get("state"),
                "alert_id": alert_id
            })
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket desconectado: {session_id}")
        if session_id in active_sessions:
            del active_sessions[session_id]
    except Exception as e:
        print(f"❌ Error en WebSocket: {e}")

@router.post("/reset")
async def reset_detection():
    for session_id in active_sessions:
        active_sessions[session_id].reset_state()
    return {"message": "Todos los detectores reiniciados"}