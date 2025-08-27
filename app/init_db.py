#!/usr/bin/env python3
"""
Script para inicializar la base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, Integer, String, Text, ForeignKey, TIMESTAMP, func, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
import time

Base = declarative_base()

class Proveedores(Base):
    """Modelo para gestionar los proveedores de repuestos.
    
    Almacena información básica de contacto de los proveedores
    que suministran repuestos para las máquinas SMT.
    """
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String)
    telefono = Column(String)
    email = Column(String)
    
    repuestos = relationship("Repuestos", back_populates="proveedor")
    ordenes_compra = relationship("OrdenesCompra", back_populates="proveedor")

class ModelosMaquinas(Base):
    """Modelo para los diferentes tipos de máquinas SMT.
    
    Define las características generales de cada modelo de máquina,
    incluyendo fabricante, modelo específico y detalles técnicos.
    """
    __tablename__ = 'modelos_maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fabricante = Column(String)
    modelo = Column(String, nullable=False)
    detalle = Column(Text)
    
    maquinas = relationship("Maquinas", back_populates="modelo")

class Almacenamientos(Base):
    """Modelo para lugares de almacenamiento de repuestos.
    
    Define ubicaciones estandarizadas donde se almacenan los repuestos,
    facilitando la gestión del inventario y localización física.
    """
    __tablename__ = 'almacenamientos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    ubicacion_fisica = Column(String)
    activo = Column(Integer, default=1)
    
    repuestos = relationship("Repuestos", back_populates="almacenamiento")

class Maquinas(Base):
    """Modelo para las máquinas SMT individuales.
    
    Representa cada máquina física con su número de serie único
    y ubicación en la planta de producción.
    """
    __tablename__ = 'maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    modelo_id = Column(Integer, ForeignKey('modelos_maquinas.id'))
    numero_serie = Column(String, unique=True, nullable=False)
    alias = Column(String)
    ubicacion = Column(String)
    
    modelo = relationship("ModelosMaquinas", back_populates="maquinas")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="maquina")

class Repuestos(Base):
    """Modelo para el inventario de repuestos.
    
    Gestiona el stock de repuestos disponibles para mantenimiento
    de las máquinas SMT, incluyendo cantidad y ubicación física.
    """
    __tablename__ = 'repuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    detalle = Column(Text)
    ubicacion = Column(String)  # Campo legacy para compatibilidad
    almacenamiento_id = Column(Integer, ForeignKey('almacenamientos.id'))
    cantidad = Column(Integer, default=0)
    cantidad_minima = Column(Integer)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    tipo = Column(String, nullable=True)  # insumo, repuesto, consumible (opcional)
    descripcion_aduana = Column(Text, nullable=True)  # Descripción para aduana (opcional)
    
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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repuesto_id = Column(Integer, ForeignKey('repuestos.id'))
    maquina_id = Column(Integer, ForeignKey('maquinas.id'))
    cantidad_usada = Column(Integer, nullable=False)
    fecha = Column(TIMESTAMP, default=func.now())
    observaciones = Column(Text)
    
    repuesto = relationship("Repuestos", back_populates="historial_repuestos")
    maquina = relationship("Maquinas", back_populates="historial_repuestos")

class OrdenesCompra(Base):
    """Modelo para órdenes de compra de repuestos.
    
    Gestiona el ciclo completo de pedidos de repuestos desde la creación
    hasta la recepción y almacenamiento en inventario.
    """
    __tablename__ = 'ordenes_compra'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_requisicion = Column(String, unique=True, nullable=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    legajo = Column(String, nullable=True)
    estado = Column(String, default='borrador')  # borrador, cotizado, confirmado, completado
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    observaciones = Column(Text)
    usuario_creador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    
    orden = relationship("OrdenesCompra", back_populates="items")
    repuesto = relationship("Repuestos", back_populates="items_orden")

class DocumentosOrden(Base):
    """Modelo para documentos adjuntos a órdenes de compra.
    
    Almacena información de archivos PDF, imágenes y otros documentos
    relacionados con las órdenes de compra.
    """
    __tablename__ = 'documentos_orden'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey('ordenes_compra.id'), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    ruta_archivo = Column(String, nullable=False)
    tipo_archivo = Column(String, nullable=False)
    tamaño_archivo = Column(Integer, nullable=False)
    fecha_subida = Column(TIMESTAMP, default=func.now())
    usuario_subida_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    orden = relationship("OrdenesCompra", back_populates="documentos")
    usuario_subida = relationship("Usuarios")

# Tablas de asociación para el sistema de usuarios
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
    """Modelo para la gestión de usuarios del sistema."""
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
    debe_cambiar_password = Column(Boolean, default=True)
    fecha_cambio_password = Column(TIMESTAMP)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(TIMESTAMP)
    
    rol = relationship("Roles", back_populates="usuarios")
    paginas_permitidas = relationship("Paginas", secondary=usuarios_paginas, back_populates="usuarios")

class Roles(Base):
    """Modelo para roles del sistema."""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    usuarios = relationship("Usuarios", back_populates="rol")
    permisos = relationship("Permisos", secondary=roles_permisos, back_populates="roles")

class Permisos(Base):
    """Modelo para permisos granulares."""
    __tablename__ = 'permisos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    recurso = Column(String, nullable=False)
    accion = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    
    roles = relationship("Roles", secondary=roles_permisos, back_populates="permisos")

class Paginas(Base):
    """Modelo para páginas del sistema."""
    __tablename__ = 'paginas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    ruta = Column(String, unique=True, nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    icono = Column(String)
    orden = Column(Integer, default=0)
    activa = Column(Boolean, default=True)
    solo_admin = Column(Boolean, default=False)
    
    usuarios = relationship("Usuarios", secondary=usuarios_paginas, back_populates="paginas_permitidas")


class OrdenesTrabajoMantenimiento(Base):
    """Modelo para órdenes de trabajo de mantenimiento."""
    __tablename__ = 'ordenes_trabajo_mantenimiento'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    maquina_id = Column(Integer, ForeignKey('maquinas.id'), nullable=False)
    usuario_asignado_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    usuario_creador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipo_mantenimiento = Column(String, nullable=False, default='correctivo')  # preventivo, predictivo, correctivo
    nivel_criticidad = Column(String, nullable=False)  # baja, media, alta, critica
    estado = Column(String, default='pendiente')  # pendiente, en_proceso, completada, cancelada
    fecha_programada = Column(TIMESTAMP, nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    fecha_inicio = Column(TIMESTAMP, nullable=True)
    fecha_finalizacion = Column(TIMESTAMP, nullable=True)
    tiempo_estimado_horas = Column(Integer, nullable=True)
    
    maquina = relationship("Maquinas")
    usuario_asignado = relationship("Usuarios", foreign_keys=[usuario_asignado_id])
    usuario_creador = relationship("Usuarios", foreign_keys=[usuario_creador_id])
    comentarios = relationship("ComentariosOT", back_populates="orden_trabajo", cascade="all, delete-orphan")
    archivos = relationship("ArchivosOT", back_populates="orden_trabajo", cascade="all, delete-orphan")


class ComentariosOT(Base):
    """Modelo para comentarios en órdenes de trabajo."""
    __tablename__ = 'comentarios_ot'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    orden_trabajo_id = Column(Integer, ForeignKey('ordenes_trabajo_mantenimiento.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    comentario = Column(Text, nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    orden_trabajo = relationship("OrdenesTrabajoMantenimiento", back_populates="comentarios")
    usuario = relationship("Usuarios")
    archivos = relationship("ArchivosComentarioOT", back_populates="comentario", cascade="all, delete-orphan")


class ArchivosOT(Base):
    """Modelo para archivos adjuntos en órdenes de trabajo."""
    __tablename__ = 'archivos_ot'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    orden_trabajo_id = Column(Integer, ForeignKey('ordenes_trabajo_mantenimiento.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    nombre_archivo_sistema = Column(String, nullable=False)
    ruta_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    tamaño_bytes = Column(Integer, nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    orden_trabajo = relationship("OrdenesTrabajoMantenimiento", back_populates="archivos")
    usuario = relationship("Usuarios")


class ArchivosComentarioOT(Base):
    """Modelo para archivos adjuntos en comentarios de órdenes de trabajo."""
    __tablename__ = 'archivos_comentario_ot'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    comentario_id = Column(Integer, ForeignKey('comentarios_ot.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    nombre_archivo_sistema = Column(String, nullable=False)
    ruta_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    tamaño_bytes = Column(Integer, nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=func.now())
    
    comentario = relationship("ComentariosOT", back_populates="archivos")
    usuario = relationship("Usuarios")

def wait_for_db(engine, max_retries=30):
    """Espera a que la base de datos esté disponible"""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("Base de datos conectada")
                return True
        except SQLAlchemyError as e:
            print(f"Esperando base de datos... intento {i+1}/{max_retries}")
            time.sleep(2)
    
    print("No se pudo conectar a la base de datos")
    return False

def init_database(engine):
    """Inicializar la base de datos (crear extensiones si es necesario)"""
    try:
        with engine.connect() as conn:
            # Crear extensiones que puedan ser útiles
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.commit()
            print("Base de datos inicializada")
            
    except SQLAlchemyError as e:
        print(f"Error inicializando base de datos: {e}")
        return False
    
    return True

def create_tables(engine):
    """Crear todas las tablas del sistema de gestión de repuestos"""
    try:
        Base.metadata.create_all(engine)
        print("Tablas creadas exitosamente")
        return True
    except SQLAlchemyError as e:
        print(f"ERROR: Error creando tablas: {e}")
        return False

def migrate_database(engine):
    """Ejecutar migraciones de base de datos"""
    try:
        with engine.connect() as conn:
            # Migración 1: Cambiar numero_compra a numero_requisicion
            print("Ejecutando migración: numero_compra -> numero_requisicion")
            
            # Verificar si la columna numero_compra existe y numero_requisicion no
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ordenes_compra' 
                AND column_name IN ('numero_compra', 'numero_requisicion')
            """))
            
            columns = [row[0] for row in result.fetchall()]
            
            if 'numero_compra' in columns and 'numero_requisicion' not in columns:
                print("Renombrando columna numero_compra a numero_requisicion...")
                conn.execute(text("""
                    ALTER TABLE ordenes_compra 
                    RENAME COLUMN numero_compra TO numero_requisicion
                """))
                conn.commit()
                print("✓ Migración completada: numero_compra -> numero_requisicion")
            elif 'numero_requisicion' in columns:
                print("✓ Columna numero_requisicion ya existe")
            else:
                print("Creando columna numero_requisicion...")
                conn.execute(text("""
                    ALTER TABLE ordenes_compra 
                    ADD COLUMN numero_requisicion VARCHAR(255) UNIQUE
                """))
                conn.commit()
                print("✓ Columna numero_requisicion creada")
            
            # Verificar si necesitamos migrar datos de numero_compra a numero_requisicion
            if 'numero_compra' in columns and 'numero_requisicion' in columns:
                print("Migrando datos de numero_compra a numero_requisicion...")
                conn.execute(text("""
                    UPDATE ordenes_compra 
                    SET numero_requisicion = numero_compra 
                    WHERE numero_compra IS NOT NULL 
                    AND numero_requisicion IS NULL
                """))
                conn.commit()
                print("✓ Datos migrados exitosamente")
                
                # Eliminar la columna antigua
                print("Eliminando columna numero_compra...")
                conn.execute(text("ALTER TABLE ordenes_compra DROP COLUMN numero_compra"))
                conn.commit()
                print("✓ Columna numero_compra eliminada")
            
            # Migración 2: Agregar campos 'tipo' y 'descripcion_aduana' a la tabla repuestos
            print("Ejecutando migración: agregar campos tipo y descripcion_aduana a repuestos")
            
            # Verificar si las columnas ya existen
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'repuestos' 
                AND column_name IN ('tipo', 'descripcion_aduana')
            """))
            
            repuestos_columns = [row[0] for row in result.fetchall()]
            
            # Agregar columna 'tipo' si no existe (opcional)
            if 'tipo' not in repuestos_columns:
                print("Agregando columna 'tipo' a la tabla repuestos...")
                conn.execute(text("""
                    ALTER TABLE repuestos 
                    ADD COLUMN tipo VARCHAR(50)
                """))
                conn.commit()
                print("✓ Columna 'tipo' agregada a repuestos (opcional)")
            else:
                print("✓ Columna 'tipo' ya existe en repuestos")
            
            # Agregar columna 'descripcion_aduana' si no existe (opcional)
            if 'descripcion_aduana' not in repuestos_columns:
                print("Agregando columna 'descripcion_aduana' a la tabla repuestos...")
                conn.execute(text("""
                    ALTER TABLE repuestos 
                    ADD COLUMN descripcion_aduana TEXT
                """))
                conn.commit()
                print("✓ Columna 'descripcion_aduana' agregada a repuestos (opcional)")
            else:
                print("✓ Columna 'descripcion_aduana' ya existe en repuestos")
            
            # Migración 3: Agregar campo 'tipo_mantenimiento' a OrdenesTrabajoMantenimiento
            print("Ejecutando migración: agregar campo tipo_mantenimiento a ordenes_trabajo_mantenimiento")
            
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ordenes_trabajo_mantenimiento' 
                AND column_name = 'tipo_mantenimiento'
            """))
            
            ot_columns = [row[0] for row in result.fetchall()]
            
            if 'tipo_mantenimiento' not in ot_columns:
                print("Agregando columna 'tipo_mantenimiento' a la tabla ordenes_trabajo_mantenimiento...")
                conn.execute(text("""
                    ALTER TABLE ordenes_trabajo_mantenimiento 
                    ADD COLUMN tipo_mantenimiento VARCHAR(20) NOT NULL DEFAULT 'correctivo'
                """))
                conn.commit()
                print("✓ Columna 'tipo_mantenimiento' agregada a ordenes_trabajo_mantenimiento")
            else:
                print("✓ Columna 'tipo_mantenimiento' ya existe en ordenes_trabajo_mantenimiento")
            
        print("Migraciones completadas exitosamente")
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error ejecutando migraciones: {e}")
        return False

