"""
Operaciones CRUD para gestión de usuarios, roles, permisos y páginas
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from passlib.context import CryptContext

from models.models import Usuarios, Roles, Permisos, Paginas
from schemas.schemas import (
    UsuarioCreate, UsuarioUpdate, 
    RolCreate, RolUpdate,
    PermisoCreate, PermisoUpdate,
    PaginaCreate, PaginaUpdate
)

# Configuración para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === UTILIDADES DE CONTRASEÑAS ===

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña"""
    return pwd_context.hash(password)

# === CRUD USUARIOS ===

def get_usuario(db: Session, usuario_id: int) -> Optional[Usuarios]:
    """Obtiene un usuario por ID"""
    return db.query(Usuarios).filter(Usuarios.id == usuario_id).first()

def get_usuario_by_username(db: Session, username: str) -> Optional[Usuarios]:
    """Obtiene un usuario por username"""
    return db.query(Usuarios).filter(Usuarios.username == username).first()

def get_usuario_by_email(db: Session, email: str) -> Optional[Usuarios]:
    """Obtiene un usuario por email"""
    return db.query(Usuarios).filter(Usuarios.email == email).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[Usuarios]:
    """Obtiene lista de usuarios con paginación"""
    return db.query(Usuarios).offset(skip).limit(limit).all()

def create_usuario(db: Session, usuario: UsuarioCreate) -> Usuarios:
    """Crea un nuevo usuario"""
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuarios(
        username=usuario.username,
        email=usuario.email,
        hashed_password=hashed_password,
        nombre_completo=usuario.nombre_completo,
        activo=usuario.activo,
        es_admin=usuario.es_admin,
        rol_id=usuario.rol_id,
        debe_cambiar_password=usuario.debe_cambiar_password,
        fecha_cambio_password=datetime.now()
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario(db: Session, usuario_id: int, usuario: UsuarioUpdate) -> Optional[Usuarios]:
    """Actualiza un usuario existente"""
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        for key, value in usuario.dict(exclude_unset=True).items():
            setattr(db_usuario, key, value)
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int) -> bool:
    """Elimina un usuario (lo desactiva)"""
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        db_usuario.activo = False
        db.commit()
        return True
    return False

def change_password(db: Session, usuario_id: int, current_password: str, new_password: str) -> bool:
    """Cambia la contraseña de un usuario"""
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario and verify_password(current_password, db_usuario.hashed_password):
        db_usuario.hashed_password = get_password_hash(new_password)
        db_usuario.debe_cambiar_password = False
        db_usuario.fecha_cambio_password = datetime.now()
        db_usuario.intentos_fallidos = 0  # Resetear intentos fallidos
        db.commit()
        return True
    return False

def reset_password(db: Session, usuario_id: int, new_password: str, force_change: bool = True) -> bool:
    """Resetea la contraseña de un usuario (solo admin)"""
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        db_usuario.hashed_password = get_password_hash(new_password)
        db_usuario.debe_cambiar_password = force_change
        db_usuario.fecha_cambio_password = datetime.now()
        db_usuario.intentos_fallidos = 0
        db_usuario.bloqueado_hasta = None
        db.commit()
        return True
    return False

def authenticate_user(db: Session, username: str, password: str) -> Optional[Usuarios]:
    """Autentica un usuario y maneja intentos fallidos"""
    user = get_usuario_by_username(db, username)
    if not user:
        return None
    
    # Verificar si está bloqueado
    if user.bloqueado_hasta and user.bloqueado_hasta > datetime.now():
        return None
    
    # Verificar contraseña
    if not verify_password(password, user.hashed_password):
        # Incrementar intentos fallidos
        user.intentos_fallidos = (user.intentos_fallidos or 0) + 1
        
        # Bloquear si superó 5 intentos (por 30 minutos)
        if user.intentos_fallidos >= 5:
            user.bloqueado_hasta = datetime.now() + timedelta(minutes=30)
        
        db.commit()
        return None
    
    # Login exitoso - resetear intentos fallidos y actualizar última conexión
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.ultima_conexion = datetime.now()
    db.commit()
    
    return user

def asignar_paginas_usuario(db: Session, usuario_id: int, paginas_ids: List[int]) -> bool:
    """Asigna páginas específicas a un usuario"""
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return False
    
    # Limpiar páginas actuales
    db_usuario.paginas_permitidas.clear()
    
    # Asignar nuevas páginas
    paginas = db.query(Paginas).filter(Paginas.id.in_(paginas_ids)).all()
    for pagina in paginas:
        db_usuario.paginas_permitidas.append(pagina)
    
    db.commit()
    return True

# === CRUD ROLES ===

def get_rol(db: Session, rol_id: int) -> Optional[Roles]:
    """Obtiene un rol por ID"""
    return db.query(Roles).filter(Roles.id == rol_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Roles]:
    """Obtiene lista de roles con paginación"""
    return db.query(Roles).offset(skip).limit(limit).all()

