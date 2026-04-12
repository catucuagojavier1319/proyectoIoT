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
    """Listar alertas recientes con URLs de S3 y análisis GPT"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
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
        "foto1_url": r[2],
        "foto2_url": r[3],
        "moto_confianza": r[4],
        "distancia": r[5],
        "telegram_enviado": r[6],
        "estado": r[7],
        "tipo_evento": r[8] if len(r) > 8 else "normal",
        "arma_utilizada": r[9] if len(r) > 9 else "ninguna",
        "testigos": r[10] if len(r) > 10 else 0,
        "descripcion": r[11] if len(r) > 11 else ""
    } for r in resultados]

@router.get("/{alerta_id}/imagenes")
def get_imagenes(alerta_id: int):
    """Obtener URLs de las imágenes desde S3"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT foto1_url, foto2_url FROM alertas WHERE id = %s", (alerta_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {
        "id": alerta_id,
        "foto1_url": row[0],
        "foto2_url": row[1]
    }

@router.get("/{alerta_id}")
def get_alerta(alerta_id: int):
    """Detalle de una alerta con análisis completo"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona, 
               telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
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
        "foto1_url": row[2],
        "foto2_url": row[3],
        "moto_confianza": row[4],
        "distancia": row[5],
        "telegram_enviado": row[6],
        "estado": row[7],
        "tipo_evento": row[8] if len(row) > 8 else "normal",
        "arma_utilizada": row[9] if len(row) > 9 else "ninguna",
        "testigos": row[10] if len(row) > 10 else 0,
        "descripcion": row[11] if len(row) > 11 else ""
    }

@router.patch("/{alerta_id}/estado")
def update_estado(alerta_id: int, estado: str = Query(..., pattern="^(pendiente|revisado|falso)$")):
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
    """Estadísticas generales incluyendo tipos de evento"""
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
            AVG(distancia_moto_persona) as avg_distancia,
            COUNT(CASE WHEN tipo_evento = 'arrebato' THEN 1 END) as arrebatos,
            COUNT(CASE WHEN tipo_evento = 'asalto' THEN 1 END) as asaltos,
            COUNT(CASE WHEN tipo_evento = 'sospechoso' THEN 1 END) as sospechosos,
            COUNT(CASE WHEN tipo_evento NOT IN ('arrebato', 'asalto', 'sospechoso') THEN 1 END) as normales
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
        "distancia_promedio": round(row[6], 2) if row[6] else 0,
        "arrebatos": row[7] or 0,
        "asaltos": row[8] or 0,
        "sospechosos": row[9] or 0,
        "normales": row[10] or 0
    }