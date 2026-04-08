# app/services/detection_service.py
import cv2
import base64
import numpy as np
from ultralytics import YOLO
import math

MODELO_PATH = "yolov8n.pt"
CONFIANZA_MIN = 0.4
DISTANCIA_PELIGRO = 150  # px de distancia entre moto y persona

class DetectionService:
    def __init__(self):
        self.modelo = YOLO(MODELO_PATH)
        self.frame_num = 0
    
    def decode_image(self, base64_string):
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        img_bytes = base64.b64decode(base64_string)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    def procesar_frame(self, frame_base64):
        try:
            frame = self.decode_image(frame_base64)
            self.frame_num += 1
            
            # Procesar cada 2 frames
            if self.frame_num % 2 != 0:
                return {"detected": False}
            
            resultados = self.modelo(frame, verbose=False)
            
            moto_bbox = None
            persona_bbox = None
            confianza_moto = 0
            
            for box in resultados[0].boxes:
                clase = int(box.cls[0])
                confianza = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                if confianza < CONFIANZA_MIN:
                    continue
                
                if clase == 3:  # moto
                    moto_bbox = (x1, y1, x2, y2)
                    confianza_moto = confianza
                    
                elif clase == 0:  # persona
                    persona_bbox = (x1, y1, x2, y2)
            
            # Solo alerta si hay moto Y persona cerca
            if moto_bbox and persona_bbox:
                # Centro de la moto
                cx_m = (moto_bbox[0] + moto_bbox[2]) // 2
                cy_m = (moto_bbox[1] + moto_bbox[3]) // 2
                
                # Centro de la persona
                cx_p = (persona_bbox[0] + persona_bbox[2]) // 2
                cy_p = (persona_bbox[1] + persona_bbox[3]) // 2
                
                # Distancia entre centros
                distancia = math.sqrt((cx_m - cx_p)**2 + (cy_m - cy_p)**2)
                
                # Si están muy cerca → ALERTA
                if distancia < DISTANCIA_PELIGRO:
                    # Guardar frame
                    alto, ancho = frame.shape[:2]
                    if alto > 800 or ancho > 800:
                        frame = cv2.resize(frame, (ancho//2, alto//2))
                    
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_bytes = buffer.tobytes()
                    
                    print(f"🚨 ALERTA! Moto y persona cerca - Distancia: {int(distancia)}px")
                    
                    return {
                        "detected": True,
                        "confidence": round(confianza_moto, 2),
                        "distance": int(distancia),
                        "state": "PELIGRO",
                        "message": "🚨 ¡Moto y persona muy cerca!",
                        "frame_bytes": frame_bytes
                    }
            
            return {"detected": False}
            
        except Exception as e:
            print(f"Error: {e}")
            return {"detected": False}