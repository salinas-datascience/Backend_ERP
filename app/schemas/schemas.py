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
    proveedor_id: Optional[int] = None

class RepuestoResponse(RepuestoBase):
    id: int
    proveedor: Optional[ProveedorResponse] = None
    almacenamiento: Optional[AlmacenamientoResponse] = None

    class Config:
        from_attributes = True


# === HISTORIAL DE REPUESTOS ===

class HistorialRepuestoBase(BaseModel):
    repuesto_id: int
    maquina_id: int
    cantidad_usada: int
    observaciones: Optional[str] = None

class HistorialRepuestoCreate(HistorialRepuestoBase):
    pass

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