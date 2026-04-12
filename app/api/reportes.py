# app/api/reportes.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_connection
from app.services.pdf_service import generar_pdf_reporte
from app.services.reporte_ia_service import generar_reporte_ia  # 👈 Importar

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])

@router.get("/pdf")
async def generar_reporte(
    tipo: str = Query(..., pattern="^(day|week|month|custom)$"),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
):
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Construir filtro de fechas
        if tipo == 'day':
            fecha = datetime.now().date()
            cur.execute("""
                SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona,
                       telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
                FROM alertas 
                WHERE DATE(fecha) = %s
                ORDER BY fecha DESC
            """, (fecha,))
            fecha_inicio = fecha.strftime("%Y-%m-%d")
            fecha_fin = fecha.strftime("%Y-%m-%d")
        elif tipo == 'week':
            fecha = datetime.now().date()
            inicio_semana = fecha - timedelta(days=fecha.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            cur.execute("""
                SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona,
                       telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
                FROM alertas 
                WHERE DATE(fecha) BETWEEN %s AND %s
                ORDER BY fecha DESC
            """, (inicio_semana, fin_semana))
            fecha_inicio = inicio_semana.strftime("%Y-%m-%d")
            fecha_fin = fin_semana.strftime("%Y-%m-%d")
        elif tipo == 'month':
            fecha_actual = datetime.now()
            cur.execute("""
                SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona,
                       telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
                FROM alertas 
                WHERE EXTRACT(YEAR FROM fecha) = %s AND EXTRACT(MONTH FROM fecha) = %s
                ORDER BY fecha DESC
            """, (fecha_actual.year, fecha_actual.month))
            fecha_inicio = datetime(fecha_actual.year, fecha_actual.month, 1).strftime("%Y-%m-%d")
            fecha_fin = datetime.now().strftime("%Y-%m-%d")
        else:  # custom
            if not fecha_inicio or not fecha_fin:
                raise HTTPException(status_code=400, detail="Fechas requeridas para tipo custom")
            cur.execute("""
                SELECT id, fecha, foto1_url, foto2_url, moto_confianza, distancia_moto_persona,
                       telegram_enviado, estado, tipo_evento, arma_utilizada, testigos, descripcion
                FROM alertas 
                WHERE DATE(fecha) BETWEEN %s AND %s
                ORDER BY fecha DESC
            """, (fecha_inicio, fecha_fin))
        
        alertas = []
        for row in cur.fetchall():
            alertas.append({
                "id": row[0],
                "fecha": row[1],
                "foto1_url": row[2],
                "foto2_url": row[3],
                "moto_confianza": row[4],
                "distancia_moto_persona": row[5],
                "telegram_enviado": row[6],
                "estado": row[7],
                "tipo_evento": row[8] if len(row) > 8 else "normal",
                "arma_utilizada": row[9] if len(row) > 9 else "ninguna",
                "testigos": int(row[10]) if row[10] else 0,
                "descripcion": row[11] if len(row) > 11 else ""
            })
        
        cur.close()
        conn.close()
        
        if not alertas:
            raise HTTPException(status_code=404, detail="No hay alertas en el período seleccionado")
        
        # 👈 Generar análisis con IA
        analisis_ia = generar_reporte_ia(alertas, tipo, fecha_inicio, fecha_fin)
        
        # 👈 Generar PDF con el análisis
        pdf_buffer = generar_pdf_reporte(alertas, tipo, fecha_inicio, fecha_fin, analisis_ia)
        
        filename = f"reporte_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generando reporte: {e}")
        raise HTTPException(status_code=500, detail=str(e))