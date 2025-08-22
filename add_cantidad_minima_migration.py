#!/usr/bin/env python3
"""
Script de migración para agregar el campo cantidad_minima a la tabla repuestos
"""
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, Integer, Column
from database import engine, SessionLocal
from models.models import Repuestos

def add_cantidad_minima_column():
    """Agregar columna cantidad_minima a la tabla repuestos"""
    
    with engine.connect() as conn:
        # Verificar si la columna ya existe (PostgreSQL)
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name='repuestos' AND column_name='cantidad_minima'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if not column_exists:
            print("Agregando columna cantidad_minima a la tabla repuestos...")
            
            # Agregar la nueva columna
            conn.execute(text("""
                ALTER TABLE repuestos 
                ADD COLUMN cantidad_minima INTEGER
            """))
            
            conn.commit()
            print("✅ Columna cantidad_minima agregada exitosamente")
        else:
            print("ℹ️  La columna cantidad_minima ya existe en la tabla repuestos")

if __name__ == "__main__":
    try:
        add_cantidad_minima_column()
        print("🎉 Migración completada exitosamente")
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        sys.exit(1)