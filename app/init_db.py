#!/usr/bin/env python3
"""
Script para inicializar la base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
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
    ubicacion = Column(String)
    cantidad = Column(Integer, default=0)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    
    proveedor = relationship("Proveedores", back_populates="repuestos")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="repuesto")

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

def wait_for_db(engine, max_retries=30):
    """Espera a que la base de datos esté disponible"""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✅ Base de datos conectada")
                return True
        except SQLAlchemyError as e:
            print(f"🔄 Esperando base de datos... intento {i+1}/{max_retries}")
            time.sleep(2)
    
    print("❌ No se pudo conectar a la base de datos")
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
        print(f"❌ Error inicializando base de datos: {e}")
        return False
    
    return True

def create_tables(engine):
    """Crear todas las tablas del sistema de gestión de repuestos"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except SQLAlchemyError as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Variable DATABASE_URL no encontrada")
        sys.exit(1)
    
    print(f"🚀 Inicializando base de datos...")
    
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
        
        print("🎉 Inicialización completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()