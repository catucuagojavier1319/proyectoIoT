# app/services/openai_service.py
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_image(image_url: str) -> dict:
    """
    Analiza una imagen y determina si es un robo o situación peligrosa.
    Retorna: {"is_robo": bool, "reason": str}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analista de seguridad. Responde SOLO en formato JSON: {\"is_robo\": true/false, \"reason\": \"explicación breve\"}"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza esta imagen: ¿hay una persona siendo atracada por un motorizado? ¿Hay situación de robo o arrebato?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return {
            "is_robo": result.get("is_robo", False),
            "reason": result.get("reason", "No se pudo determinar")
        }
        
    except Exception as e:
        print(f"❌ Error analizando con GPT: {e}")
        return {"is_robo": False, "reason": f"Error: {e}"}