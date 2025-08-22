"""
Router para endpoints de autenticación
"""
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from crud import crud_usuarios
from schemas.schemas import (
    LoginResponse, TokenData, UsuarioResponse, 
    ChangePasswordRequest, ResetPasswordRequest
)
from models.models import Usuarios

# Configuración JWT
SECRET_KEY = "tu_secret_key_super_secreta_aqui_cambiala_en_produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

router = APIRouter(prefix="/auth", tags=["autenticación"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> Usuarios:
    """Obtiene el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud_usuarios.get_usuario_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    # Verificar si el usuario está activo
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )
    
    # Verificar si está bloqueado
    if user.bloqueado_hasta and user.bloqueado_hasta > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario temporalmente bloqueado",
        )
    
    return user

async def get_current_active_user(
    current_user: Annotated[Usuarios, Depends(get_current_user)]
) -> Usuarios:
    """Obtiene el usuario actual activo"""
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

async def get_current_admin_user(
    current_user: Annotated[Usuarios, Depends(get_current_active_user)]
) -> Usuarios:
    """Verifica que el usuario actual sea administrador"""
    if not current_user.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user


@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Endpoint para login de usuarios"""
    user = crud_usuarios.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario bloqueado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el usuario está activo
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": user,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # en segundos
    }


@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(
    current_user: Annotated[Usuarios, Depends(get_current_active_user)]
):
    """Obtiene información del usuario actual"""
    return current_user


@router.get("/me/paginas")
async def get_my_pages(
    current_user: Annotated[Usuarios, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Obtiene las páginas permitidas para el usuario actual"""
    paginas = crud_usuarios.get_paginas_usuario(db, current_user.id)
    return {"paginas": paginas}


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[Usuarios, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Permite al usuario cambiar su propia contraseña"""
    
    # Verificar que las contraseñas nuevas coincidan
    if password_data.password_nueva != password_data.confirmar_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas nuevas no coinciden"
        )
    
    # Cambiar contraseña
    success = crud_usuarios.change_password(
        db, 
        current_user.id, 
        password_data.password_actual, 
        password_data.password_nueva
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    current_admin: Annotated[Usuarios, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    """Permite al admin resetear la contraseña de cualquier usuario"""
    
    # Verificar que el usuario existe
    target_user = crud_usuarios.get_usuario(db, reset_data.usuario_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Resetear contraseña
    success = crud_usuarios.reset_password(
        db, 
        reset_data.usuario_id, 
        reset_data.password_nueva,
        reset_data.forzar_cambio
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al resetear la contraseña"
        )
    
    return {"message": f"Contraseña reseteada para el usuario {target_user.username}"}


@router.post("/logout")
async def logout(
    current_user: Annotated[Usuarios, Depends(get_current_active_user)]
):
    """Endpoint para logout (principalmente para limpiar tokens en el cliente)"""
    return {"message": "Logout exitoso"}


@router.get("/check-token")
async def check_token(
    current_user: Annotated[Usuarios, Depends(get_current_active_user)]
):
    """Verifica si el token actual es válido"""
    return {
        "valid": True,
        "username": current_user.username,
        "debe_cambiar_password": current_user.debe_cambiar_password
    }