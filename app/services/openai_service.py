# app/services/openai_service.py
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_image(image_url: str) -> dict:
    """
    Analiza una imagen y clasifica el evento.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Eres un analista de seguridad. Clasifica la imagen en UNA de estas categorías:
                    - arrebato: robo rápido donde el motorizado jala una pertenencia
                    - asalto: con amenaza o violencia explícita
                    - entrega de encomienda: moto entregando paquete/comida
                    - transporte: persona en moto normal
                    - normal: situación cotidiana sin riesgo
                    - sospechoso: comportamiento extraño
                    
                    Responde SOLO en formato JSON. Ejemplo: {"tipo_evento": "normal", "arma_utilizada": "ninguna", "testigos": 0, "descripcion": "sin incidentes"}"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza esta imagen y clasifícala."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        return {
            "tipo_evento": result.get("tipo_evento", "normal"),
            "arma_utilizada": result.get("arma_utilizada", "ninguna"),
            "testigos": result.get("testigos", 0),
            "descripcion": result.get("descripcion", "Sin información")
        }
        
    except Exception as e:
        print(f"❌ Error analizando con GPT: {e}")
        return {
            "tipo_evento": "normal",
            "arma_utilizada": "ninguna",
            "testigos": 0,
            "descripcion": f"Error: {e}"
        }