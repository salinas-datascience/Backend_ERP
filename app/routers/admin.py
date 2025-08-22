"""
Router para gestión administrativa: roles, permisos y páginas (solo admin)
"""
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from crud import crud_usuarios
from schemas.schemas import (
    RolResponse, RolCreate, RolUpdate,
    PermisoResponse, PermisoCreate, PermisoUpdate,
    PaginaResponse, PaginaCreate, PaginaUpdate
)
from models.models import Usuarios, Roles, Permisos, Paginas
from routers.auth import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["administración"])


# === GESTIÓN DE ROLES ===

@router.get("/roles", response_model=List[RolResponse])
async def list_roles(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los roles (solo admin)"""
    roles = crud_usuarios.get_roles(db, skip=skip, limit=limit)
    return roles


@router.get("/roles/{rol_id}", response_model=RolResponse)
async def get_rol(
    rol_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Obtiene un rol específico por ID (solo admin)"""
    rol = crud_usuarios.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return rol


@router.post("/roles", response_model=RolResponse)
async def create_rol(
    rol: RolCreate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Crea un nuevo rol (solo admin)"""
    
    # Verificar que el nombre del rol no exista
    existing_rol = db.query(Roles).filter(Roles.nombre == rol.nombre).first()
    if existing_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un rol con ese nombre"
        )
    
    # Verificar que todos los permisos existen
    if rol.permisos_ids:
        for permiso_id in rol.permisos_ids:
            permiso = crud_usuarios.get_permiso(db, permiso_id)
            if not permiso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El permiso con ID {permiso_id} no existe"
                )
    
    nuevo_rol = crud_usuarios.create_rol(db, rol)
    return nuevo_rol


@router.put("/roles/{rol_id}", response_model=RolResponse)
async def update_rol(
    rol_id: int,
    rol: RolUpdate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Actualiza un rol existente (solo admin)"""
    
    # Verificar que el rol existe
    existing_rol = crud_usuarios.get_rol(db, rol_id)
    if not existing_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Si se está cambiando el nombre, verificar que no exista
    if rol.nombre and rol.nombre != existing_rol.nombre:
        rol_with_name = db.query(Roles).filter(Roles.nombre == rol.nombre).first()
        if rol_with_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre"
            )
    
    # Verificar que todos los permisos existen
    if rol.permisos_ids is not None:
        for permiso_id in rol.permisos_ids:
            permiso = crud_usuarios.get_permiso(db, permiso_id)
            if not permiso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El permiso con ID {permiso_id} no existe"
                )
    
    rol_actualizado = crud_usuarios.update_rol(db, rol_id, rol)
    return rol_actualizado


