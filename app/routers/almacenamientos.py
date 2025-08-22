"""
Endpoints para gestión de almacenamientos
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from crud import crud_almacenamientos
from schemas.schemas import AlmacenamientoResponse, AlmacenamientoCreate, AlmacenamientoUpdate

router = APIRouter(prefix="/almacenamientos", tags=["almacenamientos"])


@router.get("/", response_model=List[AlmacenamientoResponse])
def read_almacenamientos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a devolver"),
    search: str = Query("", description="Término de búsqueda"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de almacenamientos con búsqueda opcional
    """
    if search:
        almacenamientos = crud_almacenamientos.search_almacenamientos(db, search_term=search, skip=skip, limit=limit)
    else:
        almacenamientos = crud_almacenamientos.get_almacenamientos(db, skip=skip, limit=limit)
    
    return almacenamientos


@router.get("/{almacenamiento_id}", response_model=AlmacenamientoResponse)
def read_almacenamiento(almacenamiento_id: int, db: Session = Depends(get_db)):
    """
    Obtener un almacenamiento específico por ID
    """
    db_almacenamiento = crud_almacenamientos.get_almacenamiento_by_id(db, almacenamiento_id=almacenamiento_id)
    if db_almacenamiento is None:
        raise HTTPException(status_code=404, detail="Almacenamiento no encontrado")
    return db_almacenamiento


@router.post("/", response_model=AlmacenamientoResponse)
def create_almacenamiento(almacenamiento: AlmacenamientoCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo almacenamiento
    """
    # Verificar que el código no exista
    existing_almacenamiento = crud_almacenamientos.get_almacenamiento_by_codigo(db, codigo=almacenamiento.codigo)
    if existing_almacenamiento:
        raise HTTPException(status_code=400, detail="Ya existe un almacenamiento con este código")
    
    return crud_almacenamientos.create_almacenamiento(db=db, almacenamiento=almacenamiento)


@router.put("/{almacenamiento_id}", response_model=AlmacenamientoResponse)
def update_almacenamiento(
    almacenamiento_id: int,
    almacenamiento_update: AlmacenamientoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar un almacenamiento existente
    """
    # Si se está actualizando el código, verificar que no exista
    if almacenamiento_update.codigo:
        existing_almacenamiento = crud_almacenamientos.get_almacenamiento_by_codigo(db, codigo=almacenamiento_update.codigo)
        if existing_almacenamiento and existing_almacenamiento.id != almacenamiento_id:
            raise HTTPException(status_code=400, detail="Ya existe un almacenamiento con este código")
    
    updated_almacenamiento = crud_almacenamientos.update_almacenamiento(
        db=db, 
        almacenamiento_id=almacenamiento_id, 
        almacenamiento_update=almacenamiento_update
    )
    
    if updated_almacenamiento is None:
        raise HTTPException(status_code=404, detail="Almacenamiento no encontrado")
    
    return updated_almacenamiento


@router.delete("/{almacenamiento_id}")
def delete_almacenamiento(almacenamiento_id: int, db: Session = Depends(get_db)):
    """
    Eliminar (desactivar) un almacenamiento
    """
    success = crud_almacenamientos.delete_almacenamiento(db=db, almacenamiento_id=almacenamiento_id)
    if not success:
        raise HTTPException(status_code=404, detail="Almacenamiento no encontrado")
    
    return {"message": "Almacenamiento eliminado exitosamente"}