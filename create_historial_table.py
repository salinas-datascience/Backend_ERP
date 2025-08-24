#!/usr/bin/env python3
"""
Script para crear la tabla de historial_repuestos si no existe.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import logging

# Agregar el directorio app al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import DATABASE_URL
from models.models import Base

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_historial_table():
    """Crear la tabla de historial_repuestos si no existe."""
    try:
        # Crear engine
        engine = create_engine(DATABASE_URL)
        
        # Verificar si la tabla ya existe
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'historial_repuestos'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("La tabla 'historial_repuestos' ya existe.")
                return True
            
            logger.info("Creando tabla 'historial_repuestos'...")
            
            # Crear solo la tabla de historial
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historial_repuestos (
                    id SERIAL PRIMARY KEY,
                    repuesto_id INTEGER NOT NULL REFERENCES repuestos(id),
                    maquina_id INTEGER NOT NULL REFERENCES maquinas(id),
                    cantidad_usada INTEGER NOT NULL,
                    observaciones TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Crear índices para mejorar rendimiento
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_historial_repuestos_repuesto_id 
                ON historial_repuestos(repuesto_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_historial_repuestos_maquina_id 
                ON historial_repuestos(maquina_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_historial_repuestos_fecha 
                ON historial_repuestos(fecha);
            """))
            
            conn.commit()
            logger.info("Tabla 'historial_repuestos' creada exitosamente.")
            return True
            
    except OperationalError as e:
        logger.error(f"Error de operación en la base de datos: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False

def main():
    """Función principal."""
    logger.info("Iniciando creación de tabla de historial...")
    
    if create_historial_table():
        logger.info("Proceso completado exitosamente.")
    else:
        logger.error("Error en el proceso. Revisa los logs para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()