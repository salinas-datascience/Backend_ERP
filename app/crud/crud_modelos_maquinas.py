"""
Operaciones CRUD para Modelos de Máquinas
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.models import ModelosMaquinas
from schemas.schemas import ModeloMaquinaCreate, ModeloMaquinaUpdate


def get_modelos_maquinas(db: Session, skip: int = 0, limit: int = 100) -> List[ModelosMaquinas]:
    """Obtener lista de modelos de máquinas con paginación"""
    return db.query(ModelosMaquinas).offset(skip).limit(limit).all()


def get_modelo_maquina(db: Session, modelo_id: int) -> Optional[ModelosMaquinas]:
    """Obtener modelo de máquina por ID"""
    return db.query(ModelosMaquinas).filter(ModelosMaquinas.id == modelo_id).first()


def get_modelo_by_fabricante_modelo(db: Session, fabricante: str, modelo: str) -> Optional[ModelosMaquinas]:
    """Obtener modelo por fabricante y modelo"""
    return db.query(ModelosMaquinas).filter(
        ModelosMaquinas.fabricante == fabricante,
        ModelosMaquinas.modelo == modelo
    ).first()


def create_modelo_maquina(db: Session, modelo: ModeloMaquinaCreate) -> ModelosMaquinas:
    """Crear nuevo modelo de máquina"""
    db_modelo = ModelosMaquinas(**modelo.model_dump())
    db.add(db_modelo)
    db.commit()
    db.refresh(db_modelo)
    return db_modelo


def update_modelo_maquina(db: Session, modelo_id: int, modelo: ModeloMaquinaUpdate) -> Optional[ModelosMaquinas]:
    """Actualizar modelo de máquina existente"""
    db_modelo = db.query(ModelosMaquinas).filter(ModelosMaquinas.id == modelo_id).first()
    if db_modelo:
        update_data = modelo.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_modelo, field, value)
        db.commit()
        db.refresh(db_modelo)
    return db_modelo


def delete_modelo_maquina(db: Session, modelo_id: int) -> bool:
    """Eliminar modelo de máquina"""
    db_modelo = db.query(ModelosMaquinas).filter(ModelosMaquinas.id == modelo_id).first()
    if db_modelo:
        db.delete(db_modelo)
        db.commit()
        return True
    return False