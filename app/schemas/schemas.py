"""
Esquemas Pydantic para validación de entrada y salida de la API
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# === PROVEEDORES ===

class ProveedorBase(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorResponse(ProveedorBase):
    id: int

    class Config:
        from_attributes = True


# === ALMACENAMIENTOS ===

class AlmacenamientoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    ubicacion_fisica: Optional[str] = None
    activo: int = 1

class AlmacenamientoCreate(AlmacenamientoBase):
    pass

class AlmacenamientoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    ubicacion_fisica: Optional[str] = None
    activo: Optional[int] = None

class AlmacenamientoResponse(AlmacenamientoBase):
    id: int

    class Config:
        from_attributes = True


# === MODELOS DE MÁQUINAS ===

class ModeloMaquinaBase(BaseModel):
    fabricante: Optional[str] = None
    modelo: str
    detalle: Optional[str] = None

class ModeloMaquinaCreate(ModeloMaquinaBase):
    pass

class ModeloMaquinaUpdate(BaseModel):
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    detalle: Optional[str] = None

class ModeloMaquinaResponse(ModeloMaquinaBase):
    id: int

    class Config:
        from_attributes = True


# === MÁQUINAS ===

class MaquinaBase(BaseModel):
    numero_serie: str
    alias: Optional[str] = None
    ubicacion: Optional[str] = None
    modelo_id: int

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaUpdate(BaseModel):
    numero_serie: Optional[str] = None
    alias: Optional[str] = None
    ubicacion: Optional[str] = None
    modelo_id: Optional[int] = None

class MaquinaResponse(MaquinaBase):
    id: int
    modelo: Optional[ModeloMaquinaResponse] = None

    class Config:
        from_attributes = True


# === REPUESTOS ===

class RepuestoBase(BaseModel):
    codigo: str
    nombre: str
    detalle: Optional[str] = None
    ubicacion: Optional[str] = None  # Campo legacy para compatibilidad
    almacenamiento_id: Optional[int] = None
    cantidad: int = 0
    cantidad_minima: Optional[int] = None  # Cantidad mínima personalizada para alertas
    proveedor_id: Optional[int] = None

class RepuestoCreate(RepuestoBase):
    pass

class RepuestoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    detalle: Optional[str] = None
    ubicacion: Optional[str] = None
    almacenamiento_id: Optional[int] = None
    cantidad: Optional[int] = None
    cantidad_minima: Optional[int] = None
    proveedor_id: Optional[int] = None

class RepuestoResponse(RepuestoBase):
    id: int
    proveedor: Optional[ProveedorResponse] = None
    almacenamiento: Optional[AlmacenamientoResponse] = None

    class Config:
        from_attributes = True


# === HISTORIAL DE REPUESTOS ===

class HistorialRepuestoBase(BaseModel):
    repuesto_id: Optional[int] = None
    maquina_id: Optional[int] = None
    cantidad_usada: int
    observaciones: Optional[str] = None

class HistorialRepuestoCreate(BaseModel):
    repuesto_id: int
    maquina_id: int
    cantidad_usada: int
    observaciones: Optional[str] = None

class HistorialRepuestoUpdate(BaseModel):
    repuesto_id: Optional[int] = None
    maquina_id: Optional[int] = None
    cantidad_usada: Optional[int] = None
    observaciones: Optional[str] = None

class HistorialRepuestoResponse(HistorialRepuestoBase):
    id: int
    fecha: datetime
    repuesto: Optional[RepuestoResponse] = None
    maquina: Optional[MaquinaResponse] = None

    class Config:
        from_attributes = True


# === AUTENTICACIÓN Y USUARIOS ===

class UsuarioBase(BaseModel):
    username: str
    email: str
    nombre_completo: Optional[str] = None
    activo: bool = True
    es_admin: bool = False
    rol_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    password: str
    debe_cambiar_password: bool = True

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    nombre_completo: Optional[str] = None
    activo: Optional[bool] = None
    es_admin: Optional[bool] = None
    rol_id: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id: int
    fecha_creacion: datetime
    ultima_conexion: Optional[datetime] = None
    debe_cambiar_password: bool
    fecha_cambio_password: Optional[datetime] = None
    intentos_fallidos: int
    bloqueado_hasta: Optional[datetime] = None
    rol: Optional["RolResponse"] = None
    paginas_permitidas: List["PaginaResponse"] = []

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    password_actual: str
    password_nueva: str
    confirmar_password: str

class ResetPasswordRequest(BaseModel):
    usuario_id: int
    password_nueva: str
    forzar_cambio: bool = True


# === ROLES ===

class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class RolCreate(RolBase):
    permisos_ids: List[int] = []

class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    permisos_ids: Optional[List[int]] = None

class RolResponse(RolBase):
    id: int
    fecha_creacion: datetime
    permisos: List["PermisoResponse"] = []

    class Config:
        from_attributes = True


# === PERMISOS ===

class PermisoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    recurso: str
    accion: str
    activo: bool = True

class PermisoCreate(PermisoBase):
    pass

class PermisoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    recurso: Optional[str] = None
    accion: Optional[str] = None
    activo: Optional[bool] = None

class PermisoResponse(PermisoBase):
    id: int

    class Config:
        from_attributes = True


# === PÁGINAS ===

class PaginaBase(BaseModel):
    nombre: str
    ruta: str
    titulo: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    orden: int = 0
    activa: bool = True
    solo_admin: bool = False

class PaginaCreate(PaginaBase):
    pass

class PaginaUpdate(BaseModel):
    nombre: Optional[str] = None
    ruta: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    orden: Optional[int] = None
    activa: Optional[bool] = None
    solo_admin: Optional[bool] = None

class PaginaResponse(PaginaBase):
    id: int

    class Config:
        from_attributes = True

class AsignarPaginasRequest(BaseModel):
    usuario_id: int
    paginas_ids: List[int]


# === AUTENTICACIÓN ===

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None