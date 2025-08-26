"""
CRUD operations for ordenes de trabajo de mantenimiento
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, text
from datetime import datetime, date

from models.models import OrdenesTrabajoMantenimiento, ComentariosOT, Maquinas, Usuarios, ArchivosOT, ArchivosComentarioOT
from schemas.schemas import (
    OrdenTrabajoCreate, 
    OrdenTrabajoUpdate,
    ComentarioOTCreate
)


class CRUDOrdenTrabajo:
    def get(self, db: Session, id: int) -> Optional[OrdenesTrabajoMantenimiento]:
        """Obtener una orden de trabajo por ID con relaciones cargadas"""
        return db.query(OrdenesTrabajoMantenimiento)\
            .options(
                joinedload(OrdenesTrabajoMantenimiento.maquina).joinedload(Maquinas.modelo),
                joinedload(OrdenesTrabajoMantenimiento.usuario_asignado),
                joinedload(OrdenesTrabajoMantenimiento.usuario_creador),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.archivos).joinedload(ArchivosOT.usuario)
            )\
            .filter(OrdenesTrabajoMantenimiento.id == id)\
            .first()

    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        estado: Optional[str] = None,
        nivel_criticidad: Optional[str] = None,
        usuario_asignado_id: Optional[int] = None,
        maquina_id: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        order_by: str = "fecha_creacion",
        order_direction: str = "desc"
    ) -> List[OrdenesTrabajoMantenimiento]:
        """Obtener múltiples órdenes de trabajo con filtros"""
        
        query = db.query(OrdenesTrabajoMantenimiento)\
            .options(
                joinedload(OrdenesTrabajoMantenimiento.maquina).joinedload(Maquinas.modelo),
                joinedload(OrdenesTrabajoMantenimiento.usuario_asignado),
                joinedload(OrdenesTrabajoMantenimiento.usuario_creador),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.archivos).joinedload(ArchivosOT.usuario)
            )
        
        # Filtro de búsqueda por título o descripción
        if search:
            search_filter = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    OrdenesTrabajoMantenimiento.titulo.ilike(search_filter),
                    OrdenesTrabajoMantenimiento.descripcion.ilike(search_filter)
                )
            )
        
        # Filtro por estado
        if estado:
            query = query.filter(OrdenesTrabajoMantenimiento.estado == estado)
        
        # Filtro por nivel de criticidad
        if nivel_criticidad:
            query = query.filter(OrdenesTrabajoMantenimiento.nivel_criticidad == nivel_criticidad)
        
        # Filtro por usuario asignado
        if usuario_asignado_id:
            query = query.filter(OrdenesTrabajoMantenimiento.usuario_asignado_id == usuario_asignado_id)
        
        # Filtro por máquina
        if maquina_id:
            query = query.filter(OrdenesTrabajoMantenimiento.maquina_id == maquina_id)
        
        # Filtro por rango de fechas
        if fecha_inicio:
            query = query.filter(OrdenesTrabajoMantenimiento.fecha_programada >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(OrdenesTrabajoMantenimiento.fecha_programada <= fecha_fin)
        
        # Ordenamiento
        if order_direction == "desc":
            if order_by == "fecha_creacion":
                query = query.order_by(desc(OrdenesTrabajoMantenimiento.fecha_creacion))
            elif order_by == "fecha_programada":
                query = query.order_by(desc(OrdenesTrabajoMantenimiento.fecha_programada))
            elif order_by == "nivel_criticidad":
                # Ordenar por criticidad: critica > alta > media > baja
                query = query.order_by(
                    desc(text("CASE WHEN nivel_criticidad = 'critica' THEN 4 "
                             "WHEN nivel_criticidad = 'alta' THEN 3 "
                             "WHEN nivel_criticidad = 'media' THEN 2 "
                             "WHEN nivel_criticidad = 'baja' THEN 1 "
                             "ELSE 0 END"))
                )
        else:
            if order_by == "fecha_creacion":
                query = query.order_by(asc(OrdenesTrabajoMantenimiento.fecha_creacion))
            elif order_by == "fecha_programada":
                query = query.order_by(asc(OrdenesTrabajoMantenimiento.fecha_programada))
            elif order_by == "nivel_criticidad":
                query = query.order_by(
                    asc(text("CASE WHEN nivel_criticidad = 'baja' THEN 1 "
                            "WHEN nivel_criticidad = 'media' THEN 2 "
                            "WHEN nivel_criticidad = 'alta' THEN 3 "
                            "WHEN nivel_criticidad = 'critica' THEN 4 "
                            "ELSE 5 END"))
                )
        
        return query.offset(skip).limit(limit).all()

    def get_by_user(
        self,
        db: Session,
        usuario_id: int,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenesTrabajoMantenimiento]:
        """Obtener órdenes de trabajo asignadas a un usuario específico"""
        
        query = db.query(OrdenesTrabajoMantenimiento)\
            .options(
                joinedload(OrdenesTrabajoMantenimiento.maquina).joinedload(Maquinas.modelo),
                joinedload(OrdenesTrabajoMantenimiento.usuario_creador),
                joinedload(OrdenesTrabajoMantenimiento.usuario_asignado),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.comentarios).joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario),
                joinedload(OrdenesTrabajoMantenimiento.archivos).joinedload(ArchivosOT.usuario)
            )\
            .filter(OrdenesTrabajoMantenimiento.usuario_asignado_id == usuario_id)
        
        if estado:
            query = query.filter(OrdenesTrabajoMantenimiento.estado == estado)
        
        query = query.order_by(desc(OrdenesTrabajoMantenimiento.fecha_programada))
        
        return query.offset(skip).limit(limit).all()

    def create(
        self, 
        db: Session, 
        *, 
        obj_in: OrdenTrabajoCreate, 
        usuario_creador_id: int
    ) -> OrdenesTrabajoMantenimiento:
        """Crear una nueva orden de trabajo"""
        
        db_obj = OrdenesTrabajoMantenimiento(
            titulo=obj_in.titulo,
            descripcion=obj_in.descripcion,
            maquina_id=obj_in.maquina_id,
            usuario_asignado_id=obj_in.usuario_asignado_id,
            usuario_creador_id=usuario_creador_id,
            nivel_criticidad=obj_in.nivel_criticidad,
            fecha_programada=obj_in.fecha_programada,
            tiempo_estimado_horas=obj_in.tiempo_estimado_horas,
            estado="pendiente"
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Cargar relaciones
        return self.get(db, id=db_obj.id)

    def update(
        self, 
        db: Session, 
        *, 
        db_obj: OrdenesTrabajoMantenimiento, 
        obj_in: OrdenTrabajoUpdate
    ) -> OrdenesTrabajoMantenimiento:
        """Actualizar una orden de trabajo"""
        
        update_data = obj_in.dict(exclude_unset=True)
        
        # Manejar cambio de estado con timestamps
        if "estado" in update_data:
            nuevo_estado = update_data["estado"]
            if nuevo_estado == "en_proceso" and db_obj.fecha_inicio is None:
                update_data["fecha_inicio"] = datetime.utcnow()
            elif nuevo_estado == "completada" and db_obj.fecha_finalizacion is None:
                update_data["fecha_finalizacion"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return self.get(db, id=db_obj.id)

    def delete(self, db: Session, *, id: int) -> OrdenesTrabajoMantenimiento:
        """Eliminar una orden de trabajo"""
        obj = db.query(OrdenesTrabajoMantenimiento).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Obtener estadísticas de órdenes de trabajo"""
        
        stats = {}
        
        # Contar por estado
        estados = ["pendiente", "en_proceso", "completada", "cancelada"]
        for estado in estados:
            count = db.query(OrdenesTrabajoMantenimiento)\
                .filter(OrdenesTrabajoMantenimiento.estado == estado)\
                .count()
            stats[f"total_{estado}"] = count
        
        # Contar por criticidad
        criticidades = ["baja", "media", "alta", "critica"]
        for criticidad in criticidades:
            count = db.query(OrdenesTrabajoMantenimiento)\
                .filter(OrdenesTrabajoMantenimiento.nivel_criticidad == criticidad)\
                .count()
            stats[f"total_{criticidad}"] = count
        
        # Total general
        stats["total_general"] = db.query(OrdenesTrabajoMantenimiento).count()
        
        # OTs vencidas (fecha programada pasada y no completadas)
        from datetime import date
        hoy = date.today()
        stats["total_vencidas"] = db.query(OrdenesTrabajoMantenimiento)\
            .filter(
                and_(
                    OrdenesTrabajoMantenimiento.fecha_programada < hoy,
                    OrdenesTrabajoMantenimiento.estado.in_(["pendiente", "en_proceso"])
                )
            ).count()
        
        return stats


