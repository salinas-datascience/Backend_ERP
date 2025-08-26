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
    tipo: Optional[str] = None  # insumo, repuesto, consumible (opcional)
    descripcion_aduana: Optional[str] = None  # Descripción para aduana (opcional)

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
    tipo: Optional[str] = None
    descripcion_aduana: Optional[str] = None

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


# === ÓRDENES DE COMPRA ===

class ItemOrdenBase(BaseModel):
    repuesto_id: Optional[int] = None  # Opcional para items manuales
    cantidad_pedida: int
    descripcion_aduana: Optional[str] = None
    precio_unitario: Optional[str] = None
    # Campos para items manuales
    es_item_manual: bool = False
    nombre_manual: Optional[str] = None
    codigo_manual: Optional[str] = None
    detalle_manual: Optional[str] = None
    cantidad_minima_manual: Optional[int] = None

class ItemOrdenCreate(ItemOrdenBase):
    pass

class ItemOrdenUpdate(BaseModel):
    repuesto_id: Optional[int] = None  # Permitir cambiar el repuesto
    cantidad_pedida: Optional[int] = None
    descripcion_aduana: Optional[str] = None
    precio_unitario: Optional[str] = None
    cantidad_recibida: Optional[int] = None
    # Campos manuales (solo para actualizar)
    nombre_manual: Optional[str] = None
    codigo_manual: Optional[str] = None
    detalle_manual: Optional[str] = None
    cantidad_minima_manual: Optional[int] = None

class ItemOrdenResponse(ItemOrdenBase):
    id: int
    orden_id: int
    cantidad_recibida: int
    fecha_creacion: datetime
    repuesto: Optional[RepuestoResponse] = None

    class Config:
        from_attributes = True

class DocumentoOrdenBase(BaseModel):
    nombre_archivo: str
    tipo_archivo: str
    tamaño_archivo: int

class DocumentoOrdenResponse(DocumentoOrdenBase):
    id: int
    orden_id: int
    ruta_archivo: str
    fecha_subida: datetime
    usuario_subida_id: int

    class Config:
        from_attributes = True

class OrdenCompraBase(BaseModel):
    proveedor_id: int
    observaciones: Optional[str] = None

class OrdenCompraCreate(OrdenCompraBase):
    items: List[ItemOrdenCreate] = []

class OrdenCompraUpdate(BaseModel):
    proveedor_id: Optional[int] = None
    numero_requisicion: Optional[str] = None
    legajo: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None

class OrdenCompraResponse(OrdenCompraBase):
    id: int
    numero_requisicion: Optional[str] = None
    legajo: Optional[str] = None
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    usuario_creador_id: int
    proveedor: Optional[ProveedorResponse] = None
    items: List[ItemOrdenResponse] = []
    documentos: List[DocumentoOrdenResponse] = []

    class Config:
        from_attributes = True

class OrdenCompraListResponse(BaseModel):
    id: int
    numero_compra: Optional[str] = None
    proveedor_nombre: str
    estado: str
    fecha_creacion: datetime
    total_items: int

    class Config:
        from_attributes = True

# Estados válidos para órdenes de compra
class EstadosOrden:
    BORRADOR = "borrador"
    COTIZADO = "cotizado"
    CONFIRMADO = "confirmado" 
    COMPLETADO = "completado"

# Para actualización masiva de llegada de repuestos
class ConfirmarLlegadaRequest(BaseModel):
    items_recibidos: List[dict]  # [{"item_id": int, "cantidad_recibida": int}]


# === ESQUEMAS PARA ÓRDENES DE TRABAJO DE MANTENIMIENTO ===

# Esquemas base
class OrdenTrabajoBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    maquina_id: int
    usuario_asignado_id: int
    nivel_criticidad: str  # baja, media, alta, critica
    fecha_programada: datetime
    tiempo_estimado_horas: Optional[int] = None


class OrdenTrabajoCreate(OrdenTrabajoBase):
    pass


class OrdenTrabajoUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    maquina_id: Optional[int] = None
    usuario_asignado_id: Optional[int] = None
    nivel_criticidad: Optional[str] = None
    fecha_programada: Optional[datetime] = None
    tiempo_estimado_horas: Optional[int] = None
    estado: Optional[str] = None  # pendiente, en_proceso, completada, cancelada


# Esquemas de respuesta para comentarios
class ComentarioOTBase(BaseModel):
    comentario: str


class ComentarioOTCreate(ComentarioOTBase):
    orden_trabajo_id: int


class UsuarioBasico(BaseModel):
    id: int
    username: str
    nombre_completo: Optional[str] = None

    class Config:
        from_attributes = True


class ComentarioOTResponse(ComentarioOTBase):
    id: int
    orden_trabajo_id: int
    fecha_creacion: datetime
    usuario: UsuarioBasico
    archivos: List['ArchivoComentarioOTResponse'] = []

    class Config:
        from_attributes = True


# Esquemas para archivos de órdenes de trabajo
class ArchivoOTBase(BaseModel):
    nombre_archivo: str
    tipo_mime: str
    tamaño_bytes: int


class ArchivoOTResponse(ArchivoOTBase):
    id: int
    orden_trabajo_id: int
    nombre_archivo_sistema: str
    ruta_archivo: str
    fecha_creacion: datetime
    usuario: UsuarioBasico

    class Config:
        from_attributes = True


# Esquemas para archivos de comentarios
class ArchivoComentarioOTBase(BaseModel):
    nombre_archivo: str
    tipo_mime: str
    tamaño_bytes: int


class ArchivoComentarioOTResponse(ArchivoComentarioOTBase):
    id: int
    comentario_id: int
    nombre_archivo_sistema: str
    ruta_archivo: str
    fecha_creacion: datetime
    usuario: UsuarioBasico

    class Config:
        from_attributes = True


# Esquemas de respuesta para órdenes de trabajo
class MaquinaBasica(BaseModel):
    id: int
    numero_serie: str
    alias: Optional[str] = None
    ubicacion: Optional[str] = None
    modelo: Optional[ModeloMaquinaResponse] = None

    class Config:
        from_attributes = True


class OrdenTrabajoResponse(OrdenTrabajoBase):
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_inicio: Optional[datetime] = None
    fecha_finalizacion: Optional[datetime] = None
    
    # Relaciones
    maquina: MaquinaBasica
    usuario_asignado: UsuarioBasico
    usuario_creador: UsuarioBasico
    comentarios: List[ComentarioOTResponse] = []
    archivos: List[ArchivoOTResponse] = []

    class Config:
        from_attributes = True


class OrdenTrabajoListResponse(BaseModel):
    id: int
    titulo: str
    estado: str
    nivel_criticidad: str
    fecha_programada: datetime
    fecha_creacion: datetime
    maquina_numero_serie: str
    maquina_alias: Optional[str] = None
    usuario_asignado_nombre: str
    usuario_creador_nombre: str

    class Config:
        from_attributes = True


# Estados válidos para órdenes de trabajo
class EstadosOrdenTrabajo:
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


# Niveles de criticidad válidos
class NivelesCriticidad:
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


# Esquema para estadísticas
class EstadisticasOT(BaseModel):
    total_pendiente: int
    total_en_proceso: int
    total_completada: int
    total_cancelada: int
    total_baja: int
    total_media: int
    total_alta: int
    total_critica: int
    total_general: int
    total_vencidas: int