"""
Endpoints para gestión de Repuestos
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import RepuestoResponse, RepuestoCreate, RepuestoUpdate
from crud import crud_repuestos, crud_proveedores

router = APIRouter(prefix="/repuestos", tags=["Repuestos"])


@router.get("/", response_model=List[RepuestoResponse])
def listar_repuestos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de todos los repuestos"""
    repuestos = crud_repuestos.get_repuestos(db, skip=skip, limit=limit)
    return repuestos


@router.get("/{repuesto_id}", response_model=RepuestoResponse)
def obtener_repuesto(
    repuesto_id: int,
    db: Session = Depends(get_db)
):
    """Obtener repuesto por ID"""
    repuesto = crud_repuestos.get_repuesto(db, repuesto_id=repuesto_id)
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    return repuesto


@router.get("/codigo/{codigo}", response_model=RepuestoResponse)
def obtener_repuesto_por_codigo(
    codigo: str,
    db: Session = Depends(get_db)
):
    """Obtener repuesto por código"""
    repuesto = crud_repuestos.get_repuesto_by_codigo(db, codigo=codigo)
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    return repuesto


@router.get("/proveedor/{proveedor_id}", response_model=List[RepuestoResponse])
def listar_repuestos_por_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db)
):
    """Obtener repuestos por proveedor"""
    # Verificar que el proveedor existe
    proveedor = crud_proveedores.get_proveedor(db, proveedor_id=proveedor_id)
    if proveedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado"
        )
    
    repuestos = crud_repuestos.get_repuestos_by_proveedor(db, proveedor_id=proveedor_id)
    return repuestos


@router.get("/stock/bajo", response_model=List[RepuestoResponse])
def listar_repuestos_bajo_stock(
    cantidad_minima_default: int = 10,
    db: Session = Depends(get_db)
):
    """Obtener repuestos con stock bajo usando cantidad mínima personalizada o default"""
    repuestos = crud_repuestos.get_repuestos_bajo_stock(db, cantidad_minima_default=cantidad_minima_default)
    return repuestos


@router.post("/", response_model=RepuestoResponse, status_code=status.HTTP_201_CREATED)
def crear_repuesto(
    repuesto: RepuestoCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo repuesto"""
    # Verificar si ya existe un repuesto con el mismo código
    db_repuesto = crud_repuestos.get_repuesto_by_codigo(db, codigo=repuesto.codigo)
    if db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un repuesto con este código"
        )
    
    # Si se especifica proveedor, verificar que existe
    if repuesto.proveedor_id:
        proveedor = crud_proveedores.get_proveedor(db, proveedor_id=repuesto.proveedor_id)
        if proveedor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado"
            )
    
    return crud_repuestos.create_repuesto(db=db, repuesto=repuesto)


@router.put("/{repuesto_id}", response_model=RepuestoResponse)
def actualizar_repuesto(
    repuesto_id: int,
    repuesto: RepuestoUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar repuesto existente"""
    # Verificar que el repuesto existe
    db_repuesto = crud_repuestos.get_repuesto(db, repuesto_id=repuesto_id)
    if db_repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    
    # Si se está actualizando el código, verificar que no exista otro con el mismo código
    if repuesto.codigo:
        existing_repuesto = crud_repuestos.get_repuesto_by_codigo(db, codigo=repuesto.codigo)
        if existing_repuesto and existing_repuesto.id != repuesto_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro repuesto con este código"
            )
    
    # Si se está actualizando el proveedor, verificar que existe
    if repuesto.proveedor_id:
        proveedor = crud_proveedores.get_proveedor(db, proveedor_id=repuesto.proveedor_id)
        if proveedor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado"
            )
    
    updated_repuesto = crud_repuestos.update_repuesto(
        db=db, 
        repuesto_id=repuesto_id, 
        repuesto=repuesto
    )
    return updated_repuesto


@router.patch("/{repuesto_id}/stock", response_model=RepuestoResponse)
def actualizar_stock_repuesto(
    repuesto_id: int,
    nueva_cantidad: int,
    db: Session = Depends(get_db)
):
    """Actualizar solo el stock de un repuesto"""
    # Verificar que el repuesto existe
    db_repuesto = crud_repuestos.get_repuesto(db, repuesto_id=repuesto_id)
    if db_repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    
    if nueva_cantidad < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad no puede ser negativa"
        )
    
    updated_repuesto = crud_repuestos.actualizar_stock(
        db=db, 
        repuesto_id=repuesto_id, 
        nueva_cantidad=nueva_cantidad
    )
    return updated_repuesto


@router.delete("/{repuesto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_repuesto(
    repuesto_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar repuesto"""
    success = crud_repuestos.delete_repuesto(db=db, repuesto_id=repuesto_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )