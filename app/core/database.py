import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def guardar_alerta(foto1_bytes, foto2_bytes, confianza_moto, distancia):
    """Guardar alerta en base de datos"""
    if not isinstance(foto1_bytes, bytes):
        foto1_bytes = foto1_bytes.tobytes() if hasattr(foto1_bytes, 'tobytes') else bytes(foto1_bytes)
    if not isinstance(foto2_bytes, bytes):
        foto2_bytes = foto2_bytes.tobytes() if hasattr(foto2_bytes, 'tobytes') else bytes(foto2_bytes)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO alertas (foto1_blob, foto2_blob, moto_confianza, distancia_moto_persona)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (foto1_bytes, foto2_bytes, confianza_moto, distancia))
    
    alerta_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return alerta_id

def obtener_alertas(limit=50):
    """Obtener alertas recientes"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado
        FROM alertas ORDER BY fecha DESC LIMIT %s
    """, (limit,))
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return resultados