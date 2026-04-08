# app/api/detection.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict
import base64
import json
from datetime import datetime

from app.services.detection_service import DetectionService
from app.core.database import guardar_alerta
from app.services.telegram_bot import enviar_telegram

router = APIRouter(prefix="/api/detection", tags=["deteccion"])

# Almacenar sesiones activas
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

# Endpoint HTTP
@router.post("/detect", response_model=FrameResponse)
async def detect_frame(request: FrameRequest):
    try:
        detection_service = DetectionService()
        result = detection_service.procesar_frame(request.image)
        
        alert_id = None
        if result.get("detected") and result.get("frame_bytes"):
            try:
                # ✅ Sin argumentos nombrados
                alert_id = guardar_alerta(
                    result["frame_bytes"],
                    result["frame_bytes"],
                    result.get("confidence", 0.5),
                    result.get("distance", 0)
                )
                await enviar_telegram(
                    result["frame_bytes"], 
                    result["frame_bytes"], 
                    result.get("distance", 0), 
                    result.get("confidence", 0)
                )
                print(f"✅ ALERTA GUARDADA - ID: {alert_id}")
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

# WebSocket para tiempo real
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
            
            print(f"🔍 Resultado: detected={result.get('detected')}, has_frame_bytes={result.get('frame_bytes') is not None}")
            
            alert_id = None
            if result.get("detected") and result.get("frame_bytes"):
                try:
                    print(f"💾 Guardando alerta...")
                    # ✅ Sin argumentos nombrados
                    alert_id = guardar_alerta(
                        result["frame_bytes"],
                        result["frame_bytes"],
                        result.get("confidence", 0.5),
                        result.get("distance", 0)
                    )
                    await enviar_telegram(
                        result["frame_bytes"], 
                        result["frame_bytes"], 
                        result.get("distance", 0), 
                        result.get("confidence", 0),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    result["alert_id"] = alert_id
                    print(f"✅ ALERTA GUARDADA - ID: {alert_id}")
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