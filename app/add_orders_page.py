#!/usr/bin/env python3
"""
Script para agregar la página de órdenes de compra al sistema
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models.models import Usuarios, Paginas

def add_orders_page():
    """Agregar página de órdenes de compra si no existe"""
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: Variable DATABASE_URL no encontrada")
        sys.exit(1)
    
    try:
        # Crear engine y sesión
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Verificar si la página ya existe
        existing_page = db.query(Paginas).filter(Paginas.nombre == 'ordenes_compra').first()
        
        if existing_page:
            print("La página de órdenes de compra ya existe")
            db.close()
            return True
        
        print("Creando página de órdenes de compra...")
        
        # Crear la nueva página
        nueva_pagina = Paginas(
            nombre="ordenes_compra",
            ruta="/ordenes-compra", 
            titulo="Órdenes de Compra",
            descripcion="Gestión de pedidos de repuestos y seguimiento de órdenes",
            icono="ShoppingCart",
            orden=7,
            activa=True,
            solo_admin=False
        )
        
        db.add(nueva_pagina)
        db.flush()
        
        # Obtener usuario admin y asignar la página
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        
        if admin_user:
            admin_user.paginas_permitidas.append(nueva_pagina)
            print("Página asignada al usuario admin")
        
        db.commit()
        
        print("✅ Página de órdenes de compra creada y asignada exitosamente")
        
        # Verificar todas las páginas del admin
        admin_pages_count = len(admin_user.paginas_permitidas)
        print(f"El usuario admin tiene acceso a {admin_pages_count} páginas")
        
        db.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"ERROR: Error creando página: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    add_orders_page()