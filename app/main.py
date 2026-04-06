from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import incidents, devices

app = FastAPI(
    title="API Antirrobo - Detección de Arrebatos",
    description="Sistema de detección de posibles robos en moto",
    version="1.0.0"
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidentes"])
app.include_router(devices.router, prefix="/api/devices", tags=["Dispositivos"])

@app.get("/")
def root():
    return {
        "message": "API Antirrobo funcionando",
        "endpoints": {
            "alertas": "/api/incidents/",
            "imagenes": "/api/incidents/{id}/imagenes",
            "stats": "/api/incidents/stats/resumen"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}