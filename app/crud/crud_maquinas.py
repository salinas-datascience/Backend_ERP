"""
Operaciones CRUD para Máquinas
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from models.models import Maquinas
from schemas.schemas import MaquinaCreate, MaquinaUpdate


def get_maquinas(db: Session, skip: int = 0, limit: int = 100) -> List[Maquinas]:
    """Obtener lista de máquinas con paginación incluyendo modelo"""
    return db.query(Maquinas).options(joinedload(Maquinas.modelo)).offset(skip).limit(limit).all()


def get_maquina(db: Session, maquina_id: int) -> Optional[Maquinas]:
    """Obtener máquina por ID incluyendo modelo"""
    return db.query(Maquinas).options(joinedload(Maquinas.modelo)).filter(Maquinas.id == maquina_id).first()


def get_maquina_by_numero_serie(db: Session, numero_serie: str) -> Optional[Maquinas]:
    """Obtener máquina por número de serie"""
    return db.query(Maquinas).filter(Maquinas.numero_serie == numero_serie).first()


def get_maquina_by_alias(db: Session, alias: str) -> Optional[Maquinas]:
    """Obtener máquina por alias"""
    return db.query(Maquinas).options(joinedload(Maquinas.modelo)).filter(Maquinas.alias == alias).first()


def get_maquinas_by_modelo(db: Session, modelo_id: int) -> List[Maquinas]:
    """Obtener máquinas por modelo"""
    return db.query(Maquinas).options(joinedload(Maquinas.modelo)).filter(Maquinas.modelo_id == modelo_id).all()


def create_maquina(db: Session, maquina: MaquinaCreate) -> Maquinas:
    """Crear nueva máquina"""
    db_maquina = Maquinas(**maquina.model_dump())
    db.add(db_maquina)
    db.commit()
    db.refresh(db_maquina)
    return db_maquina


def update_maquina(db: Session, maquina_id: int, maquina: MaquinaUpdate) -> Optional[Maquinas]:
    """Actualizar máquina existente"""
    db_maquina = db.query(Maquinas).filter(Maquinas.id == maquina_id).first()
    if db_maquina:
        update_data = maquina.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_maquina, field, value)
        db.commit()
        db.refresh(db_maquina)
    return db_maquina


def delete_maquina(db: Session, maquina_id: int) -> bool:
    """Eliminar máquina"""
    db_maquina = db.query(Maquinas).filter(Maquinas.id == maquina_id).first()
    if db_maquina:
        db.delete(db_maquina)
        db.commit()
        return True
    return False