"""
Operaciones CRUD para Proveedores
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.models import Proveedores
from schemas.schemas import ProveedorCreate, ProveedorUpdate


def get_proveedores(db: Session, skip: int = 0, limit: int = 100) -> List[Proveedores]:
    """Obtener lista de proveedores con paginación"""
    return db.query(Proveedores).offset(skip).limit(limit).all()


def get_proveedor(db: Session, proveedor_id: int) -> Optional[Proveedores]:
    """Obtener proveedor por ID"""
    return db.query(Proveedores).filter(Proveedores.id == proveedor_id).first()


def get_proveedor_by_nombre(db: Session, nombre: str) -> Optional[Proveedores]:
    """Obtener proveedor por nombre"""
    return db.query(Proveedores).filter(Proveedores.nombre == nombre).first()


def create_proveedor(db: Session, proveedor: ProveedorCreate) -> Proveedores:
    """Crear nuevo proveedor"""
    db_proveedor = Proveedores(**proveedor.model_dump())
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


def update_proveedor(db: Session, proveedor_id: int, proveedor: ProveedorUpdate) -> Optional[Proveedores]:
    """Actualizar proveedor existente"""
    db_proveedor = db.query(Proveedores).filter(Proveedores.id == proveedor_id).first()
    if db_proveedor:
        update_data = proveedor.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_proveedor, field, value)
        db.commit()
        db.refresh(db_proveedor)
    return db_proveedor


def delete_proveedor(db: Session, proveedor_id: int) -> bool:
    """Eliminar proveedor"""
    db_proveedor = db.query(Proveedores).filter(Proveedores.id == proveedor_id).first()
    if db_proveedor:
        db.delete(db_proveedor)
        db.commit()
        return True
    return False