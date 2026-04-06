from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_devices():
    """Lista de dispositivos (para futuro)"""
    return {"devices": []}

@router.post("/register")
def register_device():
    """Registrar dispositivo (para futuro)"""
    return {"message": "Dispositivo registrado"}