#!/usr/bin/env python3
"""
Script para ejecutar migraciones de base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time

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
    
    print("Error: No se pudo conectar a la base de datos")
    return False

def run_migration(engine):
    """Ejecutar migración para agregar almacenamientos"""
    try:
        with engine.connect() as conn:
            # Verificar si la tabla almacenamientos ya existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'almacenamientos'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("La tabla almacenamientos ya existe")
                
                # Verificar si la columna almacenamiento_id existe en repuestos
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'repuestos' 
                        AND column_name = 'almacenamiento_id'
                    );
                """))
                
                column_exists = result.scalar()
                
                if column_exists:
                    print("La columna almacenamiento_id ya existe en repuestos")
                    return True
                else:
                    print("Agregando columna almacenamiento_id a repuestos...")
                    conn.execute(text("""
                        ALTER TABLE repuestos 
                        ADD COLUMN almacenamiento_id INTEGER REFERENCES almacenamientos(id);
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_repuestos_almacenamiento_id 
                        ON repuestos(almacenamiento_id);
                    """))
                    
                    conn.commit()
                    print("Columna almacenamiento_id agregada")
                    return True
            
            print("Creando tabla almacenamientos...")
            
            # Crear tabla almacenamientos
            conn.execute(text("""
                CREATE TABLE almacenamientos (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR UNIQUE NOT NULL,
                    nombre VARCHAR NOT NULL,
                    descripcion TEXT,
                    ubicacion_fisica VARCHAR,
                    activo INTEGER DEFAULT 1
                );
            """))
            
            # Crear índices
            conn.execute(text("""
                CREATE INDEX idx_almacenamientos_codigo ON almacenamientos(codigo);
            """))
            
            conn.execute(text("""
                CREATE INDEX idx_almacenamientos_activo ON almacenamientos(activo);
            """))
            
            print("Tabla almacenamientos creada")
            
            # Agregar columna a repuestos
            print("Agregando columna almacenamiento_id a repuestos...")
            
            conn.execute(text("""
                ALTER TABLE repuestos 
                ADD COLUMN almacenamiento_id INTEGER REFERENCES almacenamientos(id);
            """))
            
            conn.execute(text("""
                CREATE INDEX idx_repuestos_almacenamiento_id ON repuestos(almacenamiento_id);
            """))
            
            print("Columna almacenamiento_id agregada")
            
            # Insertar datos de ejemplo
            print("Insertando datos de ejemplo...")
            
            conn.execute(text("""
                INSERT INTO almacenamientos (codigo, nombre, descripcion, ubicacion_fisica, activo)
                VALUES 
                    ('A1-E1', 'Estante A1', 'Estante principal para componentes pequeños', 'Planta 1 - Zona A - Estante 1', 1),
                    ('A1-E2', 'Estante A2', 'Estante para componentes medianos', 'Planta 1 - Zona A - Estante 2', 1),
                    ('B1-E1', 'Estante B1', 'Estante para componentes electrónicos', 'Planta 1 - Zona B - Estante 1', 1),
                    ('C1-CAJ', 'Cajón C1', 'Cajón para herramientas y consumibles', 'Planta 1 - Zona C - Cajón 1', 1),
                    ('DEP-FRI', 'Depósito Refrigerado', 'Depósito con temperatura controlada para componentes sensibles', 'Planta 1 - Depósito Principal', 1);
            """))
            
            conn.commit()
            print("Migracion completada exitosamente")
            return True
            
    except SQLAlchemyError as e:
        print(f"Error ejecutando migracion: {e}")
        return False

def main():
    """Función principal"""
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: Variable DATABASE_URL no encontrada")
        sys.exit(1)
    
    print(f"Ejecutando migracion de base de datos...")
    
    try:
        # Crear engine
        engine = create_engine(database_url)
        
        # Esperar a que la BD esté disponible
        if not wait_for_db(engine):
            sys.exit(1)
        
        # Ejecutar migración
        if not run_migration(engine):
            sys.exit(1)
        
        print("Migracion completada exitosamente")
        
    except Exception as e:
        print(f"Error general: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()