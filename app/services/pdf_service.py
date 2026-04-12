# app/services/pdf_service.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import io

def generar_pdf_reporte(alertas: list, tipo: str, fecha_inicio: str = None, fecha_fin: str = None, analisis_ia: str = None):
    """
    Genera PDF con reporte de alertas
    tipo: 'day', 'week', 'month', 'custom'
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Estilo personalizado
    titulo_style = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#1e1b4b'))
    subtitulo_style = ParagraphStyle('Subtitulo', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#6366f1'))
    ia_style = ParagraphStyle('IA', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4b5563'), leading=14)
    
    contenido = []
    
    # Título
    contenido.append(Paragraph("🚨 VisionTrack", titulo_style))
    contenido.append(Spacer(1, 12))
    
    # Subtítulo según tipo
    if tipo == 'day':
        contenido.append(Paragraph("REPORTE POR DÍA", subtitulo_style))
    elif tipo == 'week':
        contenido.append(Paragraph("REPORTE POR SEMANA", subtitulo_style))
    elif tipo == 'month':
        contenido.append(Paragraph("REPORTE POR MES", subtitulo_style))
    else:
        contenido.append(Paragraph("REPORTE PERSONALIZADO", subtitulo_style))
    
    contenido.append(Spacer(1, 12))
    
    # Fecha del reporte
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    contenido.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_actual}", styles['Normal']))
    contenido.append(Spacer(1, 20))
    
    # ============ ESTADÍSTICAS GENERALES ============
    total = len(alertas)
    arrebatos = sum(1 for a in alertas if a.get('tipo_evento') == 'arrebato')
    asaltos = sum(1 for a in alertas if a.get('tipo_evento') == 'asalto')
    sospechosos = sum(1 for a in alertas if a.get('tipo_evento') == 'sospechoso')
    entregas = sum(1 for a in alertas if a.get('tipo_evento') == 'entrega de encomienda')
    transportes = sum(1 for a in alertas if a.get('tipo_evento') == 'transporte')
    normales = total - arrebatos - asaltos - sospechosos - entregas - transportes
    total_riesgo = arrebatos + asaltos
    porcentaje_riesgo = round((total_riesgo / total) * 100) if total > 0 else 0
    
    # Estadísticas de armas
    armas = {}
    for a in alertas:
        arma = a.get('arma_utilizada', 'ninguna')
        armas[arma] = armas.get(arma, 0) + 1
    
    # Estadísticas de testigos
    total_testigos = sum(a.get('testigos', 0) for a in alertas)
    
    # Confianza promedio
    confianza_promedio = sum(a.get('moto_confianza', 0) for a in alertas) / total if total > 0 else 0
    
    # Distancia promedio
    distancia_promedio = sum(a.get('distancia_moto_persona', 0) for a in alertas) / total if total > 0 else 0
    
    contenido.append(Paragraph("<b>📊 ESTADÍSTICAS GENERALES</b>", styles['Heading3']))
    contenido.append(Spacer(1, 8))
    
    stats_data = [
        ["Total eventos", str(total)],
        ["Arrebatos", str(arrebatos)],
        ["Asaltos", str(asaltos)],
        ["Situaciones sospechosas", str(sospechosos)],
        ["Entregas de encomienda", str(entregas)],
        ["Transporte normal", str(transportes)],
        ["Eventos normales", str(normales)],
        ["Porcentaje de riesgo", f"{porcentaje_riesgo}%"],
        ["Confianza promedio", f"{confianza_promedio*100:.1f}%"],
        ["Distancia promedio", f"{distancia_promedio:.0f}px"],
        ["Total testigos", str(total_testigos)]
    ]
    
    stats_table = Table(stats_data, colWidths=[180, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    contenido.append(stats_table)
    contenido.append(Spacer(1, 20))
    
    # ============ ANÁLISIS DE IA ============
    if analisis_ia:
        contenido.append(PageBreak())
        contenido.append(Paragraph("<b>🤖 ANÁLISIS DE INTELIGENCIA ARTIFICIAL</b>", styles['Heading2']))
        contenido.append(Spacer(1, 12))
        
        # Procesar el texto del análisis
        for linea in analisis_ia.split('\n'):
            if linea.strip():
                # Detectar encabezados ##
                if linea.startswith('##'):
                    contenido.append(Paragraph(f"<b>{linea.replace('#', '').strip()}</b>", styles['Heading3']))
                    contenido.append(Spacer(1, 6))
                # Detectar listas con - o *
                elif linea.startswith('-') or linea.startswith('*') or linea.startswith('•'):
                    contenido.append(Paragraph(f"• {linea[1:].strip()}", ia_style))
                    contenido.append(Spacer(1, 4))
                # Detectar números
                elif linea[0].isdigit() and '.' in linea[:3]:
                    contenido.append(Paragraph(linea, ia_style))
                    contenido.append(Spacer(1, 4))
                # Texto normal
                else:
                    contenido.append(Paragraph(linea, ia_style))
                    contenido.append(Spacer(1, 4))
        
        contenido.append(Spacer(1, 20))
    
    # ============ TABLA DE EVENTOS ============
    contenido.append(PageBreak())
    contenido.append(Paragraph("<b>📋 DETALLE DE EVENTOS</b>", styles['Heading3']))
    contenido.append(Spacer(1, 8))
    
    # Encabezados de tabla
    data = [['Fecha', 'Distancia', 'Confianza', 'Tipo', 'Arma', 'Testigos']]
    
    for alerta in alertas[:50]:  # Limitar a 50 por página
        fecha = alerta['fecha'].strftime("%d/%m %H:%M") if hasattr(alerta['fecha'], 'strftime') else str(alerta['fecha'])[:16]
        data.append([
            fecha,
            f"{alerta.get('distancia_moto_persona', 0)}px",
            f"{round(alerta.get('moto_confianza', 0) * 100)}%",
            alerta.get('tipo_evento', 'normal'),
            alerta.get('arma_utilizada', 'ninguna'),
            str(alerta.get('testigos', 0))
        ])
    
    tabla = Table(data, colWidths=[70, 60, 60, 80, 60, 50])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    contenido.append(tabla)
    
    doc.build(contenido)
    buffer.seek(0)
    return buffer