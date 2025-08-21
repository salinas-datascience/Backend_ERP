"""
Endpoints para gestión de Máquinas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import MaquinaResponse, MaquinaCreate, MaquinaUpdate
from crud import crud_maquinas, crud_modelos_maquinas

router = APIRouter(prefix="/maquinas", tags=["Máquinas"])


@router.get("/", response_model=List[MaquinaResponse])
def listar_maquinas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de todas las máquinas"""
    maquinas = crud_maquinas.get_maquinas(db, skip=skip, limit=limit)
    return maquinas


@router.get("/{maquina_id}", response_model=MaquinaResponse)
def obtener_maquina(
    maquina_id: int,
    db: Session = Depends(get_db)
):
    """Obtener máquina por ID"""
    maquina = crud_maquinas.get_maquina(db, maquina_id=maquina_id)
    if maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    return maquina


@router.get("/numero-serie/{numero_serie}", response_model=MaquinaResponse)
def obtener_maquina_por_numero_serie(
    numero_serie: str,
    db: Session = Depends(get_db)
):
    """Obtener máquina por número de serie"""
    maquina = crud_maquinas.get_maquina_by_numero_serie(db, numero_serie=numero_serie)
    if maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    return maquina


@router.get("/alias/{alias}", response_model=MaquinaResponse)
def obtener_maquina_por_alias(
    alias: str,
    db: Session = Depends(get_db)
):
    """Obtener máquina por alias"""
    maquina = crud_maquinas.get_maquina_by_alias(db, alias=alias)
    if maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    return maquina


@router.get("/modelo/{modelo_id}", response_model=List[MaquinaResponse])
def listar_maquinas_por_modelo(
    modelo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener máquinas por modelo"""
    # Verificar que el modelo existe
    modelo = crud_modelos_maquinas.get_modelo_maquina(db, modelo_id=modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de máquina no encontrado"
        )
    
    maquinas = crud_maquinas.get_maquinas_by_modelo(db, modelo_id=modelo_id)
    return maquinas


@router.post("/", response_model=MaquinaResponse, status_code=status.HTTP_201_CREATED)
def crear_maquina(
    maquina: MaquinaCreate,
    db: Session = Depends(get_db)
):
    """Crear nueva máquina"""
    # Verificar si ya existe una máquina con el mismo número de serie
    db_maquina = crud_maquinas.get_maquina_by_numero_serie(db, numero_serie=maquina.numero_serie)
    if db_maquina:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una máquina con este número de serie"
        )
    
    # Verificar que el modelo existe
    modelo = crud_modelos_maquinas.get_modelo_maquina(db, modelo_id=maquina.modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de máquina no encontrado"
        )
    
    return crud_maquinas.create_maquina(db=db, maquina=maquina)


@router.put("/{maquina_id}", response_model=MaquinaResponse)
def actualizar_maquina(
    maquina_id: int,
    maquina: MaquinaUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar máquina existente"""
    # Verificar que la máquina existe
    db_maquina = crud_maquinas.get_maquina(db, maquina_id=maquina_id)
    if db_maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    
    # Si se está actualizando el número de serie, verificar que no exista otro
    if maquina.numero_serie:
        existing_maquina = crud_maquinas.get_maquina_by_numero_serie(db, numero_serie=maquina.numero_serie)
        if existing_maquina and existing_maquina.id != maquina_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otra máquina con este número de serie"
            )
    
    # Si se está actualizando el modelo, verificar que existe
    if maquina.modelo_id:
        modelo = crud_modelos_maquinas.get_modelo_maquina(db, modelo_id=maquina.modelo_id)
        if modelo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modelo de máquina no encontrado"
            )
    
    updated_maquina = crud_maquinas.update_maquina(
        db=db, 
        maquina_id=maquina_id, 
        maquina=maquina
    )
    return updated_maquina


@router.delete("/{maquina_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_maquina(
    maquina_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar máquina"""
    success = crud_maquinas.delete_maquina(db=db, maquina_id=maquina_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )