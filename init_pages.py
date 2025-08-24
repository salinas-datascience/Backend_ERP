#!/usr/bin/env python3
"""
Script para inicializar las páginas del sistema ERP
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.models import Paginas
from datetime import datetime

def create_default_pages():
    """Crea las páginas por defecto del sistema"""
    
    db: Session = SessionLocal()
    
    try:
        # Verificar si ya hay páginas
        existing_pages = db.query(Paginas).count()
        if existing_pages > 0:
            print(f"Ya existen {existing_pages} páginas en el sistema.")
            response = input("¿Deseas agregar páginas adicionales? (s/n): ")
            if response.lower() not in ['s', 'sí', 'si', 'y', 'yes']:
                print("Operación cancelada.")
                return
        
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
            }
        ]
        
        # Páginas administrativas
        paginas_admin = [
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
        
        todas_las_paginas = paginas_sistema + paginas_admin
        
        # Crear páginas
        paginas_creadas = 0
        for pagina_data in todas_las_paginas:
            # Verificar si la página ya existe
            existing = db.query(Paginas).filter(
                (Paginas.nombre == pagina_data["nombre"]) |
                (Paginas.ruta == pagina_data["ruta"])
            ).first()
            
            if existing:
                print(f"La página '{pagina_data['titulo']}' ya existe. Saltando...")
                continue
            
            # Crear nueva página
            nueva_pagina = Paginas(
                nombre=pagina_data["nombre"],
                ruta=pagina_data["ruta"],
                titulo=pagina_data["titulo"],
                descripcion=pagina_data["descripcion"],
                icono=pagina_data["icono"],
                orden=pagina_data["orden"],
                activa=pagina_data["activa"],
                solo_admin=pagina_data["solo_admin"],
                fecha_creacion=datetime.utcnow()
            )
            
            db.add(nueva_pagina)
            paginas_creadas += 1
            print(f"✓ Creada página: {pagina_data['titulo']}")
        
        # Confirmar cambios
        db.commit()
        
        print(f"\n🎉 Proceso completado:")
        print(f"   - Páginas creadas: {paginas_creadas}")
        print(f"   - Total páginas en sistema: {db.query(Paginas).count()}")
        
        # Mostrar resumen
        print(f"\n📋 Páginas del Sistema:")
        paginas_regulares = db.query(Paginas).filter(Paginas.solo_admin == False).all()
        for pagina in paginas_regulares:
            print(f"   - {pagina.titulo} ({pagina.ruta})")
        
        print(f"\n🔐 Páginas Administrativas:")
        paginas_admin_db = db.query(Paginas).filter(Paginas.solo_admin == True).all()
        for pagina in paginas_admin_db:
            print(f"   - {pagina.titulo} ({pagina.ruta})")
        
    except Exception as e:
        print(f"❌ Error al crear páginas: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

def main():
    """Función principal"""
    print("🚀 Inicializador de Páginas del Sistema ERP")
    print("=" * 50)
    
    try:
        create_default_pages()
        print("\n✅ Páginas inicializadas correctamente!")
        print("Ahora puedes asignar páginas específicas a los usuarios.")
        
    except Exception as e:
        print(f"\n❌ Error durante la inicialización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()