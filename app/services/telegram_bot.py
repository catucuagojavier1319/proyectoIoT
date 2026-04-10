# app/services/telegram_bot.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_telegram(foto1_url: str, foto2_url: str, distancia: float, confianza: float, analisis: str = None):
    """Enviar alerta a Telegram con URLs de S3 y análisis de GPT"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        # Caption base
        caption = f"🚨 ALERTA DE SEGURIDAD\n\n📏 Distancia: {distancia}px\n🎯 Confianza: {confianza:.1f}%"
        
        # Agregar análisis de GPT si existe
        if analisis:
            caption += f"\n\n Análisis IA:\n{analisis}"
        
        # Enviar primera foto con caption
        response1 = requests.post(
            url,
            data={
                'chat_id': CHAT_ID, 
                'caption': caption,
                'photo': foto1_url
            }
        )
        
        # Enviar segunda foto (sin caption para no repetir)
        response2 = requests.post(
            url,
            data={
                'chat_id': CHAT_ID,
                'photo': foto2_url
            }
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            print("✅ Alertas enviadas a Telegram")
        else:
            print(f"❌ Error Telegram: {response1.status_code} - {response1.text}")
            
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")