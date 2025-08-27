#!/usr/bin/env python3
"""
Script completo para inicializar la base de datos desde cero
Funciona correctamente con contenedores Docker
"""
import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext

# Importar modelos existentes
from models.models import (
    Base, Usuarios, Roles, Permisos, Paginas, Proveedores, ModelosMaquinas,
    Almacenamientos, Maquinas, Repuestos, HistorialRepuestos, OrdenesCompra,
    ItemsOrdenCompra, DocumentosOrden, OrdenesTrabajoMantenimiento,
    ComentariosOT, ArchivosOT, ArchivosComentarioOT
)
from database import engine

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def wait_for_db(engine, max_retries=30):
    """Esperar a que la base de datos esté disponible"""
    for i in range(max_retries):
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            print("✅ Base de datos disponible")
            return True
        except Exception as e:
            if i < 5 or i % 10 == 0:
                print(f"⏳ Esperando base de datos... intento {i+1}/{max_retries}")
            time.sleep(2)
    
    print("❌ Base de datos no disponible después de esperar")
    return False

def create_tables():
    """Crear todas las tablas definidas en los modelos"""
    try:
        print("📋 Creando tablas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except SQLAlchemyError as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def init_database(engine):
    """Inicializar la base de datos (crear extensiones si es necesario)"""
    try:
        with engine.connect() as conn:
            # Crear extensiones que puedan ser útiles
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.commit()
            print("✅ Base de datos inicializada")
            
    except SQLAlchemyError as e:
        print(f"⚠️ Advertencia inicializando base de datos: {e}")
        # No es crítico, continuar
    
    return True

def migrate_database(engine):
    """Ejecutar migraciones de base de datos"""
    try:
        with engine.connect() as conn:
            print("🔄 Ejecutando migraciones...")
            
            # Verificar y agregar columnas que puedan faltar
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'repuestos'
            """))
            
            if result.fetchone():
                # La tabla repuestos existe, verificar columnas opcionales
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'repuestos' 
                    AND column_name IN ('tipo', 'descripcion_aduana')
                """))
                
                existing_columns = [row[0] for row in result.fetchall()]
                
                if 'tipo' not in existing_columns:
                    conn.execute(text("ALTER TABLE repuestos ADD COLUMN tipo VARCHAR(50)"))
                    print("✅ Columna 'tipo' agregada a repuestos")
                
                if 'descripcion_aduana' not in existing_columns:
                    conn.execute(text("ALTER TABLE repuestos ADD COLUMN descripcion_aduana TEXT"))
                    print("✅ Columna 'descripcion_aduana' agregada a repuestos")
                
                conn.commit()
            
            print("✅ Migraciones completadas")
            
    except SQLAlchemyError as e:
        print(f"⚠️ Advertencia en migraciones: {e}")
        # No es crítico para instalación nueva
    
    return True