@router.delete("/roles/{rol_id}")
async def delete_rol(
    rol_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Desactiva un rol (no lo elimina físicamente) (solo admin)"""
    
    # Verificar que el rol existe
    rol = crud_usuarios.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Verificar que no hay usuarios asignados a este rol
    usuarios_con_rol = db.query(Usuarios).filter(Usuarios.rol_id == rol_id).count()
    if usuarios_con_rol > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar el rol porque hay {usuarios_con_rol} usuarios asignados a él"
        )
    
    success = crud_usuarios.delete_rol(db, rol_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar el rol"
        )
    
    return {"message": f"Rol {rol.nombre} desactivado exitosamente"}


# === GESTIÓN DE PERMISOS ===

@router.get("/permisos", response_model=List[PermisoResponse])
async def list_permisos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los permisos (solo admin)"""
    permisos = crud_usuarios.get_permisos(db, skip=skip, limit=limit)
    return permisos


@router.get("/permisos/{permiso_id}", response_model=PermisoResponse)
async def get_permiso(
    permiso_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Obtiene un permiso específico por ID (solo admin)"""
    permiso = crud_usuarios.get_permiso(db, permiso_id)
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    return permiso


@router.post("/permisos", response_model=PermisoResponse)
async def create_permiso(
    permiso: PermisoCreate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Crea un nuevo permiso (solo admin)"""
    
    # Verificar que el nombre del permiso no exista
    existing_permiso = db.query(Permisos).filter(Permisos.nombre == permiso.nombre).first()
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un permiso con ese nombre"
        )
    
    nuevo_permiso = crud_usuarios.create_permiso(db, permiso)
    return nuevo_permiso


@router.put("/permisos/{permiso_id}", response_model=PermisoResponse)
async def update_permiso(
    permiso_id: int,
    permiso: PermisoUpdate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Actualiza un permiso existente (solo admin)"""
    
    # Verificar que el permiso existe
    existing_permiso = crud_usuarios.get_permiso(db, permiso_id)
    if not existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    
    # Si se está cambiando el nombre, verificar que no exista
    if permiso.nombre and permiso.nombre != existing_permiso.nombre:
        permiso_with_name = db.query(Permisos).filter(Permisos.nombre == permiso.nombre).first()
        if permiso_with_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un permiso con ese nombre"
            )
    
    permiso_actualizado = crud_usuarios.update_permiso(db, permiso_id, permiso)
    return permiso_actualizado


@router.delete("/permisos/{permiso_id}")
async def delete_permiso(
    permiso_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Desactiva un permiso (no lo elimina físicamente) (solo admin)"""
    
    # Verificar que el permiso existe
    permiso = crud_usuarios.get_permiso(db, permiso_id)
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    
    success = crud_usuarios.delete_permiso(db, permiso_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar el permiso"
        )
    
    return {"message": f"Permiso {permiso.nombre} desactivado exitosamente"}


# === GESTIÓN DE PÁGINAS ===

@router.get("/paginas", response_model=List[PaginaResponse])
async def list_paginas(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Lista todas las páginas (solo admin)"""
    paginas = crud_usuarios.get_paginas(db, skip=skip, limit=limit)
    return paginas


@router.get("/paginas/{pagina_id}", response_model=PaginaResponse)
async def get_pagina(
    pagina_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Obtiene una página específica por ID (solo admin)"""
    pagina = crud_usuarios.get_pagina(db, pagina_id)
    if not pagina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Página no encontrada"
        )
    return pagina


@router.post("/paginas", response_model=PaginaResponse)
async def create_pagina(
    pagina: PaginaCreate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Crea una nueva página (solo admin)"""
    
    # Verificar que el nombre de la página no exista
    existing_pagina = db.query(Paginas).filter(Paginas.nombre == pagina.nombre).first()
    if existing_pagina:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una página con ese nombre"
        )
    
    # Verificar que la ruta no exista
    existing_ruta = db.query(Paginas).filter(Paginas.ruta == pagina.ruta).first()
    if existing_ruta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una página con esa ruta"
        )
    
    nueva_pagina = crud_usuarios.create_pagina(db, pagina)
    return nueva_pagina


@router.put("/paginas/{pagina_id}", response_model=PaginaResponse)
async def update_pagina(
    pagina_id: int,
    pagina: PaginaUpdate,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Actualiza una página existente (solo admin)"""
    
    # Verificar que la página existe
    existing_pagina = crud_usuarios.get_pagina(db, pagina_id)
    if not existing_pagina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Página no encontrada"
        )
    
    # Si se está cambiando el nombre, verificar que no exista
    if pagina.nombre and pagina.nombre != existing_pagina.nombre:
        pagina_with_name = db.query(Paginas).filter(Paginas.nombre == pagina.nombre).first()
        if pagina_with_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una página con ese nombre"
            )
    
    # Si se está cambiando la ruta, verificar que no exista
    if pagina.ruta and pagina.ruta != existing_pagina.ruta:
        pagina_with_ruta = db.query(Paginas).filter(Paginas.ruta == pagina.ruta).first()
        if pagina_with_ruta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una página con esa ruta"
            )
    
    pagina_actualizada = crud_usuarios.update_pagina(db, pagina_id, pagina)
    return pagina_actualizada


@router.delete("/paginas/{pagina_id}")
async def delete_pagina(
    pagina_id: int,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)] = None,
    db: Session = Depends(get_db)
):
    """Desactiva una página (no la elimina físicamente) (solo admin)"""
    
    # Verificar que la página existe
    pagina = crud_usuarios.get_pagina(db, pagina_id)
    if not pagina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Página no encontrada"
        )
    
    success = crud_usuarios.delete_pagina(db, pagina_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar la página"
        )
    
    return {"message": f"Página {pagina.nombre} desactivada exitosamente"}