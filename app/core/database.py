# app/core/database.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "antirobos_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password")
    )

def guardar_alerta(foto1_url: str, foto2_url: str, confianza: float, distancia: int,
                   tipo_evento: str = "normal", arma_utilizada: str = "ninguna",
                   testigos: int = 0, descripcion: str = None):
    """Guardar alerta con URLs de S3 y análisis de GPT"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO alertas (foto1_url, foto2_url, moto_confianza, distancia_moto_persona, 
                             tipo_evento, arma_utilizada, testigos, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (foto1_url, foto2_url, confianza, distancia, tipo_evento, arma_utilizada, testigos, descripcion))
    
    alerta_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Alerta guardada - ID: {alerta_id} | Tipo: {tipo_evento} | Arma: {arma_utilizada} | Testigos: {testigos}")
    return alerta_id

def obtener_alertas(limit: int = 500):
    """Obtener todas las alertas con análisis"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona,
               telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
        FROM alertas 
        ORDER BY fecha DESC 
        LIMIT %s
    """, (limit,))
    
    alertas = []
    for row in cur.fetchall():
        alertas.append({
            "id": row[0],
            "fecha": row[1],
            "foto1_url": row[2],
            "foto2_url": row[3],
            "moto_confianza": row[4],
            "distancia": row[5],
            "telegram_enviado": row[6],
            "estado": row[7],
            "tipo_evento": row[8] or "normal",
            "arma_utilizada": row[9] or "ninguna",
            "testigos": row[10] or 0,
            "descripcion": row[11] or ""
        })
    
    cur.close()
    conn.close()
    return alertas