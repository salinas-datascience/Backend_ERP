"""
Modelos ORM SQLAlchemy para el sistema de gestión de repuestos SMT
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database import Base


class Proveedores(Base):
    """Modelo para gestionar los proveedores de repuestos.
    
    Almacena información básica de contacto de los proveedores
    que suministran repuestos para las máquinas SMT.
    """
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String)
    telefono = Column(String)
    email = Column(String)
    
    # Relación con repuestos
    repuestos = relationship("Repuestos", back_populates="proveedor")


class ModelosMaquinas(Base):
    """Modelo para los diferentes tipos de máquinas SMT.
    
    Define las características generales de cada modelo de máquina,
    incluyendo fabricante, modelo específico y detalles técnicos.
    """
    __tablename__ = 'modelos_maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    fabricante = Column(String)
    modelo = Column(String, nullable=False)
    detalle = Column(Text)
    
    # Relación con máquinas
    maquinas = relationship("Maquinas", back_populates="modelo")


class Maquinas(Base):
    """Modelo para las máquinas SMT individuales.
    
    Representa cada máquina física con su número de serie único
    y ubicación en la planta de producción.
    """
    __tablename__ = 'maquinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    modelo_id = Column(Integer, ForeignKey('modelos_maquinas.id'))
    numero_serie = Column(String, unique=True, nullable=False, index=True)
    alias = Column(String)
    ubicacion = Column(String)
    
    # Relaciones
    modelo = relationship("ModelosMaquinas", back_populates="maquinas")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="maquina")


class Repuestos(Base):
    """Modelo para el inventario de repuestos.
    
    Gestiona el stock de repuestos disponibles para mantenimiento
    de las máquinas SMT, incluyendo cantidad y ubicación física.
    """
    __tablename__ = 'repuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    detalle = Column(Text)
    ubicacion = Column(String)
    cantidad = Column(Integer, default=0)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    
    # Relaciones
    proveedor = relationship("Proveedores", back_populates="repuestos")
    historial_repuestos = relationship("HistorialRepuestos", back_populates="repuesto")


class HistorialRepuestos(Base):
    """Modelo para el historial de uso de repuestos.
    
    Registra cada vez que se utilizan repuestos en el mantenimiento
    de máquinas, manteniendo un control de consumo y fechas.
    """
    __tablename__ = 'historial_repuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    repuesto_id = Column(Integer, ForeignKey('repuestos.id'), nullable=False)
    maquina_id = Column(Integer, ForeignKey('maquinas.id'), nullable=False)
    cantidad_usada = Column(Integer, nullable=False)
    fecha = Column(TIMESTAMP, default=func.now())
    observaciones = Column(Text)
    
    # Relaciones
    repuesto = relationship("Repuestos", back_populates="historial_repuestos")
    maquina = relationship("Maquinas", back_populates="historial_repuestos")