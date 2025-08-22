"""
Router para gestión de usuarios (solo admin)
"""
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from crud import crud_usuarios
from schemas.schemas import (
    UsuarioResponse, UsuarioCreate, UsuarioUpdate,
    AsignarPaginasRequest, RolResponse, PaginaResponse
)
from models.models import Usuarios
from routers.auth import get_current_admin_user

router = APIRouter(prefix="/usuarios", tags=["gestión de usuarios"])


@router.get("/", response_model=List[UsuarioResponse])
async def list_usuarios(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios (solo admin)"""
    usuarios = crud_usuarios.get_usuarios(db, skip=skip, limit=limit)
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Obtiene un usuario específico por ID (solo admin)"""
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


@router.post("/", response_model=UsuarioResponse)
async def create_usuario(
    usuario: UsuarioCreate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario (solo admin)"""
    
    # Verificar que el username no exista
    existing_user = crud_usuarios.get_usuario_by_username(db, usuario.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )
    
    # Verificar que el email no exista
    existing_email = crud_usuarios.get_usuario_by_email(db, usuario.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar que el rol existe (si se especificó)
    if usuario.rol_id:
        rol = crud_usuarios.get_rol(db, usuario.rol_id)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol especificado no existe"
            )
    
    nuevo_usuario = crud_usuarios.create_usuario(db, usuario)
    return nuevo_usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Actualiza un usuario existente (solo admin)"""
    
    # Verificar que el usuario existe
    existing_user = crud_usuarios.get_usuario(db, usuario_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Si se está cambiando el username, verificar que no exista
    if usuario.username and usuario.username != existing_user.username:
        user_with_username = crud_usuarios.get_usuario_by_username(db, usuario.username)
        if user_with_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya existe"
            )
    
    # Si se está cambiando el email, verificar que no exista
    if usuario.email and usuario.email != existing_user.email:
        user_with_email = crud_usuarios.get_usuario_by_email(db, usuario.email)
        if user_with_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    
    # Verificar que el rol existe (si se especificó)
    if usuario.rol_id:
        rol = crud_usuarios.get_rol(db, usuario.rol_id)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol especificado no existe"
            )
    
    usuario_actualizado = crud_usuarios.update_usuario(db, usuario_id, usuario)
    return usuario_actualizado


@router.delete("/{usuario_id}")
async def delete_usuario(
    usuario_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Desactiva un usuario (no lo elimina físicamente) (solo admin)"""
    
    # No permitir que el admin se desactive a sí mismo
    if usuario_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta"
        )
    
    # Verificar que el usuario existe
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    success = crud_usuarios.delete_usuario(db, usuario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar el usuario"
        )
    
    return {"message": f"Usuario {usuario.username} desactivado exitosamente"}


@router.post("/{usuario_id}/activate")
async def activate_usuario(
    usuario_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Reactiva un usuario desactivado (solo admin)"""
    
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario_update = UsuarioUpdate(activo=True)
    usuario_actualizado = crud_usuarios.update_usuario(db, usuario_id, usuario_update)
    
    return {"message": f"Usuario {usuario_actualizado.username} reactivado exitosamente"}


@router.post("/{usuario_id}/asignar-paginas")
async def asignar_paginas(
    usuario_id: int,
    asignacion: AsignarPaginasRequest,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Asigna páginas específicas a un usuario (solo admin)"""
    
    # Verificar que el usuario existe
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que las páginas existen
    for pagina_id in asignacion.paginas_ids:
        pagina = crud_usuarios.get_pagina(db, pagina_id)
        if not pagina:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La página con ID {pagina_id} no existe"
            )
    
    success = crud_usuarios.asignar_paginas_usuario(db, usuario_id, asignacion.paginas_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al asignar páginas al usuario"
        )
    
    return {"message": f"Páginas asignadas exitosamente al usuario {usuario.username}"}


@router.get("/{usuario_id}/paginas", response_model=List[PaginaResponse])
async def get_usuario_paginas(
    usuario_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Obtiene las páginas asignadas a un usuario específico (solo admin)"""
    
    # Verificar que el usuario existe
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    paginas = crud_usuarios.get_paginas_usuario(db, usuario_id)
    return paginas


@router.post("/{usuario_id}/unlock")
async def unlock_usuario(
    usuario_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Desbloquea un usuario que esté temporalmente bloqueado (solo admin)"""
    
    usuario = crud_usuarios.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Resetear intentos fallidos y desbloquear
    usuario_update = UsuarioUpdate()
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    
    return {"message": f"Usuario {usuario.username} desbloqueado exitosamente"}