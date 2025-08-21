"""
Endpoints para gestión de Modelos de Máquinas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import ModeloMaquinaResponse, ModeloMaquinaCreate, ModeloMaquinaUpdate
from crud import crud_modelos_maquinas

router = APIRouter(prefix="/modelos-maquinas", tags=["Modelos de Máquinas"])


@router.get("/", response_model=List[ModeloMaquinaResponse])
def listar_modelos_maquinas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de todos los modelos de máquinas"""
    modelos = crud_modelos_maquinas.get_modelos_maquinas(db, skip=skip, limit=limit)
    return modelos


@router.get("/{modelo_id}", response_model=ModeloMaquinaResponse)
def obtener_modelo_maquina(
    modelo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener modelo de máquina por ID"""
    modelo = crud_modelos_maquinas.get_modelo_maquina(db, modelo_id=modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de máquina no encontrado"
        )
    return modelo


@router.post("/", response_model=ModeloMaquinaResponse, status_code=status.HTTP_201_CREATED)
def crear_modelo_maquina(
    modelo: ModeloMaquinaCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo modelo de máquina"""
    # Verificar si ya existe un modelo con el mismo fabricante y modelo
    if modelo.fabricante:
        db_modelo = crud_modelos_maquinas.get_modelo_by_fabricante_modelo(
            db, 
            fabricante=modelo.fabricante, 
            modelo=modelo.modelo
        )
        if db_modelo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un modelo con este fabricante y modelo"
            )
    
    return crud_modelos_maquinas.create_modelo_maquina(db=db, modelo=modelo)


@router.put("/{modelo_id}", response_model=ModeloMaquinaResponse)
def actualizar_modelo_maquina(
    modelo_id: int,
    modelo: ModeloMaquinaUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar modelo de máquina existente"""
    # Verificar que el modelo existe
    db_modelo = crud_modelos_maquinas.get_modelo_maquina(db, modelo_id=modelo_id)
    if db_modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de máquina no encontrado"
        )
    
    # Si se están actualizando fabricante y modelo, verificar que no exista otro igual
    if modelo.fabricante and modelo.modelo:
        existing_modelo = crud_modelos_maquinas.get_modelo_by_fabricante_modelo(
            db, 
            fabricante=modelo.fabricante, 
            modelo=modelo.modelo
        )
        if existing_modelo and existing_modelo.id != modelo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro modelo con este fabricante y modelo"
            )
    
    updated_modelo = crud_modelos_maquinas.update_modelo_maquina(
        db=db, 
        modelo_id=modelo_id, 
        modelo=modelo
    )
    return updated_modelo


@router.delete("/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_modelo_maquina(
    modelo_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar modelo de máquina"""
    success = crud_modelos_maquinas.delete_modelo_maquina(db=db, modelo_id=modelo_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de máquina no encontrado"
        )