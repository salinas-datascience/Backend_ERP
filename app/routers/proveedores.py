"""
Endpoints para gestión de Proveedores
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import ProveedorResponse, ProveedorCreate, ProveedorUpdate
from crud import crud_proveedores

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.get("/", response_model=List[ProveedorResponse])
def listar_proveedores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de todos los proveedores"""
    proveedores = crud_proveedores.get_proveedores(db, skip=skip, limit=limit)
    return proveedores


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def obtener_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db)
):
    """Obtener proveedor por ID"""
    proveedor = crud_proveedores.get_proveedor(db, proveedor_id=proveedor_id)
    if proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado"
        )
    return proveedor


@router.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    proveedor: ProveedorCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo proveedor"""
    # Verificar si ya existe un proveedor con el mismo nombre
    db_proveedor = crud_proveedores.get_proveedor_by_nombre(db, nombre=proveedor.nombre)
    if db_proveedor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un proveedor con este nombre"
        )
    
    return crud_proveedores.create_proveedor(db=db, proveedor=proveedor)


@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def actualizar_proveedor(
    proveedor_id: int,
    proveedor: ProveedorUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar proveedor existente"""
    # Verificar que el proveedor existe
    db_proveedor = crud_proveedores.get_proveedor(db, proveedor_id=proveedor_id)
    if db_proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado"
        )
    
    # Si se está actualizando el nombre, verificar que no exista otro con el mismo nombre
    if proveedor.nombre:
        existing_proveedor = crud_proveedores.get_proveedor_by_nombre(db, nombre=proveedor.nombre)
        if existing_proveedor and existing_proveedor.id != proveedor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro proveedor con este nombre"
            )
    
    updated_proveedor = crud_proveedores.update_proveedor(
        db=db, 
        proveedor_id=proveedor_id, 
        proveedor=proveedor
    )
    return updated_proveedor


@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar proveedor"""
    success = crud_proveedores.delete_proveedor(db=db, proveedor_id=proveedor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado"
        )