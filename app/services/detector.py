import cv2
from ultralytics import YOLO
import math
from collections import deque
import numpy as np
import os

# Importaciones ajustadas
from app.core.database import guardar_alerta
from app.services.telegram_bot import enviar_telegram
from app.core.config import *

# Rutas (ajústalas según tu estructura)
MODELO_PATH = "ml/best.pt"
VIDEO_PATH = "ml/videos/ejem1.mp4"

modelo = YOLO(MODELO_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

# ─── UMBRALES ────────────────────────────────────────────────
CONFIANZA_MIN          = 0.3
DISTANCIA_PELIGRO      = 200
CRECIMIENTO_ACELERANDO = 1.15
CRECIMIENTO_FRENANDO   = 0.98
FRAMES_FRENADO_MIN     = 2
FRAMES_ALERTA          = 90    # ~3 segundos a 30fps
confianza_moto = 0  # Agrega esta línea

# ─── ESTADO ──────────────────────────────────────────────────
historial_tamanos   = deque(maxlen=5)
contador_freno      = 0
frames_alerta       = 0
total_alertas       = 0
frame_num           = 0

def obtener_estado_moto(historial):
    if len(historial) < 2 or historial[-2] == 0:
        return "DESCONOCIDO"
    ratio = historial[-1] / historial[-2]
    if ratio > CRECIMIENTO_ACELERANDO:
        return "ACELERANDO"
    elif ratio < CRECIMIENTO_FRENANDO:
        return "FRENANDO"
    return "ESTABLE"

print("Presiona ESC para salir | Q para pausar")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_num += 1
    
    if frame_num % 3 != 0:  # Procesa 1 de cada 3 frames
        continue
    resultados = modelo(frame, verbose=False)

    moto_bbox    = None
    persona_bbox = None
    tamano_moto  = 0

    for box in resultados[0].boxes:
        clase     = int(box.cls[0])
        confianza = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if confianza < CONFIANZA_MIN:
            continue

        if clase == 3:   # motorbike
            moto_bbox   = (x1, y1, x2, y2)
            tamano_moto = (x2 - x1) * (y2 - y1)
            confianza_moto = confianza
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 140, 0), 2)
            cv2.putText(frame, f"moto {confianza:.2f}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 140, 0), 2)

        elif clase == 4:  # person
            persona_bbox = (x1, y1, x2, y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
            cv2.putText(frame, f"persona {confianza:.2f}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 0), 2)

    # ─── CONDICIÓN 1: CERCANÍA ───────────────────────────────
    cerca     = False
    distancia = 0

    if moto_bbox and persona_bbox:
        cx_m = (moto_bbox[0] + moto_bbox[2]) // 2
        cy_m = (moto_bbox[1] + moto_bbox[3]) // 2
        cx_p = (persona_bbox[0] + persona_bbox[2]) // 2
        cy_p = (persona_bbox[1] + persona_bbox[3]) // 2

        distancia    = math.sqrt((cx_m - cx_p)**2 + (cy_m - cy_p)**2)
        color_linea  = (0, 0, 255) if distancia < DISTANCIA_PELIGRO else (100, 100, 100)
        cv2.line(frame, (cx_m, cy_m), (cx_p, cy_p), color_linea, 2)

        if distancia < DISTANCIA_PELIGRO:
            cerca = True

    # ─── CONDICIÓN 2 y 3: FRENO + ACELERACIÓN ────────────────
    historial_tamanos.append(tamano_moto)
    estado_actual = obtener_estado_moto(historial_tamanos)

    if estado_actual == "FRENANDO":
        contador_freno += 1
    elif estado_actual == "ACELERANDO":
        if contador_freno >= FRAMES_FRENADO_MIN and cerca:
            frames_alerta  = FRAMES_ALERTA
            total_alertas += 1
            
            # --- GUARDAR EN BD Y ENVIAR TELEGRAM ---
            # --- GUARDAR EN BD Y ENVIAR TELEGRAM ---
            try:
                # Redimensionar si es muy grande
                alto, ancho = frame.shape[:2]
                if alto > 800 or ancho > 800:
                    frame_pequeno = cv2.resize(frame, (ancho//2, alto//2))
                else:
                    frame_pequeno = frame
                
                # Convertir a JPEG con calidad 70%
                _, foto1_buffer = cv2.imencode('.jpg', frame_pequeno, [cv2.IMWRITE_JPEG_QUALITY, 70])
                _, foto2_buffer = cv2.imencode('.jpg', frame_pequeno, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                # Convertir a bytes
                foto1_bytes = foto1_buffer.tobytes()
                foto2_bytes = foto2_buffer.tobytes()
                
                # Guardar en base de datos
                alerta_id = guardar_alerta(foto1_bytes, foto2_bytes, confianza_moto, int(distancia))
                
                # Enviar a Telegram
                enviar_telegram(foto1_bytes, foto2_bytes, int(distancia), confianza_moto)
                
                print(f"✅ ALERTA #{total_alertas} | ID:{alerta_id} | dist {int(distancia)}px")
            except Exception as e:
                print(f"Error al guardar alerta: {e}")
            # ----------------------------------------
            # ----------------------------------------
            
        contador_freno = 0
    else:
        contador_freno = 0

    # ─── HUD ─────────────────────────────────────────────────
    color_dist   = (0, 0, 255) if cerca else (200, 200, 200)
    color_estado = (0, 0, 255) if estado_actual == "FRENANDO" else \
                   (0, 200, 255) if estado_actual == "ACELERANDO" else (200, 200, 200)

    cv2.putText(frame, f"Distancia: {int(distancia)}px", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_dist, 2)
    cv2.putText(frame, f"Moto: {estado_actual}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_estado, 2)
    cv2.putText(frame, f"Freno: {contador_freno} frames", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    cv2.putText(frame, f"Alertas: {total_alertas}", (10, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    # ─── ALERTA VISUAL ───────────────────────────────────────
    if frames_alerta > 0:
        frames_alerta -= 1
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 75), (0, 0, 180), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
        cv2.putText(frame, "ALERTA: POSIBLE ROBO", (20, 52),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)

    cv2.imshow("Detector - 3 Condiciones", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key == ord('q'):
        cv2.waitKey(0)

cap.release()
cv2.destroyAllWindows()
print(f"Terminado. Total alertas: {total_alertas}")