"""
Operaciones CRUD para gestión de almacenamientos
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.models import Almacenamientos
from schemas.schemas import AlmacenamientoCreate, AlmacenamientoUpdate


def get_almacenamientos(db: Session, skip: int = 0, limit: int = 100) -> List[Almacenamientos]:
    """Obtener lista de almacenamientos con paginación"""
    return db.query(Almacenamientos).filter(Almacenamientos.activo == 1).offset(skip).limit(limit).all()


def get_almacenamiento_by_id(db: Session, almacenamiento_id: int) -> Optional[Almacenamientos]:
    """Obtener un almacenamiento por su ID"""
    return db.query(Almacenamientos).filter(
        Almacenamientos.id == almacenamiento_id,
        Almacenamientos.activo == 1
    ).first()


def get_almacenamiento_by_codigo(db: Session, codigo: str) -> Optional[Almacenamientos]:
    """Obtener un almacenamiento por su código único"""
    return db.query(Almacenamientos).filter(
        Almacenamientos.codigo == codigo,
        Almacenamientos.activo == 1
    ).first()


def create_almacenamiento(db: Session, almacenamiento: AlmacenamientoCreate) -> Almacenamientos:
    """Crear un nuevo almacenamiento"""
    db_almacenamiento = Almacenamientos(**almacenamiento.dict())
    db.add(db_almacenamiento)
    db.commit()
    db.refresh(db_almacenamiento)
    return db_almacenamiento


def update_almacenamiento(db: Session, almacenamiento_id: int, almacenamiento_update: AlmacenamientoUpdate) -> Optional[Almacenamientos]:
    """Actualizar un almacenamiento existente"""
    db_almacenamiento = get_almacenamiento_by_id(db, almacenamiento_id)
    if not db_almacenamiento:
        return None
    
    update_data = almacenamiento_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_almacenamiento, field, value)
    
    db.commit()
    db.refresh(db_almacenamiento)
    return db_almacenamiento


def delete_almacenamiento(db: Session, almacenamiento_id: int) -> bool:
    """Eliminar (desactivar) un almacenamiento"""
    db_almacenamiento = get_almacenamiento_by_id(db, almacenamiento_id)
    if not db_almacenamiento:
        return False
    
    # Soft delete: marcar como inactivo
    db_almacenamiento.activo = 0
    db.commit()
    return True


def search_almacenamientos(db: Session, search_term: str = "", skip: int = 0, limit: int = 100) -> List[Almacenamientos]:
    """Buscar almacenamientos por término de búsqueda"""
    query = db.query(Almacenamientos).filter(Almacenamientos.activo == 1)
    
    if search_term:
        search_filter = f"%{search_term}%"
        query = query.filter(
            (Almacenamientos.codigo.ilike(search_filter)) |
            (Almacenamientos.nombre.ilike(search_filter)) |
            (Almacenamientos.descripcion.ilike(search_filter)) |
            (Almacenamientos.ubicacion_fisica.ilike(search_filter))
        )
    
    return query.offset(skip).limit(limit).all()