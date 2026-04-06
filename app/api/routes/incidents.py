from fastapi import APIRouter, HTTPException, Query
import base64
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@router.get("/")
def get_alertas(limit: int = Query(50, ge=1, le=500)):
    """Listar alertas recientes"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado
        FROM alertas 
        ORDER BY fecha DESC 
        LIMIT %s
    """, (limit,))
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{
        "id": r[0],
        "fecha": r[1].isoformat(),
        "moto_confianza": r[2],
        "distancia": r[3],
        "telegram_enviado": r[4],
        "estado": r[5]
    } for r in resultados]

@router.get("/{alerta_id}/imagenes")
def get_imagenes(alerta_id: int):
    """Obtener imágenes en base64"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT foto1_blob, foto2_blob FROM alertas WHERE id = %s", (alerta_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {
        "id": alerta_id,
        "foto1_base64": base64.b64encode(row[0]).decode('utf-8'),
        "foto2_base64": base64.b64encode(row[1]).decode('utf-8')
    }

@router.get("/{alerta_id}")
def get_alerta(alerta_id: int):
    """Detalle de una alerta"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado
        FROM alertas WHERE id = %s
    """, (alerta_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {
        "id": row[0],
        "fecha": row[1].isoformat(),
        "moto_confianza": row[2],
        "distancia": row[3],
        "telegram_enviado": row[4],
        "estado": row[5]
    }

@router.patch("/{alerta_id}/estado")
def update_estado(alerta_id: int, estado: str = Query(..., regex="^(pendiente|revisado|falso)$")):
    """Actualizar estado: pendiente, revisado, falso"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE alertas SET estado = %s WHERE id = %s", (estado, alerta_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Estado actualizado", "id": alerta_id, "estado": estado}

@router.get("/stats/resumen")
def get_stats():
    """Estadísticas generales"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN telegram_enviado THEN 1 END) as enviados,
            COUNT(CASE WHEN estado = 'pendiente' THEN 1 END) as pendientes,
            COUNT(CASE WHEN estado = 'revisado' THEN 1 END) as revisados,
            COUNT(CASE WHEN estado = 'falso' THEN 1 END) as falsos,
            AVG(moto_confianza) as avg_confianza,
            AVG(distancia_moto_persona) as avg_distancia
        FROM alertas
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return {
        "total_alertas": row[0] or 0,
        "telegram_enviados": row[1] or 0,
        "pendientes": row[2] or 0,
        "revisados": row[3] or 0,
        "falsos": row[4] or 0,
        "confianza_promedio": round(row[5], 2) if row[5] else 0,
        "distancia_promedio": round(row[6], 2) if row[6] else 0
    }