def migrate_pages_database(engine):
    """Migración específica para páginas faltantes"""
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("Ejecutando migración: agregar páginas faltantes")
        
        # Verificar páginas existentes
        paginas_existentes = db.query(Paginas).all()
        nombres_existentes = [p.nombre for p in paginas_existentes]
        print(f"Páginas existentes encontradas: {len(nombres_existentes)}")
        
        # Páginas que deben existir
        paginas_requeridas = [
            {
                "nombre": "ordenes_trabajo",
                "ruta": "/ordenes-trabajo",
                "titulo": "Generar OT", 
                "descripcion": "Gestión y creación de órdenes de trabajo de mantenimiento",
                "icono": "Wrench",
                "orden": 8,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "mis_ordenes_trabajo",
                "ruta": "/mis-ordenes-trabajo",
                "titulo": "OTs Asignadas",
                "descripcion": "Órdenes de trabajo asignadas al usuario", 
                "icono": "ClipboardList",
                "orden": 9,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "dashboard_metricas",
                "ruta": "/dashboard-metricas",
                "titulo": "Dashboard MTBF/MTTR",
                "descripcion": "Dashboard con métricas de mantenimiento MTBF y MTTR",
                "icono": "BarChart3",
                "orden": 6,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "plan_mantenimiento",
                "ruta": "/plan-mantenimiento",
                "titulo": "Plan de Mantenimiento",
                "descripcion": "Timeline de mantenimientos preventivos y programación",
                "icono": "Calendar",
                "orden": 5,
                "activa": True,
                "solo_admin": False
            }
        ]
        
        # Agregar páginas que no existen
        paginas_agregadas = 0
        for page_data in paginas_requeridas:
            if page_data["nombre"] not in nombres_existentes:
                nueva_pagina = Paginas(
                    nombre=page_data["nombre"],
                    ruta=page_data["ruta"],
                    titulo=page_data["titulo"],
                    descripcion=page_data["descripcion"],
                    icono=page_data["icono"],
                    orden=page_data["orden"],
                    activa=page_data["activa"],
                    solo_admin=page_data["solo_admin"]
                )
                db.add(nueva_pagina)
                paginas_agregadas += 1
                print(f"✓ Página '{page_data['titulo']}' agregada")
        
        if paginas_agregadas > 0:
            db.commit()
            print(f"✓ {paginas_agregadas} páginas agregadas exitosamente")
        else:
            print("✓ Todas las páginas requeridas ya existen")
        
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error en migración de páginas: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def create_sample_data(engine):
    """Crear datos de ejemplo para el sistema"""
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Verificar si ya existen datos
        if db.query(Almacenamientos).count() > 0:
            print("Datos de ejemplo ya existen")
            db.close()
            return True
        
        # Crear almacenamientos de ejemplo
        almacenamientos = [
            Almacenamientos(
                codigo="A1-E1",
                nombre="Estante A1",
                descripcion="Estante principal para componentes pequeños",
                ubicacion_fisica="Planta 1 - Zona A - Estante 1",
                activo=1
            ),
            Almacenamientos(
                codigo="A1-E2",
                nombre="Estante A2",
                descripcion="Estante para componentes medianos",
                ubicacion_fisica="Planta 1 - Zona A - Estante 2",
                activo=1
            ),
            Almacenamientos(
                codigo="B1-E1",
                nombre="Estante B1",
                descripcion="Estante para componentes electrónicos",
                ubicacion_fisica="Planta 1 - Zona B - Estante 1",
                activo=1
            ),
            Almacenamientos(
                codigo="C1-CAJ",
                nombre="Cajón C1",
                descripcion="Cajón para herramientas y consumibles",
                ubicacion_fisica="Planta 1 - Zona C - Cajón 1",
                activo=1
            ),
            Almacenamientos(
                codigo="DEP-FRI",
                nombre="Depósito Refrigerado",
                descripcion="Depósito con temperatura controlada para componentes sensibles",
                ubicacion_fisica="Planta 1 - Depósito Principal",
                activo=1
            ),
        ]
        
        for almacenamiento in almacenamientos:
            db.add(almacenamiento)
        
        # Crear proveedores de ejemplo
        proveedores = [
            Proveedores(
                nombre="TechComponents SA",
                contacto="Juan Pérez",
                telefono="+54-11-1234-5678",
                email="ventas@techcomponents.com"
            ),
            Proveedores(
                nombre="ElectroSuministros",
                contacto="María García",
                telefono="+54-11-8765-4321",
                email="pedidos@electrosuministros.com"
            ),
            Proveedores(
                nombre="SMT Solutions",
                contacto="Carlos Rodriguez",
                telefono="+54-11-5555-6666",
                email="info@smtsolutions.com"
            ),
        ]
        
        for proveedor in proveedores:
            db.add(proveedor)
        
        db.commit()
        print("Datos de ejemplo creados exitosamente")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error creando datos de ejemplo: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def create_system_pages(engine):
    """Crear las páginas del sistema"""
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Verificar si ya existen páginas
        if db.query(Paginas).count() > 0:
            print("Páginas del sistema ya existen")
            db.close()
            return True
        
        print("Creando páginas del sistema...")
        
        # Definir páginas del sistema
        paginas_sistema = [
            {
                "nombre": "repuestos",
                "ruta": "/repuestos",
                "titulo": "Gestión de Repuestos",
                "descripcion": "Administrar inventario de repuestos y componentes",
                "icono": "Warehouse",
                "orden": 1,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "proveedores",
                "ruta": "/proveedores",
                "titulo": "Gestión de Proveedores", 
                "descripcion": "Administrar proveedores y contactos",
                "icono": "Users",
                "orden": 2,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "maquinas",
                "ruta": "/maquinas",
                "titulo": "Gestión de Máquinas",
                "descripcion": "Administrar máquinas y equipos",
                "icono": "Settings",
                "orden": 3,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "modelos_maquinas",
                "ruta": "/modelos-maquinas",
                "titulo": "Modelos de Máquinas",
                "descripcion": "Administrar modelos y tipos de máquinas",
                "icono": "Cpu",
                "orden": 4,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "historial",
                "ruta": "/historial",
                "titulo": "Historial del Sistema",
                "descripcion": "Ver historial de movimientos y cambios",
                "icono": "History",
                "orden": 5,
                "activa": True,
                "solo_admin": False
            },
            # Páginas administrativas
            {
                "nombre": "admin_dashboard",
                "ruta": "/admin",
                "titulo": "Panel de Administración",
                "descripcion": "Dashboard principal de administración",
                "icono": "Shield",
                "orden": 10,
                "activa": True,
                "solo_admin": True
            },
            {
                "nombre": "admin_usuarios",
                "ruta": "/admin/usuarios",
                "titulo": "Gestión de Usuarios",
                "descripcion": "Administrar usuarios del sistema",
                "icono": "Users",
                "orden": 11,
                "activa": True,
                "solo_admin": True
            },
            {
                "nombre": "admin_roles",
                "ruta": "/admin/roles",
                "titulo": "Gestión de Roles",
                "descripcion": "Administrar roles del sistema",
                "icono": "Shield",
                "orden": 12,
                "activa": True,
                "solo_admin": True
            },
            {
                "nombre": "admin_permisos",
                "ruta": "/admin/permisos",
                "titulo": "Gestión de Permisos",
                "descripcion": "Administrar permisos granulares",
                "icono": "Key",
                "orden": 13,
                "activa": True,
                "solo_admin": True
            },
            {
                "nombre": "ordenes_compra",
                "ruta": "/ordenes-compra",
                "titulo": "Órdenes de Compra",
                "descripcion": "Gestión de pedidos de repuestos y seguimiento de órdenes",
                "icono": "ShoppingCart",
                "orden": 7,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "ordenes_trabajo",
                "ruta": "/ordenes-trabajo",
                "titulo": "Generar OT",
                "descripcion": "Gestión y creación de órdenes de trabajo de mantenimiento",
                "icono": "Wrench",
                "orden": 8,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "mis_ordenes_trabajo",
                "ruta": "/mis-ordenes-trabajo",
                "titulo": "OTs Asignadas",
                "descripcion": "Órdenes de trabajo asignadas al usuario",
                "icono": "ClipboardList",
                "orden": 9,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "dashboard_metricas",
                "ruta": "/dashboard-metricas",
                "titulo": "Dashboard MTBF/MTTR",
                "descripcion": "Dashboard con métricas de mantenimiento MTBF y MTTR",
                "icono": "BarChart3",
                "orden": 6,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "plan_mantenimiento",
                "ruta": "/plan-mantenimiento",
                "titulo": "Plan de Mantenimiento",
                "descripcion": "Timeline de mantenimientos preventivos y programación",
                "icono": "Calendar",
                "orden": 5,
                "activa": True,
                "solo_admin": False
            }
        ]
        
        # Crear páginas
        for page_data in paginas_sistema:
            nueva_pagina = Paginas(
                nombre=page_data["nombre"],
                ruta=page_data["ruta"],
                titulo=page_data["titulo"],
                descripcion=page_data["descripcion"],
                icono=page_data["icono"],
                orden=page_data["orden"],
                activa=page_data["activa"],
                solo_admin=page_data["solo_admin"]
            )
            db.add(nueva_pagina)
            print(f"Página creada: {page_data['titulo']}")
        
        db.commit()
        print("Páginas del sistema creadas exitosamente")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error creando páginas del sistema: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def create_admin_user(engine):
    """Crear usuario administrador y asignar todas las páginas"""
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Verificar si ya existe el usuario admin
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        
        if admin_user:
            print("Usuario admin ya existe")
            # Asegurar que tenga todas las páginas asignadas
            todas_las_paginas = db.query(Paginas).all()
            admin_user.paginas_permitidas.clear()
            for pagina in todas_las_paginas:
                admin_user.paginas_permitidas.append(pagina)
            db.commit()
            print(f"{len(todas_las_paginas)} páginas asignadas al admin")
            db.close()
            return True
        
        print("Creando usuario administrador...")
        
        # Crear contexto de encriptación
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Crear rol de administrador
        admin_role = db.query(Roles).filter(Roles.nombre == 'Administrador').first()
        if not admin_role:
            admin_role = Roles(
                nombre='Administrador',
                descripcion='Rol con acceso completo al sistema',
                activo=True
            )
            db.add(admin_role)
            db.flush()
        
        # Crear usuario admin
        admin_user = Usuarios(
            username='admin',
            email='admin@empresa.com',
            hashed_password=pwd_context.hash('admin123'),
            nombre_completo='Administrador del Sistema',
            activo=True,
            es_admin=True,
            rol_id=admin_role.id,
            debe_cambiar_password=True
        )
        db.add(admin_user)
        db.flush()
        
        # Crear permisos básicos si no existen
        permisos_basicos = [
            ("usuarios_leer", "Ver usuarios del sistema", "usuarios", "leer"),
            ("usuarios_crear", "Crear nuevos usuarios", "usuarios", "crear"), 
            ("usuarios_editar", "Editar usuarios existentes", "usuarios", "editar"),
            ("usuarios_eliminar", "Eliminar/desactivar usuarios", "usuarios", "eliminar"),
            ("repuestos_leer", "Ver repuestos", "repuestos", "leer"),
            ("repuestos_crear", "Crear repuestos", "repuestos", "crear"),
            ("repuestos_editar", "Editar repuestos", "repuestos", "editar"),
            ("repuestos_eliminar", "Eliminar repuestos", "repuestos", "eliminar"),
            ("maquinas_leer", "Ver máquinas", "maquinas", "leer"),
            ("maquinas_crear", "Crear máquinas", "maquinas", "crear"),
            ("maquinas_editar", "Editar máquinas", "maquinas", "editar"),
            ("maquinas_eliminar", "Eliminar máquinas", "maquinas", "eliminar"),
            ("ordenes_leer", "Ver órdenes de compra", "ordenes_compra", "leer"),
            ("ordenes_crear", "Crear órdenes de compra", "ordenes_compra", "crear"),
            ("ordenes_editar", "Editar órdenes de compra", "ordenes_compra", "editar"),
            ("ordenes_eliminar", "Eliminar órdenes de compra", "ordenes_compra", "eliminar"),
            ("ordenes_confirmar", "Confirmar llegada de repuestos", "ordenes_compra", "confirmar"),
            ("ot_leer", "Ver órdenes de trabajo", "ordenes_trabajo", "leer"),
            ("ot_crear", "Crear órdenes de trabajo", "ordenes_trabajo", "crear"),
            ("ot_editar", "Editar órdenes de trabajo", "ordenes_trabajo", "editar"),
            ("ot_eliminar", "Eliminar órdenes de trabajo", "ordenes_trabajo", "eliminar"),
            ("ot_asignar", "Asignar órdenes de trabajo", "ordenes_trabajo", "asignar"),
            ("ot_comentar", "Comentar órdenes de trabajo", "ordenes_trabajo", "comentar")
        ]
        
        for nombre, descripcion, recurso, accion in permisos_basicos:
            permiso_existente = db.query(Permisos).filter(Permisos.nombre == nombre).first()
            if not permiso_existente:
                nuevo_permiso = Permisos(
                    nombre=nombre,
                    descripcion=descripcion,
                    recurso=recurso,
                    accion=accion,
                    activo=True
                )
                db.add(nuevo_permiso)
        
        db.flush()
        
        # Asignar todos los permisos al rol de administrador
        todos_los_permisos = db.query(Permisos).all()
        admin_role.permisos.clear()
        for permiso in todos_los_permisos:
            admin_role.permisos.append(permiso)
        
        # Asignar todas las páginas al admin
        todas_las_paginas = db.query(Paginas).all()
        for pagina in todas_las_paginas:
            admin_user.paginas_permitidas.append(pagina)
        
        db.commit()
        
        print("Usuario administrador creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print(f"   Páginas asignadas: {len(todas_las_paginas)}")
        print("   ADVERTENCIA: IMPORTANTE: Cambiar contraseña en primer login")
        
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error creando usuario admin: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def main():
    """Función principal"""
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: Variable DATABASE_URL no encontrada")
        sys.exit(1)
    
    print(f"Inicializando base de datos...")
    
    try:
        # Crear engine
        engine = create_engine(database_url)
        
        # Esperar a que la BD esté disponible
        if not wait_for_db(engine):
            sys.exit(1)
        
        # Inicializar base de datos
        if not init_database(engine):
            sys.exit(1)
        
        # Crear tablas
        if not create_tables(engine):
            sys.exit(1)
        
        # Ejecutar migraciones de base de datos
        if not migrate_database(engine):
            sys.exit(1)
        
        # Ejecutar migración de páginas
        if not migrate_pages_database(engine):
            sys.exit(1)
        
        # Crear datos de ejemplo
        if not create_sample_data(engine):
            sys.exit(1)
        
        # Crear páginas del sistema
        if not create_system_pages(engine):
            sys.exit(1)
        
        # Crear usuario admin con páginas asignadas
        if not create_admin_user(engine):
            sys.exit(1)
        
        print("Inicialización completada exitosamente")
        print("Sistema listo con páginas y usuario admin configurados")
        
    except Exception as e:
        print(f"ERROR: Error general: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()