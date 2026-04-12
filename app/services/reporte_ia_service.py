# app/services/reporte_ia_service.py
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_reporte_ia(alertas: list, tipo: str, fecha_inicio: str = None, fecha_fin: str = None):
    """
    Genera un reporte de seguridad usando GPT basado en estadísticas agregadas
    """
    if not alertas:
        return "No hay eventos en el período seleccionado."
    
    total = len(alertas)
    
    # Estadísticas de tipos de evento
    tipos = {}
    for a in alertas:
        tipo_evento = a.get('tipo_evento', 'normal')
        tipos[tipo_evento] = tipos.get(tipo_evento, 0) + 1
    
    # Estadísticas de armas
    armas = {}
    for a in alertas:
        arma = a.get('arma_utilizada', 'ninguna')
        armas[arma] = armas.get(arma, 0) + 1
    
    # 👈 CORREGIDO: convertir testigos a entero
    total_testigos = 0
    for a in alertas:
        testigo = a.get('testigos', 0)
        try:
            total_testigos += int(testigo) if testigo else 0
        except (ValueError, TypeError):
            total_testigos += 0
    
    # Horarios
    horarios = {'madrugada (00-06)': 0, 'mañana (06-12)': 0, 'tarde (12-18)': 0, 'noche (18-24)': 0}
    for a in alertas:
        fecha = a.get('fecha')
        if hasattr(fecha, 'hour'):
            hora = fecha.hour
        else:
            hora = 0
        if hora < 6:
            horarios['madrugada (00-06)'] += 1
        elif hora < 12:
            horarios['mañana (06-12)'] += 1
        elif hora < 18:
            horarios['tarde (12-18)'] += 1
        else:
            horarios['noche (18-24)'] += 1
    
    # Confianza promedio
    confianza_promedio = sum(a.get('moto_confianza', 0) for a in alertas) / total if total > 0 else 0
    
    # Distancia promedio
    distancia_promedio = sum(a.get('distancia_moto_persona', 0) for a in alertas) / total if total > 0 else 0
    
    # Ejemplos (solo 3 eventos representativos)
    ejemplos = []
    for a in alertas[:3]:
        fecha_str = a.get('fecha').strftime('%d/%m %H:%M') if hasattr(a.get('fecha'), 'strftime') else str(a.get('fecha', ''))
        ejemplos.append(f"- {fecha_str}: {a.get('tipo_evento', 'normal')} | {a.get('descripcion', 'Sin descripción')[:80]}")
    
    # Determinar período
    if tipo == 'day':
        periodo = f"Día {fecha_inicio}"
    elif tipo == 'week':
        periodo = f"Semana del {fecha_inicio} al {fecha_fin}"
    elif tipo == 'month':
        from datetime import datetime
        periodo = f"Mes de {datetime.now().strftime('%B %Y')}"
    else:
        periodo = f"Del {fecha_inicio} al {fecha_fin}"
    
    prompt = f"""
    Eres un analista de seguridad. Genera un reporte profesional basado en estas estadísticas:

    PERÍODO: {periodo}
    TOTAL EVENTOS: {total}

    TIPOS DE EVENTO:
    {tipos}

    ARMAS UTILIZADAS:
    {armas}

    HORARIOS:
    {horarios}

    MÉTRICAS:
    - Confianza promedio de detección: {confianza_promedio*100:.1f}%
    - Distancia promedio moto-persona: {distancia_promedio:.0f}px
    - Total de testigos reportados: {total_testigos}

    EJEMPLOS DE EVENTOS (últimos 3):
    {chr(10).join(ejemplos)}

    Genera un reporte con:
    1. Resumen ejecutivo
    2. Delitos más frecuentes (top 3)
    3. Horarios peligrosos
    4. Uso de armas
    5. Recomendaciones de seguridad (5 puntos)

    Usa lenguaje profesional pero claro.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error generando reporte IA: {e}")
        return f"Error generando reporte: {e}"