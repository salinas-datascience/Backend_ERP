"""
Operaciones CRUD para archivos de órdenes de trabajo
"""
import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from models.models import ArchivosOT, ArchivosComentarioOT
from fastapi import UploadFile
import shutil
from datetime import datetime


class CRUDArchivoOT:
    """CRUD operations para archivos de órdenes de trabajo"""
    
    def create(self, db: Session, *, archivo: UploadFile, orden_trabajo_id: int, usuario_id: int, upload_dir: str = "uploads/ot/") -> ArchivosOT:
        """Guardar archivo de orden de trabajo"""
        # Crear directorio si no existe
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(archivo.filename)[1] if archivo.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo en disco
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        
        # Crear registro en base de datos
        db_obj = ArchivosOT(
            orden_trabajo_id=orden_trabajo_id,
            usuario_id=usuario_id,
            nombre_archivo=archivo.filename or "archivo",
            nombre_archivo_sistema=unique_filename,
            ruta_archivo=file_path,
            tipo_mime=archivo.content_type or "application/octet-stream",
            tamaño_bytes=os.path.getsize(file_path)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_orden_trabajo(self, db: Session, orden_trabajo_id: int) -> List[ArchivosOT]:
        """Obtener archivos de una orden de trabajo"""
        return db.query(ArchivosOT).options(
            joinedload(ArchivosOT.usuario)
        ).filter(ArchivosOT.orden_trabajo_id == orden_trabajo_id).all()
    
    def get(self, db: Session, id: int) -> Optional[ArchivosOT]:
        """Obtener archivo por ID"""
        return db.query(ArchivosOT).options(
            joinedload(ArchivosOT.usuario)
        ).filter(ArchivosOT.id == id).first()
    
    def delete(self, db: Session, id: int) -> bool:
        """Eliminar archivo"""
        db_obj = db.query(ArchivosOT).filter(ArchivosOT.id == id).first()
        if db_obj:
            # Eliminar archivo del disco
            if os.path.exists(db_obj.ruta_archivo):
                os.remove(db_obj.ruta_archivo)
            
            # Eliminar registro de la base de datos
            db.delete(db_obj)
            db.commit()
            return True
        return False


class CRUDArchivoComentarioOT:
    """CRUD operations para archivos de comentarios de órdenes de trabajo"""
    
    def create(self, db: Session, *, archivo: UploadFile, comentario_id: int, usuario_id: int, upload_dir: str = "uploads/comentarios/") -> ArchivosComentarioOT:
        """Guardar archivo de comentario"""
        # Crear directorio si no existe
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(archivo.filename)[1] if archivo.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo en disco
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        
        # Crear registro en base de datos
        db_obj = ArchivosComentarioOT(
            comentario_id=comentario_id,
            usuario_id=usuario_id,
            nombre_archivo=archivo.filename or "archivo",
            nombre_archivo_sistema=unique_filename,
            ruta_archivo=file_path,
            tipo_mime=archivo.content_type or "application/octet-stream",
            tamaño_bytes=os.path.getsize(file_path)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_comentario(self, db: Session, comentario_id: int) -> List[ArchivosComentarioOT]:
        """Obtener archivos de un comentario"""
        return db.query(ArchivosComentarioOT).options(
            joinedload(ArchivosComentarioOT.usuario)
        ).filter(ArchivosComentarioOT.comentario_id == comentario_id).all()
    
    def get(self, db: Session, id: int) -> Optional[ArchivosComentarioOT]:
        """Obtener archivo por ID"""
        return db.query(ArchivosComentarioOT).options(
            joinedload(ArchivosComentarioOT.usuario)
        ).filter(ArchivosComentarioOT.id == id).first()
    
    def delete(self, db: Session, id: int) -> bool:
        """Eliminar archivo"""
        db_obj = db.query(ArchivosComentarioOT).filter(ArchivosComentarioOT.id == id).first()
        if db_obj:
            # Eliminar archivo del disco
            if os.path.exists(db_obj.ruta_archivo):
                os.remove(db_obj.ruta_archivo)
            
            # Eliminar registro de la base de datos
            db.delete(db_obj)
            db.commit()
            return True
        return False


# Instancias globales
crud_archivo_ot = CRUDArchivoOT()
crud_archivo_comentario_ot = CRUDArchivoComentarioOT()