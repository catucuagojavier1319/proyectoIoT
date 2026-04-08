# Utilidades generales 
def imagen_a_bytes(imagen, calidad=70):
    """Convertir imagen numpy a bytes JPEG"""
    import cv2
    _, buffer = cv2.imencode('.jpg', imagen, [cv2.IMWRITE_JPEG_QUALITY, calidad])
    return buffer.tobytes()