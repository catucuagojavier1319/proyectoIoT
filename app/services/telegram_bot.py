import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def enviar_telegram(foto1_bytes, foto2_bytes, distancia, confianza, fecha=None):
    """Enviar alerta a Telegram con 2 imágenes"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        if fecha:
            caption = f"ALERTA DE SEGURIDAD\n📅 {fecha}\n Distancia: {distancia}px\n Confianza: {confianza:.1f}%"
        else:
            caption = f"ALERTA DE SEGURIDAD\n Distancia: {distancia}px\n Confianza: {confianza:.1f}%"
        
        # Primera foto con mensaje
        response1 = requests.post(
            url,
            data={'chat_id': CHAT_ID, 'caption': caption},
            files={'photo': ('alerta1.jpg', foto1_bytes, 'image/jpeg')}
        )
        
        # Segunda foto
        response2 = requests.post(
            url,
            data={'chat_id': CHAT_ID},
            files={'photo': ('alerta2.jpg', foto2_bytes, 'image/jpeg')}
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            print(" Alertas enviadas a Telegram")
        else:
            print(f"Error Telegram: {response1.status_code}")
            
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def enviar_mensaje_simple(mensaje):
    """Enviar solo texto a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': mensaje})
    except Exception as e:
        print(f"Error: {e}")