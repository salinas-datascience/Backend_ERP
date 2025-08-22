"""
Operaciones CRUD para Repuestos
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from models.models import Repuestos
from schemas.schemas import RepuestoCreate, RepuestoUpdate


def get_repuestos(db: Session, skip: int = 0, limit: int = 100) -> List[Repuestos]:
    """Obtener lista de repuestos con paginación incluyendo proveedor y almacenamiento"""
    return db.query(Repuestos).options(
        joinedload(Repuestos.proveedor),
        joinedload(Repuestos.almacenamiento)
    ).offset(skip).limit(limit).all()


def get_repuesto(db: Session, repuesto_id: int) -> Optional[Repuestos]:
    """Obtener repuesto por ID incluyendo proveedor y almacenamiento"""
    return db.query(Repuestos).options(
        joinedload(Repuestos.proveedor),
        joinedload(Repuestos.almacenamiento)
    ).filter(Repuestos.id == repuesto_id).first()


def get_repuesto_by_codigo(db: Session, codigo: str) -> Optional[Repuestos]:
    """Obtener repuesto por código"""
    return db.query(Repuestos).filter(Repuestos.codigo == codigo).first()


def get_repuestos_by_proveedor(db: Session, proveedor_id: int) -> List[Repuestos]:
    """Obtener repuestos por proveedor"""
    return db.query(Repuestos).options(
        joinedload(Repuestos.proveedor),
        joinedload(Repuestos.almacenamiento)
    ).filter(Repuestos.proveedor_id == proveedor_id).all()


def get_repuestos_bajo_stock(db: Session, cantidad_minima_default: int = 10) -> List[Repuestos]:
    """Obtener repuestos con stock bajo usando cantidad mínima personalizada o default"""
    from sqlalchemy import case, or_
    
    return db.query(Repuestos).options(
        joinedload(Repuestos.proveedor),
        joinedload(Repuestos.almacenamiento)
    ).filter(
        or_(
            # Usar cantidad_minima personalizada si está definida
            (Repuestos.cantidad_minima.isnot(None)) & (Repuestos.cantidad <= Repuestos.cantidad_minima),
            # Usar cantidad_minima_default si no hay personalizada
            (Repuestos.cantidad_minima.is_(None)) & (Repuestos.cantidad <= cantidad_minima_default)
        )
    ).all()


def create_repuesto(db: Session, repuesto: RepuestoCreate) -> Repuestos:
    """Crear nuevo repuesto"""
    db_repuesto = Repuestos(**repuesto.model_dump())
    db.add(db_repuesto)
    db.commit()
    db.refresh(db_repuesto)
    return db_repuesto


def update_repuesto(db: Session, repuesto_id: int, repuesto: RepuestoUpdate) -> Optional[Repuestos]:
    """Actualizar repuesto existente"""
    db_repuesto = db.query(Repuestos).filter(Repuestos.id == repuesto_id).first()
    if db_repuesto:
        update_data = repuesto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_repuesto, field, value)
        db.commit()
        db.refresh(db_repuesto)
    return db_repuesto


def actualizar_stock(db: Session, repuesto_id: int, nueva_cantidad: int) -> Optional[Repuestos]:
    """Actualizar solo el stock de un repuesto"""
    db_repuesto = db.query(Repuestos).filter(Repuestos.id == repuesto_id).first()
    if db_repuesto:
        db_repuesto.cantidad = nueva_cantidad
        db.commit()
        db.refresh(db_repuesto)
    return db_repuesto


def delete_repuesto(db: Session, repuesto_id: int) -> bool:
    """Eliminar repuesto"""
    db_repuesto = db.query(Repuestos).filter(Repuestos.id == repuesto_id).first()
    if db_repuesto:
        db.delete(db_repuesto)
        db.commit()
        return True
    return False