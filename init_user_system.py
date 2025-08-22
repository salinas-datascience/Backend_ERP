#!/usr/bin/env python3
"""
Script para inicializar el sistema de usuarios
Ejecuta la migración y crea datos iniciales
"""
import os
import sys
import time

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

try:
    # Importar modelos y configuración
    from database import Base
    from models.models import *
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Directorio actual:", os.getcwd())
    print("Contenido directorio:", os.listdir('.'))
    sys.exit(1)

# Configuración
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL no está configurada")
    sys.exit(1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def wait_for_db():
    """Espera a que la base de datos esté disponible"""
    print("⏳ Esperando conexión a la base de datos...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Base de datos conectada")
            return engine
        except Exception as e:
            print(f"❌ Intento {attempt + 1}/{max_attempts}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(3)
            else:
                print("❌ No se pudo conectar a la base de datos")
                raise

def create_all_tables():
    """Crea todas las tablas en la base de datos"""
    engine = wait_for_db()
    print("📋 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
    return engine

def run_migration(engine):
    """Ejecuta la migración SQL"""
    print("Ejecutando migración...")
    
    migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '002_add_user_system.sql')
    
    if not os.path.exists(migration_file):
        print(f"Error: No se encontró el archivo de migración: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    try:
        with engine.connect() as conn:
            # Ejecutar la migración
            conn.execute(text(migration_sql))
            conn.commit()
        print("✓ Migración ejecutada exitosamente")
        return True
    except Exception as e:
        print(f"Error al ejecutar migración: {str(e)}")
        return False

def verify_admin_user(engine):
    """Verifica que el usuario admin existe y está configurado correctamente"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Buscar usuario admin
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        
        if not admin_user:
            print("Error: Usuario admin no encontrado")
            return False
        
        # Verificar que es admin
        if not admin_user.es_admin:
            print("Corrigiendo permisos de admin...")
            admin_user.es_admin = True
            db.commit()
        
        # Verificar que tiene rol de administrador
        if not admin_user.rol:
            rol_admin = db.query(Roles).filter(Roles.nombre == 'Administrador').first()
            if rol_admin:
                admin_user.rol_id = rol_admin.id
                db.commit()
                print("✓ Rol de administrador asignado")
        
        # Mostrar información del admin
        print(f"✓ Usuario administrador configurado:")
        print(f"  - Username: {admin_user.username}")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Es Admin: {admin_user.es_admin}")
        print(f"  - Activo: {admin_user.activo}")
        print(f"  - Debe cambiar contraseña: {admin_user.debe_cambiar_password}")
        print(f"  - Rol: {admin_user.rol.nombre if admin_user.rol else 'Sin rol'}")
        
        return True
    
    except Exception as e:
        print(f"Error al verificar usuario admin: {str(e)}")
        return False
    finally:
        db.close()

def show_summary(engine):
    """Muestra un resumen del estado del sistema"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        usuarios_count = db.query(Usuarios).count()
        roles_count = db.query(Roles).count()
        permisos_count = db.query(Permisos).count()
        paginas_count = db.query(Paginas).count()
        
        print("\n" + "="*50)
        print("RESUMEN DEL SISTEMA DE USUARIOS")
        print("="*50)
        print(f"Usuarios registrados: {usuarios_count}")
        print(f"Roles configurados: {roles_count}")
        print(f"Permisos definidos: {permisos_count}")
        print(f"Páginas disponibles: {paginas_count}")
        
        # Mostrar páginas disponibles
        print("\nPáginas disponibles:")
        paginas = db.query(Paginas).filter(Paginas.activa == True).order_by(Paginas.orden).all()
        for pagina in paginas:
            admin_only = " (Solo Admin)" if pagina.solo_admin else ""
            print(f"  - {pagina.titulo} ({pagina.ruta}){admin_only}")
        
        print("\n" + "="*50)
        print("CREDENCIALES DE ADMINISTRADOR:")
        print("Usuario: admin")
        print("Contraseña: admin123")
        print("¡IMPORTANTE! Cambie la contraseña en el primer login")
        print("="*50)
        
    except Exception as e:
        print(f"Error al generar resumen: {str(e)}")
    finally:
        db.close()

def create_admin_user(engine):
    """Crea el usuario admin si no existe"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("👤 Verificando usuario administrador...")
        
        # Verificar si ya existe el usuario admin
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        
        if admin_user:
            print("✅ Usuario administrador ya existe")
            return True
        
        print("🔨 Creando usuario administrador...")
        
        # Crear rol de administrador si no existe
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
        db.commit()
        
        print("✅ Usuario administrador creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   ⚠️  IMPORTANTE: Cambiar contraseña en primer login")
        
        return True
    
    except Exception as e:
        print(f"❌ Error al crear usuario admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Función principal"""
    print("🚀 Inicializando sistema de usuarios...")
    
    try:
        # Crear tablas y esperar DB
        engine = create_all_tables()
        
        # Crear usuario admin
        if not create_admin_user(engine):
            print("❌ Error: No se pudo crear el usuario admin")
            # No salir con error, continuar para que la app inicie
            print("⚠️  Continuando sin usuario admin (se puede crear manualmente)")
        
        print("✅ Inicialización completada!")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {str(e)}")
        import traceback
        traceback.print_exc()
        print("⚠️  Continuando sin inicialización completa")

if __name__ == "__main__":
    main()