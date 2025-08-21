"""
Endpoints para gestión de Historial de Repuestos
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import HistorialRepuestoResponse, HistorialRepuestoCreate, HistorialRepuestoUpdate
from crud import crud_historial, crud_repuestos, crud_maquinas

router = APIRouter(prefix="/historial", tags=["Historial de Repuestos"])


@router.get("/", response_model=List[HistorialRepuestoResponse])
def listar_historial(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de todo el historial de repuestos"""
    historial = crud_historial.get_historial_repuestos(db, skip=skip, limit=limit)
    return historial


@router.get("/{historial_id}", response_model=HistorialRepuestoResponse)
def obtener_historial(
    historial_id: int,
    db: Session = Depends(get_db)
):
    """Obtener registro de historial por ID"""
    historial = crud_historial.get_historial_repuesto(db, historial_id=historial_id)
    if historial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de historial no encontrado"
        )
    return historial


@router.get("/repuesto/{repuesto_id}", response_model=List[HistorialRepuestoResponse])
def listar_historial_por_repuesto(
    repuesto_id: int,
    db: Session = Depends(get_db)
):
    """Obtener historial por repuesto"""
    # Verificar que el repuesto existe
    repuesto = crud_repuestos.get_repuesto(db, repuesto_id=repuesto_id)
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    
    historial = crud_historial.get_historial_by_repuesto(db, repuesto_id=repuesto_id)
    return historial


@router.get("/maquina/{maquina_id}", response_model=List[HistorialRepuestoResponse])
def listar_historial_por_maquina(
    maquina_id: int,
    db: Session = Depends(get_db)
):
    """Obtener historial por máquina"""
    # Verificar que la máquina existe
    maquina = crud_maquinas.get_maquina(db, maquina_id=maquina_id)
    if maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    
    historial = crud_historial.get_historial_by_maquina(db, maquina_id=maquina_id)
    return historial


@router.get("/fecha/rango", response_model=List[HistorialRepuestoResponse])
def listar_historial_por_fecha(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Obtener historial por rango de fechas"""
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin"
        )
    
    historial = crud_historial.get_historial_by_fecha_rango(
        db, 
        fecha_inicio=fecha_inicio, 
        fecha_fin=fecha_fin
    )
    return historial


@router.post("/", response_model=HistorialRepuestoResponse, status_code=status.HTTP_201_CREATED)
def crear_historial(
    historial: HistorialRepuestoCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo registro de historial (usa repuesto automáticamente)"""
    # Verificar que el repuesto existe
    repuesto = crud_repuestos.get_repuesto(db, repuesto_id=historial.repuesto_id)
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    
    # Verificar que la máquina existe
    maquina = crud_maquinas.get_maquina(db, maquina_id=historial.maquina_id)
    if maquina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina no encontrada"
        )
    
    # Verificar cantidad positiva
    if historial.cantidad_usada <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad usada debe ser mayor a cero"
        )
    
    try:
        return crud_historial.create_historial_repuesto(db=db, historial=historial)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{historial_id}", response_model=HistorialRepuestoResponse)
def actualizar_historial(
    historial_id: int,
    historial: HistorialRepuestoUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar registro de historial existente"""
    # Verificar que el historial existe
    db_historial = crud_historial.get_historial_repuesto(db, historial_id=historial_id)
    if db_historial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de historial no encontrado"
        )
    
    # Validaciones si se actualizan ciertos campos
    if historial.repuesto_id:
        repuesto = crud_repuestos.get_repuesto(db, repuesto_id=historial.repuesto_id)
        if repuesto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repuesto no encontrado"
            )
    
    if historial.maquina_id:
        maquina = crud_maquinas.get_maquina(db, maquina_id=historial.maquina_id)
        if maquina is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Máquina no encontrada"
            )
    
    if historial.cantidad_usada is not None and historial.cantidad_usada <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad usada debe ser mayor a cero"
        )
    
    try:
        updated_historial = crud_historial.update_historial_repuesto(
            db=db, 
            historial_id=historial_id, 
            historial=historial
        )
        return updated_historial
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{historial_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_historial(
    historial_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar registro de historial (restaura stock automáticamente)"""
    success = crud_historial.delete_historial_repuesto(db=db, historial_id=historial_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de historial no encontrado"
        )


@router.get("/estadisticas/consumo/{repuesto_id}")
def obtener_estadisticas_consumo(
    repuesto_id: int,
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de consumo de un repuesto"""
    # Verificar que el repuesto existe
    repuesto = crud_repuestos.get_repuesto(db, repuesto_id=repuesto_id)
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )
    
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin"
        )
    
    estadisticas = crud_historial.get_consumo_por_repuesto(
        db, 
        repuesto_id=repuesto_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    return {
        "repuesto_id": repuesto_id,
        "codigo": repuesto.codigo,
        "nombre": repuesto.nombre,
        "periodo": {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        },
        "estadisticas": estadisticas
    }