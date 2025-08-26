"""
Endpoints para gestión de Órdenes de Compra
"""
from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import (
    OrdenCompraResponse, 
    OrdenCompraCreate, 
    OrdenCompraUpdate,
    OrdenCompraListResponse,
    ItemOrdenResponse,
    ItemOrdenCreate,
    ItemOrdenUpdate,
    DocumentoOrdenResponse,
    ConfirmarLlegadaRequest
)
from crud import crud_ordenes_compra
from routers.auth import get_current_user
from models.models import Usuarios, DocumentosOrden

router = APIRouter(prefix="/ordenes-compra", tags=["Órdenes de Compra"])

# Directorio para almacenar documentos
UPLOAD_DIRECTORY = "uploads/ordenes_compra"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.xls', '.xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# === ÓRDENES DE COMPRA ===

@router.get("/", response_model=List[OrdenCompraResponse])
def listar_ordenes_compra(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener lista de órdenes de compra con filtros opcionales"""
    ordenes = crud_ordenes_compra.get_ordenes_compra(db, skip=skip, limit=limit, estado=estado)
    return ordenes


@router.get("/estadisticas", response_model=dict)
def obtener_estadisticas_ordenes(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener estadísticas de órdenes de compra"""
    return crud_ordenes_compra.get_estadisticas_ordenes(db)


@router.get("/{orden_id}", response_model=OrdenCompraResponse)
def obtener_orden_compra(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener orden de compra por ID"""
    orden = crud_ordenes_compra.get_orden_compra(db, orden_id=orden_id)
    if orden is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada"
        )
    return orden


@router.post("/", response_model=OrdenCompraResponse)
def crear_orden_compra(
    orden: OrdenCompraCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Crear nueva orden de compra"""
    try:
        nueva_orden = crud_ordenes_compra.create_orden_compra(db, orden=orden, usuario_id=current_user.id)
        return nueva_orden
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{orden_id}", response_model=OrdenCompraResponse)
def actualizar_orden_compra(
    orden_id: int,
    orden: OrdenCompraUpdate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Actualizar orden de compra"""
    try:
        orden_actualizada = crud_ordenes_compra.update_orden_compra(db, orden_id=orden_id, orden=orden)
        if orden_actualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden de compra no encontrada"
            )
        return orden_actualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{orden_id}")
def eliminar_orden_compra(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar orden de compra (solo si está en borrador)"""
    try:
        if not crud_ordenes_compra.delete_orden_compra(db, orden_id=orden_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden de compra no encontrada"
            )
        return {"message": "Orden de compra eliminada exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# === ITEMS DE ORDEN ===

@router.get("/{orden_id}/items", response_model=List[ItemOrdenResponse])
def obtener_items_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener items de una orden específica"""
    items = crud_ordenes_compra.get_items_orden(db, orden_id=orden_id)
    return items


@router.post("/{orden_id}/items", response_model=ItemOrdenResponse)
def agregar_item_orden(
    orden_id: int,
    item: ItemOrdenCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Agregar item a una orden existente"""
    try:
        nuevo_item = crud_ordenes_compra.add_item_orden(db, orden_id=orden_id, item=item)
        if nuevo_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden de compra no encontrada"
            )
        return nuevo_item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/items/{item_id}", response_model=ItemOrdenResponse)
def actualizar_item_orden(
    item_id: int,
    item: ItemOrdenUpdate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Actualizar item de orden"""
    try:
        item_actualizado = crud_ordenes_compra.update_item_orden(db, item_id=item_id, item=item)
        if item_actualizado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item de orden no encontrado"
            )
        return item_actualizado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/items/{item_id}")
def eliminar_item_orden(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar item de orden"""
    try:
        if not crud_ordenes_compra.delete_item_orden(db, item_id=item_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item de orden no encontrado"
            )
        return {"message": "Item eliminado exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# === DOCUMENTOS DE ORDEN ===

@router.post("/{orden_id}/documentos", response_model=DocumentoOrdenResponse)
async def subir_documento_orden(
    orden_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Subir documento a una orden de compra"""
    # Validar orden existe
    orden = crud_ordenes_compra.get_orden_compra(db, orden_id)
    if not orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada"
        )
    
    # Validar archivo
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionó archivo"
        )
    
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validar tamaño
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Archivo demasiado grande. Tamaño máximo: 10MB"
        )
    
    # Generar nombre único para el archivo
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Crear registro en base de datos
        documento = crud_ordenes_compra.add_documento_orden(
            db=db,
            orden_id=orden_id,
            nombre_archivo=file.filename,
            ruta_archivo=file_path,
            tipo_archivo=file.content_type or 'application/octet-stream',
            tamaño_archivo=len(file_content),
            usuario_id=current_user.id
        )
        
        return documento
        
    except Exception as e:
        # Limpiar archivo si falla la operación
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar archivo: {str(e)}"
        )


@router.delete("/documentos/{documento_id}")
def eliminar_documento_orden(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Eliminar documento de orden"""
    # Obtener documento para eliminar archivo físico
    documento = db.query(DocumentosOrden).filter(
        DocumentosOrden.id == documento_id
    ).first()
    
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Eliminar archivo físico
    if os.path.exists(documento.ruta_archivo):
        try:
            os.remove(documento.ruta_archivo)
        except:
            pass  # Continuar aunque falle la eliminación del archivo
    
    # Eliminar registro de base de datos
    if crud_ordenes_compra.delete_documento_orden(db, documento_id=documento_id):
        return {"message": "Documento eliminado exitosamente"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )


# === FUNCIONES ESPECIALES ===

@router.post("/{orden_id}/confirmar-llegada", response_model=OrdenCompraResponse)
def confirmar_llegada_repuestos(
    orden_id: int,
    llegada: ConfirmarLlegadaRequest,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Confirmar llegada de repuestos y actualizar inventario"""
    print(f"=== CONFIRMAR LLEGADA ENDPOINT ===")
    print(f"Orden ID: {orden_id}")
    print(f"Items recibidos: {llegada.items_recibidos}")
    
    try:
        orden_actualizada = crud_ordenes_compra.confirmar_llegada_repuestos(
            db, orden_id=orden_id, llegada=llegada
        )
        if orden_actualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden de compra no encontrada"
            )
        
        # Debug: mostrar repuestos después de la actualización
        print("=== REPUESTOS DESPUÉS DE ACTUALIZACIÓN ===")
        from models.models import Repuestos
        repuestos_debug = db.query(Repuestos).all()
        for rep in repuestos_debug[-5:]:  # Últimos 5 repuestos
            print(f"ID: {rep.id}, Código: {rep.codigo}, Nombre: {rep.nombre}, Cantidad: {rep.cantidad}")
        
        return orden_actualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{orden_id}/reset-estado")
def reset_estado_orden(
    orden_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Endpoint temporal para resetear estado de orden para pruebas"""
    orden_actualizada = crud_ordenes_compra.reset_orden_estado(db, orden_id=orden_id, nuevo_estado=nuevo_estado)
    if orden_actualizada is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada"
        )
    return {"message": f"Orden {orden_id} cambiada a estado {nuevo_estado}"}


@router.get("/numero-requisicion/{numero_requisicion}", response_model=OrdenCompraResponse)
def obtener_orden_por_numero_requisicion(
    numero_requisicion: str,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user)
):
    """Obtener orden por número de requisición"""
    orden = crud_ordenes_compra.get_orden_by_numero_requisicion(db, numero_requisicion=numero_requisicion)
    if orden is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada"
        )
    return orden