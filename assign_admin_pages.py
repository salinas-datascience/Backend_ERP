#!/usr/bin/env python3
"""
Script para asignar todas las páginas al usuario admin
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio app al path
sys.path.insert(0, '/app')

from models.models import Usuarios, Paginas

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL no está configurada")
    sys.exit(1)

def assign_admin_pages():
    """Asigna todas las páginas al usuario admin"""
    print("🔧 Asignando todas las páginas al usuario admin...")
    
    # Crear conexión
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Buscar usuario admin
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        
        if not admin_user:
            print("❌ Usuario admin no encontrado")
            return False
        
        print(f"✅ Usuario admin encontrado: {admin_user.username}")
        
        # Obtener todas las páginas
        todas_las_paginas = db.query(Paginas).all()
        print(f"📋 Total páginas disponibles: {len(todas_las_paginas)}")
        
        # Limpiar páginas existentes del admin
        admin_user.paginas_permitidas.clear()
        
        # Asignar todas las páginas
        for pagina in todas_las_paginas:
            admin_user.paginas_permitidas.append(pagina)
            print(f"✅ Asignada: {pagina.titulo} ({pagina.ruta})")
        
        # Guardar cambios
        db.commit()
        
        print(f"\n🎉 ¡Todas las páginas asignadas al admin!")
        print(f"Total páginas asignadas: {len(admin_user.paginas_permitidas)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al asignar páginas: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    if assign_admin_pages():
        print("\n✅ Admin configurado correctamente!")
        print("Ahora el admin puede ver todas las páginas.")
    else:
        print("\n❌ Error en la configuración")
        sys.exit(1)