def create_essential_data():
    """Crear datos esenciales: roles, permisos básicos, páginas del sistema"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("📊 Creando datos esenciales...")
        
        # 1. Crear roles básicos
        admin_role = db.query(Roles).filter(Roles.nombre == 'admin').first()
        if not admin_role:
            admin_role = Roles(
                nombre='admin',
                descripcion='Administrador del sistema con acceso completo',
                activo=True
            )
            db.add(admin_role)
            print("   ➤ Rol admin creado")
        
        user_role = db.query(Roles).filter(Roles.nombre == 'user').first()
        if not user_role:
            user_role = Roles(
                nombre='user',
                descripcion='Usuario estándar del sistema',
                activo=True
            )
            db.add(user_role)
            print("   ➤ Rol user creado")
        
        db.flush()
        
        # 2. Crear permisos esenciales
        permisos_basicos = [
            # Repuestos
            ("repuestos_leer", "Ver repuestos", "repuestos", "leer"),
            ("repuestos_crear", "Crear repuestos", "repuestos", "crear"),
            ("repuestos_editar", "Editar repuestos", "repuestos", "editar"),
            ("repuestos_eliminar", "Eliminar repuestos", "repuestos", "eliminar"),
            
            # Máquinas
            ("maquinas_leer", "Ver máquinas", "maquinas", "leer"),
            ("maquinas_crear", "Crear máquinas", "maquinas", "crear"),
            ("maquinas_editar", "Editar máquinas", "maquinas", "editar"),
            
            # Órdenes de trabajo
            ("ordenes_trabajo_leer", "Ver órdenes de trabajo", "ordenes_trabajo", "leer"),
            ("ordenes_trabajo_crear", "Crear órdenes de trabajo", "ordenes_trabajo", "crear"),
            ("ordenes_trabajo_editar", "Editar órdenes de trabajo", "ordenes_trabajo", "editar"),
            
            # Órdenes de compra
            ("ordenes_compra_leer", "Ver órdenes de compra", "ordenes_compra", "leer"),
            ("ordenes_compra_crear", "Crear órdenes de compra", "ordenes_compra", "crear"),
            ("ordenes_compra_editar", "Editar órdenes de compra", "ordenes_compra", "editar"),
            
            # Administración
            ("admin_usuarios", "Administrar usuarios", "administracion", "admin"),
            ("admin_sistema", "Administrar sistema", "administracion", "admin"),
        ]
        
        for codigo, descripcion, modulo, accion in permisos_basicos:
            permiso_existente = db.query(Permisos).filter(Permisos.nombre == codigo).first()
            if not permiso_existente:
                nuevo_permiso = Permisos(
                    nombre=codigo,
                    descripcion=descripcion,
                    recurso=modulo,
                    accion=accion
                )
                db.add(nuevo_permiso)
        
        db.flush()
        print("   ➤ Permisos básicos creados")
        
        # 3. Crear páginas del sistema
        paginas_sistema = [
            {
                "nombre": "repuestos",
                "ruta": "/repuestos",
                "titulo": "Repuestos",
                "descripcion": "Gestión de inventario de repuestos",
                "icono": "Package",
                "orden": 1,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "proveedores",
                "ruta": "/proveedores",
                "titulo": "Proveedores",
                "descripcion": "Administrar proveedores y contactos",
                "icono": "Users",
                "orden": 2,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "ordenes_compra",
                "ruta": "/ordenes-compra",
                "titulo": "Órdenes de Compra",
                "descripcion": "Gestión de pedidos de repuestos",
                "icono": "ShoppingCart",
                "orden": 3,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "maquinas", 
                "ruta": "/maquinas",
                "titulo": "Máquinas",
                "descripcion": "Gestión de máquinas y equipos",
                "icono": "Cpu",
                "orden": 4,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "modelos_maquinas",
                "ruta": "/modelos-maquinas",
                "titulo": "Modelos",
                "descripcion": "Gestión de modelos de máquinas",
                "icono": "Settings",
                "orden": 5,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "plan_mantenimiento",
                "ruta": "/plan-mantenimiento", 
                "titulo": "Plan de Mantenimiento",
                "descripcion": "Planificación de mantenimientos preventivos",
                "icono": "Calendar",
                "orden": 6,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "ordenes_trabajo",
                "ruta": "/ordenes-trabajo",
                "titulo": "Generar OT",
                "descripcion": "Gestión de órdenes de trabajo",
                "icono": "Wrench",
                "orden": 7,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "mis_ordenes_trabajo",
                "ruta": "/mis-ordenes-trabajo",
                "titulo": "OTs Asignadas",
                "descripcion": "Órdenes de trabajo asignadas al usuario",
                "icono": "ClipboardList",
                "orden": 8,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "analytics_ia",
                "ruta": "/analytics-ia",
                "titulo": "Analytics IA",
                "descripcion": "Análisis predictivo con inteligencia artificial",
                "icono": "Brain",
                "orden": 9,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "dashboard_metricas",
                "ruta": "/dashboard-metricas",
                "titulo": "Dashboard Métricas",
                "descripcion": "Métricas y KPIs del sistema",
                "icono": "BarChart3",
                "orden": 10,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "historial",
                "ruta": "/historial",
                "titulo": "Historial de Consumo",
                "descripcion": "Historial de consumo de repuestos",
                "icono": "History",
                "orden": 11,
                "activa": True,
                "solo_admin": False
            },
            {
                "nombre": "usuarios",
                "ruta": "/admin/usuarios",
                "titulo": "Usuarios",
                "descripcion": "Administración de usuarios del sistema",
                "icono": "Shield",
                "orden": 12,
                "activa": True,
                "solo_admin": True
            },
            {
                "nombre": "admin",
                "ruta": "/admin",
                "titulo": "Administración",
                "descripcion": "Panel de administración del sistema",
                "icono": "Settings",
                "orden": 13,
                "activa": True,
                "solo_admin": True
            }
        ]
        
        for pagina_data in paginas_sistema:
            pagina_existente = db.query(Paginas).filter(Paginas.nombre == pagina_data["nombre"]).first()
            if not pagina_existente:
                nueva_pagina = Paginas(**pagina_data)
                db.add(nueva_pagina)
        
        db.flush()
        print("   ➤ Páginas del sistema creadas")
        
        # 4. Asignar permisos al rol admin
        todos_los_permisos = db.query(Permisos).all()
        admin_role.permisos.clear()
        for permiso in todos_los_permisos:
            admin_role.permisos.append(permiso)
        
        db.commit()
        print("✅ Datos esenciales creados exitosamente")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Error creando datos esenciales: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_sample_data():
    """Crear datos de ejemplo para el sistema"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        if db.query(Almacenamientos).count() > 0:
            print("   ➤ Datos de ejemplo ya existen")
            db.close()
            return True
        
        print("📦 Creando datos de ejemplo...")
        
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
        print("✅ Datos de ejemplo creados")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Error creando datos de ejemplo: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def create_admin_user():
    """Crear usuario administrador con acceso completo"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("👤 Creando usuario administrador...")
        
        # Verificar si ya existe
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        if admin_user:
            print("   ➤ Usuario admin ya existe")
            # Asegurar que tenga todas las páginas asignadas
            todas_las_paginas = db.query(Paginas).all()
            admin_user.paginas_permitidas.clear()
            for pagina in todas_las_paginas:
                admin_user.paginas_permitidas.append(pagina)
            db.commit()
            print(f"   📄 {len(todas_las_paginas)} páginas asignadas")
            db.close()
            return True
        
        # Obtener rol admin
        admin_role = db.query(Roles).filter(Roles.nombre == 'admin').first()
        if not admin_role:
            print("❌ Rol admin no encontrado")
            return False
        
        # Crear usuario admin
        hashed_password = pwd_context.hash("admin123")
        admin_user = Usuarios(
            username="admin",
            email="admin@mantia.com",
            hashed_password=hashed_password,
            nombre_completo="Administrador del Sistema",
            activo=True,
            es_admin=True,
            rol_id=admin_role.id,
            debe_cambiar_password=True
        )
        
        db.add(admin_user)
        db.flush()
        
        # Asignar todas las páginas al admin
        todas_las_paginas = db.query(Paginas).all()
        for pagina in todas_las_paginas:
            admin_user.paginas_permitidas.append(pagina)
        
        db.commit()
        
        print("✅ Usuario administrador creado:")
        print("   📧 Usuario: admin")
        print("   🔑 Contraseña: admin123")
        print(f"   📄 Páginas asignadas: {len(todas_las_paginas)}")
        print("   ⚠️  IMPORTANTE: Cambiar contraseña en primer login")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Error creando usuario admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Función principal de inicialización"""
    print("🚀 Iniciando configuración de base de datos...")
    
    try:
        # 1. Esperar a que la BD esté disponible
        if not wait_for_db(engine):
            print("❌ No se pudo conectar a la base de datos")
            sys.exit(1)
        
        # 2. Inicializar base de datos
        if not init_database(engine):
            print("❌ Error inicializando base de datos")
            sys.exit(1)
        
        # 3. Crear tablas
        if not create_tables():
            print("❌ Error creando tablas")
            sys.exit(1)
        
        # 4. Ejecutar migraciones
        if not migrate_database(engine):
            print("⚠️ Advertencia en migraciones (continuando)")
        
        # 5. Crear datos esenciales
        if not create_essential_data():
            print("❌ Error creando datos esenciales")
            sys.exit(1)
        
        # 6. Crear datos de ejemplo
        if not create_sample_data():
            print("❌ Error creando datos de ejemplo")
            sys.exit(1)
        
        # 7. Crear usuario admin
        if not create_admin_user():
            print("❌ Error creando usuario admin")
            sys.exit(1)
        
        print("\n🎉 ¡Inicialización completada exitosamente!")
        print("📊 Sistema listo para usar")
        print("🔐 Credenciales: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error general durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()