class CRUDComentarioOT:
    def create(
        self,
        db: Session,
        *,
        obj_in: ComentarioOTCreate,
        usuario_id: int
    ) -> ComentariosOT:
        """Crear un nuevo comentario en una OT"""
        
        db_obj = ComentariosOT(
            orden_trabajo_id=obj_in.orden_trabajo_id,
            usuario_id=usuario_id,
            comentario=obj_in.comentario
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Cargar relaciones con usuario y archivos
        db_obj = db.query(ComentariosOT)\
            .options(
                joinedload(ComentariosOT.usuario),
                joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario)
            )\
            .filter(ComentariosOT.id == db_obj.id)\
            .first()
        
        return db_obj

    def get(self, db: Session, id: int) -> Optional[ComentariosOT]:
        """Obtener un comentario por ID"""
        return db.query(ComentariosOT)\
            .options(
                joinedload(ComentariosOT.usuario),
                joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario)
            )\
            .filter(ComentariosOT.id == id)\
            .first()

    def get_by_orden_trabajo(
        self,
        db: Session,
        orden_trabajo_id: int
    ) -> List[ComentariosOT]:
        """Obtener comentarios de una orden de trabajo"""
        
        return db.query(ComentariosOT)\
            .options(
                joinedload(ComentariosOT.usuario),
                joinedload(ComentariosOT.archivos).joinedload(ArchivosComentarioOT.usuario)
            )\
            .filter(ComentariosOT.orden_trabajo_id == orden_trabajo_id)\
            .order_by(desc(ComentariosOT.fecha_creacion))\
            .all()


# Instancias
crud_orden_trabajo = CRUDOrdenTrabajo()
crud_comentario_ot = CRUDComentarioOT()