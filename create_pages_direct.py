#!/usr/bin/env python3
"""
Script para crear páginas directamente en la base de datos
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio app al path
sys.path.insert(0, '/app')

from models.models import Paginas

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL no está configurada")
    sys.exit(1)

def create_pages():
    """Crea las páginas del sistema"""
    print("🚀 Creando páginas del sistema...")
    
    # Crear conexión
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Verificar páginas existentes
        existing_count = db.query(Paginas).count()
        print(f"📋 Páginas existentes: {existing_count}")
        
        # Definir páginas del sistema
        paginas_sistema = [
            {
                "nombre": "repuestos",
                "ruta": "/repuestos",
                "titulo": "Gestión de Repuestos",
                "descripcion": "Administrar inventario de repuestos y componentes",
                "icono": "Package",
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
            }
        ]
        
        # Crear páginas
        created_count = 0
        skipped_count = 0
        
        for page_data in paginas_sistema:
            # Verificar si ya existe
            existing = db.query(Paginas).filter(
                (Paginas.nombre == page_data["nombre"]) |
                (Paginas.ruta == page_data["ruta"])
            ).first()
            
            if existing:
                print(f"⏭️  Saltando '{page_data['titulo']}' (ya existe)")
                skipped_count += 1
                continue
            
            # Crear nueva página
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
            created_count += 1
            print(f"✅ Creada: {page_data['titulo']}")
        
        # Confirmar cambios
        db.commit()
        
        # Mostrar resumen
        total_pages = db.query(Paginas).count()
        print(f"\n🎉 Proceso completado:")
        print(f"   - Páginas creadas: {created_count}")
        print(f"   - Páginas saltadas: {skipped_count}")
        print(f"   - Total páginas: {total_pages}")
        
        # Mostrar páginas por categoría
        system_pages = db.query(Paginas).filter(Paginas.solo_admin == False).order_by(Paginas.orden).all()
        admin_pages = db.query(Paginas).filter(Paginas.solo_admin == True).order_by(Paginas.orden).all()
        
        print(f"\n📋 Páginas del Sistema ({len(system_pages)}):")
        for page in system_pages:
            print(f"   - {page.titulo} ({page.ruta})")
        
        print(f"\n🔐 Páginas Administrativas ({len(admin_pages)}):")
        for page in admin_pages:
            print(f"   - {page.titulo} ({page.ruta})")
        
        print(f"\n✅ ¡Páginas creadas! Ahora los usuarios pueden ver páginas específicas.")
        
    except Exception as e:
        print(f"❌ Error al crear páginas: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    create_pages()