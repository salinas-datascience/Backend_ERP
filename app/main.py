from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from routers import proveedores, modelos_maquinas, maquinas, repuestos, historial, almacenamientos, auth, usuarios, admin, ordenes_compra, ordenes_trabajo


class Settings(BaseSettings):
    database_url: str
    env_state: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI(
    title="Sistema de Gestión de Repuestos SMT",
    description="API para gestión de repuestos y mantenimiento de máquinas SMT",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(admin.router)
app.include_router(proveedores.router)
app.include_router(modelos_maquinas.router)
app.include_router(maquinas.router)
app.include_router(repuestos.router)
app.include_router(historial.router)
app.include_router(almacenamientos.router)
app.include_router(ordenes_compra.router)
app.include_router(ordenes_trabajo.router, prefix="/api/ordenes-trabajo", tags=["ordenes-trabajo"])


@app.get("/")
async def root():
    return {
        "message": "Sistema de Gestión de Repuestos SMT",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.env_state}
