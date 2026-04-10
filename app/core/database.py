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

def guardar_alerta(foto1_url: str, foto2_url: str, confianza: float, distancia: int):
    """Guardar alerta con URLs de S3 (sin imágenes BLOB)"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO alertas (foto1_url, foto2_url, moto_confianza, distancia_moto_persona)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (foto1_url, foto2_url, confianza, distancia))
    
    alerta_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Alerta guardada en BD - ID: {alerta_id} | URL: {foto1_url}")
    return alerta_id

def obtener_alertas(limit: int = 50):
    """Obtener todas las alertas con URLs"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado
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
            "estado": row[7]
        })
    
    cur.close()
    conn.close()
    return alertas