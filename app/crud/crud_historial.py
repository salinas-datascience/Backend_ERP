"""
Operaciones CRUD para Historial de Repuestos
"""
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models.models import HistorialRepuestos, Repuestos, Maquinas, ModelosMaquinas
from schemas.schemas import HistorialRepuestoCreate, HistorialRepuestoUpdate


def get_historial_repuestos(db: Session, skip: int = 0, limit: int = 100) -> List[HistorialRepuestos]:
    """Obtener lista de historial con paginación incluyendo repuesto y máquina ordenado por fecha descendente"""
    return db.query(HistorialRepuestos).options(
        joinedload(HistorialRepuestos.repuesto),
        joinedload(HistorialRepuestos.maquina).joinedload(Maquinas.modelo)
    ).order_by(HistorialRepuestos.fecha.desc()).offset(skip).limit(limit).all()


def get_historial_repuesto(db: Session, historial_id: int) -> Optional[HistorialRepuestos]:
    """Obtener historial por ID incluyendo relaciones"""
    return db.query(HistorialRepuestos).options(
        joinedload(HistorialRepuestos.repuesto),
        joinedload(HistorialRepuestos.maquina).joinedload(Maquinas.modelo)
    ).filter(HistorialRepuestos.id == historial_id).first()


def get_historial_by_repuesto(db: Session, repuesto_id: int) -> List[HistorialRepuestos]:
    """Obtener historial por repuesto ordenado por fecha descendente"""
    return db.query(HistorialRepuestos).options(
        joinedload(HistorialRepuestos.repuesto),
        joinedload(HistorialRepuestos.maquina).joinedload(Maquinas.modelo)
    ).filter(HistorialRepuestos.repuesto_id == repuesto_id).order_by(HistorialRepuestos.fecha.desc()).all()


def get_historial_by_maquina(db: Session, maquina_id: int) -> List[HistorialRepuestos]:
    """Obtener historial por máquina ordenado por fecha descendente"""
    return db.query(HistorialRepuestos).options(
        joinedload(HistorialRepuestos.repuesto),
        joinedload(HistorialRepuestos.maquina).joinedload(Maquinas.modelo)
    ).filter(HistorialRepuestos.maquina_id == maquina_id).order_by(HistorialRepuestos.fecha.desc()).all()


def get_historial_by_fecha_rango(db: Session, fecha_inicio: date, fecha_fin: date) -> List[HistorialRepuestos]:
    """Obtener historial por rango de fechas ordenado por fecha descendente"""
    return db.query(HistorialRepuestos).options(
        joinedload(HistorialRepuestos.repuesto),
        joinedload(HistorialRepuestos.maquina).joinedload(Maquinas.modelo)
    ).filter(
        and_(
            HistorialRepuestos.fecha >= fecha_inicio,
            HistorialRepuestos.fecha <= fecha_fin
        )
    ).order_by(HistorialRepuestos.fecha.desc()).all()


def create_historial_repuesto(db: Session, historial: HistorialRepuestoCreate) -> HistorialRepuestos:
    """Crear nuevo registro de historial y actualizar stock del repuesto"""
    # Verificar que el repuesto tenga stock suficiente
    repuesto = db.query(Repuestos).filter(Repuestos.id == historial.repuesto_id).first()
    if not repuesto:
        raise ValueError("Repuesto no encontrado")
    
    if repuesto.cantidad < historial.cantidad_usada:
        raise ValueError(f"Stock insuficiente. Disponible: {repuesto.cantidad}, Solicitado: {historial.cantidad_usada}")
    
    # Crear registro de historial
    db_historial = HistorialRepuestos(**historial.model_dump())
    db.add(db_historial)
    
    # Actualizar stock del repuesto
    repuesto.cantidad -= historial.cantidad_usada
    
    db.commit()
    db.refresh(db_historial)
    return db_historial


def update_historial_repuesto(db: Session, historial_id: int, historial: HistorialRepuestoUpdate) -> Optional[HistorialRepuestos]:
    """Actualizar historial existente"""
    db_historial = db.query(HistorialRepuestos).filter(HistorialRepuestos.id == historial_id).first()
    if db_historial:
        # Si se actualiza la cantidad usada, ajustar el stock
        if 'cantidad_usada' in historial.model_dump(exclude_unset=True):
            diferencia = historial.cantidad_usada - db_historial.cantidad_usada
            repuesto = db.query(Repuestos).filter(Repuestos.id == db_historial.repuesto_id).first()
            if repuesto:
                if repuesto.cantidad < diferencia:
                    raise ValueError(f"Stock insuficiente para el ajuste. Disponible: {repuesto.cantidad}")
                repuesto.cantidad -= diferencia
        
        update_data = historial.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_historial, field, value)
        
        db.commit()
        db.refresh(db_historial)
    return db_historial


def delete_historial_repuesto(db: Session, historial_id: int) -> bool:
    """Eliminar historial y restaurar stock"""
    db_historial = db.query(HistorialRepuestos).filter(HistorialRepuestos.id == historial_id).first()
    if db_historial:
        # Restaurar stock al repuesto
        repuesto = db.query(Repuestos).filter(Repuestos.id == db_historial.repuesto_id).first()
        if repuesto:
            repuesto.cantidad += db_historial.cantidad_usada
        
        db.delete(db_historial)
        db.commit()
        return True
    return False


def get_consumo_por_repuesto(db: Session, repuesto_id: int, fecha_inicio: date = None, fecha_fin: date = None) -> dict:
    """Obtener estadísticas de consumo por repuesto"""
    query = db.query(HistorialRepuestos).filter(HistorialRepuestos.repuesto_id == repuesto_id)
    
    if fecha_inicio:
        query = query.filter(HistorialRepuestos.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(HistorialRepuestos.fecha <= fecha_fin)
    
    registros = query.all()
    
    return {
        "total_usado": sum(r.cantidad_usada for r in registros),
        "usos": len(registros),
        "promedio_por_uso": sum(r.cantidad_usada for r in registros) / len(registros) if registros else 0
    }