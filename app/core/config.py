import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Detección - Umbrales
CONFIANZA_MIN = float(os.getenv("CONFIANZA_MIN", 0.5))
DISTANCIA_PELIGRO = int(os.getenv("DISTANCIA_PELIGRO", 150))
CRECIMIENTO_ACELERANDO = float(os.getenv("CRECIMIENTO_ACELERANDO", 1.15))
CRECIMIENTO_FRENANDO = float(os.getenv("CRECIMIENTO_FRENANDO", 0.95))
FRAMES_FRENADO_MIN = int(os.getenv("FRAMES_FRENADO_MIN", 3))
FRAMES_ALERTA = int(os.getenv("FRAMES_ALERTA", 90))

# Rutas
MODELO_PATH = os.getenv("MODELO_PATH", "ml/best.pt")
VIDEOS_PATH = os.getenv("VIDEOS_PATH", "ml/videos")