def create_rol(db: Session, rol: RolCreate) -> Roles:
    """Crea un nuevo rol"""
    db_rol = Roles(
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        activo=rol.activo
    )
    db.add(db_rol)
    db.flush()  # Para obtener el ID antes del commit
    
    # Asignar permisos si se especificaron
    if rol.permisos_ids:
        permisos = db.query(Permisos).filter(Permisos.id.in_(rol.permisos_ids)).all()
        for permiso in permisos:
            db_rol.permisos.append(permiso)
    
    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, rol_id: int, rol: RolUpdate) -> Optional[Roles]:
    """Actualiza un rol existente"""
    db_rol = get_rol(db, rol_id)
    if db_rol:
        # Actualizar campos básicos
        update_data = rol.dict(exclude_unset=True, exclude={'permisos_ids'})
        for key, value in update_data.items():
            setattr(db_rol, key, value)
        
        # Actualizar permisos si se especificaron
        if rol.permisos_ids is not None:
            db_rol.permisos.clear()
            permisos = db.query(Permisos).filter(Permisos.id.in_(rol.permisos_ids)).all()
            for permiso in permisos:
                db_rol.permisos.append(permiso)
        
        db.commit()
        db.refresh(db_rol)
    return db_rol

def delete_rol(db: Session, rol_id: int) -> bool:
    """Elimina un rol (lo desactiva)"""
    db_rol = get_rol(db, rol_id)
    if db_rol:
        db_rol.activo = False
        db.commit()
        return True
    return False

# === CRUD PERMISOS ===

def get_permiso(db: Session, permiso_id: int) -> Optional[Permisos]:
    """Obtiene un permiso por ID"""
    return db.query(Permisos).filter(Permisos.id == permiso_id).first()

def get_permisos(db: Session, skip: int = 0, limit: int = 100) -> List[Permisos]:
    """Obtiene lista de permisos con paginación"""
    return db.query(Permisos).offset(skip).limit(limit).all()

def create_permiso(db: Session, permiso: PermisoCreate) -> Permisos:
    """Crea un nuevo permiso"""
    db_permiso = Permisos(
        nombre=permiso.nombre,
        descripcion=permiso.descripcion,
        recurso=permiso.recurso,
        accion=permiso.accion,
        activo=permiso.activo
    )
    db.add(db_permiso)
    db.commit()
    db.refresh(db_permiso)
    return db_permiso

def update_permiso(db: Session, permiso_id: int, permiso: PermisoUpdate) -> Optional[Permisos]:
    """Actualiza un permiso existente"""
    db_permiso = get_permiso(db, permiso_id)
    if db_permiso:
        for key, value in permiso.dict(exclude_unset=True).items():
            setattr(db_permiso, key, value)
        db.commit()
        db.refresh(db_permiso)
    return db_permiso

def delete_permiso(db: Session, permiso_id: int) -> bool:
    """Elimina un permiso (lo desactiva)"""
    db_permiso = get_permiso(db, permiso_id)
    if db_permiso:
        db_permiso.activo = False
        db.commit()
        return True
    return False

# === CRUD PÁGINAS ===

def get_pagina(db: Session, pagina_id: int) -> Optional[Paginas]:
    """Obtiene una página por ID"""
    return db.query(Paginas).filter(Paginas.id == pagina_id).first()

def get_paginas(db: Session, skip: int = 0, limit: int = 100) -> List[Paginas]:
    """Obtiene lista de páginas con paginación"""
    return db.query(Paginas).order_by(Paginas.orden).offset(skip).limit(limit).all()

def get_paginas_usuario(db: Session, usuario_id: int) -> List[Paginas]:
    """Obtiene las páginas permitidas para un usuario"""
    usuario = get_usuario(db, usuario_id)
    if not usuario:
        return []
    
    if usuario.es_admin:
        # Admin ve todas las páginas activas
        return db.query(Paginas).filter(Paginas.activa == True).order_by(Paginas.orden).all()
    else:
        # Usuario normal solo ve sus páginas asignadas
        return [p for p in usuario.paginas_permitidas if p.activa]

def create_pagina(db: Session, pagina: PaginaCreate) -> Paginas:
    """Crea una nueva página"""
    db_pagina = Paginas(
        nombre=pagina.nombre,
        ruta=pagina.ruta,
        titulo=pagina.titulo,
        descripcion=pagina.descripcion,
        icono=pagina.icono,
        orden=pagina.orden,
        activa=pagina.activa,
        solo_admin=pagina.solo_admin
    )
    db.add(db_pagina)
    db.commit()
    db.refresh(db_pagina)
    return db_pagina

def update_pagina(db: Session, pagina_id: int, pagina: PaginaUpdate) -> Optional[Paginas]:
    """Actualiza una página existente"""
    db_pagina = get_pagina(db, pagina_id)
    if db_pagina:
        for key, value in pagina.dict(exclude_unset=True).items():
            setattr(db_pagina, key, value)
        db.commit()
        db.refresh(db_pagina)
    return db_pagina

def delete_pagina(db: Session, pagina_id: int) -> bool:
    """Elimina una página (la desactiva)"""
    db_pagina = get_pagina(db, pagina_id)
    if db_pagina:
        db_pagina.activa = False
        db.commit()
        return True
    return False