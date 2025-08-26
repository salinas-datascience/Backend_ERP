from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from routers import proveedores, modelos_maquinas, maquinas, repuestos, historial, almacenamientos, auth, usuarios, admin, ordenes_compra


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
    allow_origins=["*"],  # En producción, especificar dominios específicos
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
