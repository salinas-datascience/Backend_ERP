"""
Modelos ORM SQLAlchemy para el sistema de gestión de repuestos SMT
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func, Boolean, Table
from sqlalchemy.orm import relationship
from database import Base


# Tablas de asociación para relaciones muchos a muchos
roles_permisos = Table(
    'roles_permisos',
    Base.metadata,
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permiso_id', Integer, ForeignKey('permisos.id'), primary_key=True)
)

usuarios_paginas = Table(
    'usuarios_paginas',
    Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('pagina_id', Integer, ForeignKey('paginas.id'), primary_key=True)
)


class Usuarios(Base):
    """Modelo para la gestión de usuarios del sistema.
    
    Almacena información de autenticación y datos básicos de los usuarios
    que tienen acceso al sistema ERP.
    """
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre_completo = Column(String)
    activo = Column(Boolean, default=True)
    es_admin = Column(Boolean, default=False)
    rol_id = Column(Integer, ForeignKey('roles.id'))
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    ultima_conexion = Column(TIMESTAMP)
    # Campos para gestión de contraseñas
    debe_cambiar_password = Column(Boolean, default=True)  # Forzar cambio en primer login
    fecha_cambio_password = Column(TIMESTAMP)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(TIMESTAMP)  # Bloqueo temporal por intentos fallidos
    
    # Relaciones
    rol = relationship("Roles", back_populates="usuarios")
    paginas_permitidas = relationship("Paginas", secondary=usuarios_paginas, back_populates="usuarios")


class Roles(Base):
    """Modelo para roles del sistema.
    
    Define diferentes niveles de acceso como admin, supervisor, operador, etc.
    """
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    # Relaciones
    usuarios = relationship("Usuarios", back_populates="rol")
    permisos = relationship("Permisos", secondary=roles_permisos, back_populates="roles")


class Permisos(Base):
    """Modelo para permisos específicos del sistema.
    
    Define acciones específicas que pueden realizar los usuarios
    como ver_repuestos, editar_maquinas, etc.
    """
    __tablename__ = 'permisos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    recurso = Column(String, nullable=False)  # ej: repuestos, maquinas, usuarios
    accion = Column(String, nullable=False)   # ej: crear, leer, actualizar, eliminar
    activo = Column(Boolean, default=True)
    
    # Relaciones
    roles = relationship("Roles", secondary=roles_permisos, back_populates="permisos")


class Paginas(Base):
    """Modelo para páginas del sistema.
    
    Define las diferentes páginas/secciones del frontend que pueden
    ser asignadas a usuarios específicos.
    """
    __tablename__ = 'paginas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    ruta = Column(String, unique=True, nullable=False)  # ej: /repuestos, /maquinas
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    icono = Column(String)  # clase CSS del icono
    orden = Column(Integer, default=0)  # para ordenar en el menú
    activa = Column(Boolean, default=True)
    solo_admin = Column(Boolean, default=False)  # páginas exclusivas para admin
    
    # Relaciones
    usuarios = relationship("Usuarios", secondary=usuarios_paginas, back_populates="paginas_permitidas")


class Proveedores(Base):
    """Modelo para gestionar los proveedores de repuestos.
    
    Almacena información básica de contacto de los proveedores
    que suministran repuestos para las máquinas SMT.
    """
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String)
    telefono = Column(String)
    email = Column(String)
    
    # Relaciones
    repuestos = relationship("Repuestos", back_populates="proveedor")
    ordenes_compra = relationship("OrdenesCompra", back_populates="proveedor")


class ModelosMaquinas(Base):
    """Modelo para los diferentes tipos de máquinas SMT.
    
    Define las características generales de cada modelo de máquina,
    incluyendo fabricante, modelo específico y detalles técnicos.
    """
    __tablename__ = 'modelos_maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    fabricante = Column(String)
    modelo = Column(String, nullable=False)
    detalle = Column(Text)
    
    # Relación con máquinas
    maquinas = relationship("Maquinas", back_populates="modelo")


class Almacenamientos(Base):
    """Modelo para lugares de almacenamiento de repuestos.
    
    Define ubicaciones estandarizadas donde se almacenan los repuestos,
    facilitando la gestión del inventario y localización física.
    """
    __tablename__ = 'almacenamientos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    ubicacion_fisica = Column(String)  # Ej: "Planta 1 - Estante A"
    activo = Column(Integer, default=1)  # 1=activo, 0=inactivo
    
    # Relación con repuestos
    repuestos = relationship("Repuestos", back_populates="almacenamiento")


class Maquinas(Base):
    """Modelo para las máquinas SMT individuales.
    
    Representa cada máquina física con su número de serie único
    y ubicación en la planta de producción.
    """
    __tablename__ = 'maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    modelo_id = Column(Integer, ForeignKey('modelos_maquinas.id'))
    numero_serie = Column(String, unique=True, nullable=False, index=True)
    alias = Column(String)
    ubicacion = Column(String)
    
    # Relaciones
    modelo = relationship("ModelosMaquinas", back_populates="maquinas")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="maquina")


class Repuestos(Base):
    """Modelo para el inventario de repuestos.
    
    Gestiona el stock de repuestos disponibles para mantenimiento
    de las máquinas SMT, incluyendo cantidad y ubicación física.
    """
    __tablename__ = 'repuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    detalle = Column(Text)
    ubicacion = Column(String)  # Campo legacy, mantener por compatibilidad
    almacenamiento_id = Column(Integer, ForeignKey('almacenamientos.id'))
    cantidad = Column(Integer, default=0)
    cantidad_minima = Column(Integer, nullable=True)  # Cantidad mínima personalizada para alertas
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    tipo = Column(String, nullable=True)  # insumo, repuesto, consumible (opcional)
    descripcion_aduana = Column(Text, nullable=True)  # Descripción para aduana (opcional)
    
    # Relaciones
    proveedor = relationship("Proveedores", back_populates="repuestos")
    almacenamiento = relationship("Almacenamientos", back_populates="repuestos")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="repuesto")
    items_orden = relationship("ItemsOrdenCompra", back_populates="repuesto")


class HistorialRepuestos(Base):
    """Modelo para el historial de uso de repuestos.
    
    Registra cada vez que se utilizan repuestos en el mantenimiento
    de máquinas, manteniendo un control de consumo y fechas.
    """
    __tablename__ = 'historial_repuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    repuesto_id = Column(Integer, ForeignKey('repuestos.id'), nullable=False)
    maquina_id = Column(Integer, ForeignKey('maquinas.id'), nullable=False)
    cantidad_usada = Column(Integer, nullable=False)
    fecha = Column(TIMESTAMP, default=func.now())
    observaciones = Column(Text)
    
    # Relaciones
    repuesto = relationship("Repuestos", back_populates="historial_repuestos")
    maquina = relationship("Maquinas", back_populates="historial_repuestos")


class OrdenesCompra(Base):
    """Modelo para órdenes de compra de repuestos.
    
    Gestiona el ciclo completo de pedidos de repuestos desde la creación
    hasta la recepción y almacenamiento en inventario.
    """
    __tablename__ = 'ordenes_compra'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    numero_requisicion = Column(String, unique=True, nullable=True, index=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    legajo = Column(String, nullable=True)
    estado = Column(String, default='borrador')  # borrador, cotizado, confirmado, completado
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    observaciones = Column(Text)
    usuario_creador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relaciones
    proveedor = relationship("Proveedores", back_populates="ordenes_compra")
    usuario_creador = relationship("Usuarios")
    items = relationship("ItemsOrdenCompra", back_populates="orden", cascade="all, delete-orphan")
    documentos = relationship("DocumentosOrden", back_populates="orden", cascade="all, delete-orphan")


class ItemsOrdenCompra(Base):
    """Modelo para items individuales dentro de una orden de compra.
    
    Cada item puede ser un repuesto existente o un item manual (temporal)
    que se convertirá en repuesto cuando llegue la orden.
    """
    __tablename__ = 'items_orden_compra'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    orden_id = Column(Integer, ForeignKey('ordenes_compra.id'), nullable=False)
    repuesto_id = Column(Integer, ForeignKey('repuestos.id'), nullable=True)  # Opcional para items manuales
    cantidad_pedida = Column(Integer, nullable=False)
    cantidad_recibida = Column(Integer, default=0)
    descripcion_aduana = Column(Text, nullable=True)
    precio_unitario = Column(String, nullable=True)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    # Campos para items manuales
    es_item_manual = Column(Boolean, default=False, nullable=False)
    nombre_manual = Column(String, nullable=True)  # Solo para items manuales
    codigo_manual = Column(String, nullable=True)  # Solo para items manuales  
    detalle_manual = Column(Text, nullable=True)   # Solo para items manuales
    cantidad_minima_manual = Column(Integer, nullable=True)  # Solo para items manuales
    
    # Relaciones
    orden = relationship("OrdenesCompra", back_populates="items")
    repuesto = relationship("Repuestos", back_populates="items_orden")


class DocumentosOrden(Base):
    """Modelo para documentos adjuntos a órdenes de compra.
    
    Almacena información de archivos PDF, imágenes y otros documentos
    relacionados con las órdenes de compra.
    """
    __tablename__ = 'documentos_orden'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    orden_id = Column(Integer, ForeignKey('ordenes_compra.id'), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    ruta_archivo = Column(String, nullable=False)
    tipo_archivo = Column(String, nullable=False)
    tamaño_archivo = Column(Integer, nullable=False)
    fecha_subida = Column(TIMESTAMP, default=func.now())
    usuario_subida_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relaciones
    orden = relationship("OrdenesCompra", back_populates="documentos")
    usuario_subida = relationship("Usuarios")