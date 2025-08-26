"""
API Router para órdenes de trabajo de mantenimiento
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from database import get_db
from routers.auth import get_current_user
from models.models import Usuarios
from schemas.schemas import (
    OrdenTrabajoCreate,
    OrdenTrabajoUpdate,
    OrdenTrabajoResponse,
    OrdenTrabajoListResponse,
    ComentarioOTCreate,
    ComentarioOTResponse,
    EstadisticasOT,
    ArchivoOTResponse,
    ArchivoComentarioOTResponse
)
from crud.crud_ordenes_trabajo import crud_orden_trabajo, crud_comentario_ot
from crud.crud_archivos import crud_archivo_ot, crud_archivo_comentario_ot

router = APIRouter()


@router.get("/stats", response_model=EstadisticasOT)
def get_ordenes_trabajo_stats(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener estadísticas de órdenes de trabajo"""
    stats = crud_orden_trabajo.get_stats(db)
    return EstadisticasOT(**stats)


@router.get("/", response_model=List[OrdenTrabajoResponse])
def read_ordenes_trabajo(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None, description="Buscar por título o descripción"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    nivel_criticidad: Optional[str] = Query(None, description="Filtrar por nivel de criticidad"),
    usuario_asignado_id: Optional[int] = Query(None, description="Filtrar por usuario asignado"),
    maquina_id: Optional[int] = Query(None, description="Filtrar por máquina"),
    fecha_inicio: Optional[date] = Query(None, description="Filtrar desde fecha"),
    fecha_fin: Optional[date] = Query(None, description="Filtrar hasta fecha"),
    order_by: str = Query("fecha_creacion", description="Campo de ordenamiento"),
    order_direction: str = Query("desc", description="Dirección del ordenamiento"),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener lista de órdenes de trabajo con filtros"""
    ordenes = crud_orden_trabajo.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        estado=estado,
        nivel_criticidad=nivel_criticidad,
        usuario_asignado_id=usuario_asignado_id,
        maquina_id=maquina_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        order_by=order_by,
        order_direction=order_direction
    )
    return ordenes


@router.get("/mis-ordenes", response_model=List[OrdenTrabajoResponse])
def read_mis_ordenes_trabajo(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener órdenes de trabajo asignadas al usuario actual"""
    ordenes = crud_orden_trabajo.get_by_user(
        db=db,
        usuario_id=current_user.id,
        estado=estado,
        skip=skip,
        limit=limit
    )
    return ordenes


@router.post("/", response_model=OrdenTrabajoResponse)
def create_orden_trabajo(
    *,
    db: Session = Depends(get_db),
    orden_in: OrdenTrabajoCreate,
    current_user: Usuarios = Depends(get_current_user)
):
    """Crear nueva orden de trabajo"""
    
    # Validar nivel de criticidad
    niveles_validos = ["baja", "media", "alta", "critica"]
    if orden_in.nivel_criticidad not in niveles_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel de criticidad debe ser uno de: {', '.join(niveles_validos)}"
        )
    
    # Verificar que la máquina existe
    from crud.crud_maquinas import get_maquina
    maquina = get_maquina(db=db, maquina_id=orden_in.maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    # Verificar que el usuario asignado existe
    from crud.crud_usuarios import get_usuario
    usuario_asignado = get_usuario(db=db, usuario_id=orden_in.usuario_asignado_id)
    if not usuario_asignado:
        raise HTTPException(status_code=404, detail="Usuario asignado no encontrado")
    
    orden = crud_orden_trabajo.create(
        db=db,
        obj_in=orden_in,
        usuario_creador_id=current_user.id
    )
    return orden


@router.get("/{id}", response_model=OrdenTrabajoResponse)
def read_orden_trabajo(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener orden de trabajo por ID"""
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    return orden


@router.put("/{id}", response_model=OrdenTrabajoResponse)
def update_orden_trabajo(
    *,
    db: Session = Depends(get_db),
    id: int,
    orden_in: OrdenTrabajoUpdate,
    current_user: Usuarios = Depends(get_current_user)
):
    """Actualizar orden de trabajo"""
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Validar nivel de criticidad si se proporciona
    if orden_in.nivel_criticidad:
        niveles_validos = ["baja", "media", "alta", "critica"]
        if orden_in.nivel_criticidad not in niveles_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Nivel de criticidad debe ser uno de: {', '.join(niveles_validos)}"
            )
    
    # Validar estado si se proporciona
    if orden_in.estado:
        estados_validos = ["pendiente", "en_proceso", "completada", "cancelada"]
        if orden_in.estado not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Estado debe ser uno de: {', '.join(estados_validos)}"
            )
    
    # Verificar que la máquina existe si se cambia
    if orden_in.maquina_id:
        from crud.crud_maquinas import get_maquina
        maquina = get_maquina(db=db, maquina_id=orden_in.maquina_id)
        if not maquina:
            raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    # Verificar que el usuario asignado existe si se cambia
    if orden_in.usuario_asignado_id:
        from crud.crud_usuarios import get_usuario
        usuario_asignado = get_usuario(db=db, usuario_id=orden_in.usuario_asignado_id)
        if not usuario_asignado:
            raise HTTPException(status_code=404, detail="Usuario asignado no encontrado")
    
    orden = crud_orden_trabajo.update(db=db, db_obj=orden, obj_in=orden_in)
    return orden


@router.delete("/{id}")
def delete_orden_trabajo(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar orden de trabajo"""
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    crud_orden_trabajo.delete(db=db, id=id)
    return {"message": "Orden de trabajo eliminada exitosamente"}


# Endpoints para comentarios
@router.post("/{id}/comentarios", response_model=ComentarioOTResponse)
def create_comentario(
    *,
    db: Session = Depends(get_db),
    id: int,
    comentario_in: ComentarioOTCreate,
    current_user: Usuarios = Depends(get_current_user)
):
    """Agregar comentario a una orden de trabajo"""
    
    # Verificar que la orden de trabajo existe
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Asegurar que el comentario está vinculado a la orden correcta
    comentario_in.orden_trabajo_id = id
    
    comentario = crud_comentario_ot.create(
        db=db,
        obj_in=comentario_in,
        usuario_id=current_user.id
    )
    return comentario


@router.get("/{id}/comentarios", response_model=List[ComentarioOTResponse])
def read_comentarios(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener comentarios de una orden de trabajo"""
    
    # Verificar que la orden de trabajo existe
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    comentarios = crud_comentario_ot.get_by_orden_trabajo(db=db, orden_trabajo_id=id)
    return comentarios


# Endpoint para cambiar estado rápidamente
@router.patch("/{id}/estado")
def cambiar_estado_orden(
    *,
    db: Session = Depends(get_db),
    id: int,
    estado: str,
    current_user: Usuarios = Depends(get_current_user)
):
    """Cambiar solo el estado de una orden de trabajo"""
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    estados_validos = ["pendiente", "en_proceso", "completada", "cancelada"]
    if estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado debe ser uno de: {', '.join(estados_validos)}"
        )
    
    orden_update = OrdenTrabajoUpdate(estado=estado)
    orden = crud_orden_trabajo.update(db=db, db_obj=orden, obj_in=orden_update)
    
    return {"message": f"Estado cambiado a {estado}", "orden": orden}


# === ENDPOINTS PARA ARCHIVOS ===

# Endpoints para archivos de órdenes de trabajo
@router.post("/{id}/archivos", response_model=ArchivoOTResponse)
def upload_archivo_ot(
    *,
    db: Session = Depends(get_db),
    id: int,
    archivo: UploadFile = File(...),
    current_user: Usuarios = Depends(get_current_user)
):
    """Subir archivo a una orden de trabajo"""
    # Verificar que la orden existe
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Verificar tamaño del archivo (máximo 50MB)
    max_size = 50 * 1024 * 1024  # 50MB en bytes
    archivo.file.seek(0, 2)  # Ir al final del archivo
    file_size = archivo.file.tell()
    archivo.file.seek(0)  # Volver al inicio
    
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande. Máximo 50MB.")
    
    # Verificar tipos de archivo permitidos
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", 
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    
    if archivo.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Tipo de archivo no permitido.")
    
    try:
        db_archivo = crud_archivo_ot.create(
            db=db,
            archivo=archivo,
            orden_trabajo_id=id,
            usuario_id=current_user.id
        )
        return db_archivo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


@router.get("/{id}/archivos", response_model=List[ArchivoOTResponse])
def get_archivos_ot(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener archivos de una orden de trabajo"""
    orden = crud_orden_trabajo.get(db=db, id=id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    archivos = crud_archivo_ot.get_by_orden_trabajo(db=db, orden_trabajo_id=id)
    return archivos


@router.get("/archivos/{archivo_id}/download")
def download_archivo_ot(
    *,
    db: Session = Depends(get_db),
    archivo_id: int
):
    """Descargar archivo de orden de trabajo"""
    archivo = crud_archivo_ot.get(db=db, id=archivo_id)
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not os.path.exists(archivo.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo no existe en el sistema")
    
    return FileResponse(
        path=archivo.ruta_archivo,
        filename=archivo.nombre_archivo,
        media_type=archivo.tipo_mime
    )


@router.delete("/archivos/{archivo_id}")
def delete_archivo_ot(
    *,
    db: Session = Depends(get_db),
    archivo_id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar archivo de orden de trabajo"""
    archivo = crud_archivo_ot.get(db=db, id=archivo_id)
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Solo el usuario que subió el archivo o un admin puede eliminarlo
    if archivo.usuario_id != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este archivo")
    
    success = crud_archivo_ot.delete(db=db, id=archivo_id)
    if success:
        return {"message": "Archivo eliminado correctamente"}
    else:
        raise HTTPException(status_code=500, detail="Error al eliminar archivo")


# Endpoints para archivos de comentarios
@router.post("/comentarios/{comentario_id}/archivos", response_model=ArchivoComentarioOTResponse)
def upload_archivo_comentario(
    *,
    db: Session = Depends(get_db),
    comentario_id: int,
    archivo: UploadFile = File(...),
    current_user: Usuarios = Depends(get_current_user)
):
    """Subir archivo a un comentario"""
    # Verificar que el comentario existe
    comentario = crud_comentario_ot.get(db=db, id=comentario_id)
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    # Verificar que el usuario puede agregar archivos a este comentario
    if comentario.usuario_id != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para agregar archivos a este comentario")
    
    # Verificar tamaño del archivo (máximo 20MB para comentarios)
    max_size = 20 * 1024 * 1024  # 20MB en bytes
    archivo.file.seek(0, 2)  # Ir al final del archivo
    file_size = archivo.file.tell()
    archivo.file.seek(0)  # Volver al inicio
    
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande. Máximo 20MB.")
    
    # Verificar tipos de archivo permitidos (más restrictivo para comentarios)
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain"
    ]
    
    if archivo.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Tipo de archivo no permitido.")
    
    try:
        db_archivo = crud_archivo_comentario_ot.create(
            db=db,
            archivo=archivo,
            comentario_id=comentario_id,
            usuario_id=current_user.id
        )
        return db_archivo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


@router.get("/comentarios/{comentario_id}/archivos", response_model=List[ArchivoComentarioOTResponse])
def get_archivos_comentario(
    *,
    db: Session = Depends(get_db),
    comentario_id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener archivos de un comentario"""
    comentario = crud_comentario_ot.get(db=db, id=comentario_id)
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    archivos = crud_archivo_comentario_ot.get_by_comentario(db=db, comentario_id=comentario_id)
    return archivos


@router.get("/comentarios/archivos/{archivo_id}/download")
def download_archivo_comentario(
    *,
    db: Session = Depends(get_db),
    archivo_id: int
):
    """Descargar archivo de comentario"""
    archivo = crud_archivo_comentario_ot.get(db=db, id=archivo_id)
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not os.path.exists(archivo.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo no existe en el sistema")
    
    return FileResponse(
        path=archivo.ruta_archivo,
        filename=archivo.nombre_archivo,
        media_type=archivo.tipo_mime
    )


@router.delete("/comentarios/archivos/{archivo_id}")
def delete_archivo_comentario(
    *,
    db: Session = Depends(get_db),
    archivo_id: int,
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar archivo de comentario"""
    archivo = crud_archivo_comentario_ot.get(db=db, id=archivo_id)
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Solo el usuario que subió el archivo o un admin puede eliminarlo
    if archivo.usuario_id != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este archivo")
    
    success = crud_archivo_comentario_ot.delete(db=db, id=archivo_id)
    if success:
        return {"message": "Archivo eliminado correctamente"}
    else:
        raise HTTPException(status_code=500, detail="Error al eliminar archivo")