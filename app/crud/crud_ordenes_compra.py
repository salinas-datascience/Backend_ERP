"""
Operaciones CRUD para Órdenes de Compra
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from models.models import (
    OrdenesCompra, 
    ItemsOrdenCompra, 
    DocumentosOrden, 
    Repuestos,
    Proveedores
)
from schemas.schemas import (
    OrdenCompraCreate, 
    OrdenCompraUpdate, 
    ItemOrdenCreate,
    ItemOrdenUpdate,
    ConfirmarLlegadaRequest
)


# === ÓRDENES DE COMPRA ===

def get_ordenes_compra(db: Session, skip: int = 0, limit: int = 100, estado: Optional[str] = None) -> List[OrdenesCompra]:
    """Obtener lista de órdenes de compra con paginación y filtro por estado"""
    query = db.query(OrdenesCompra).options(
        joinedload(OrdenesCompra.proveedor),
        joinedload(OrdenesCompra.usuario_creador),
        joinedload(OrdenesCompra.items).joinedload(ItemsOrdenCompra.repuesto),
        joinedload(OrdenesCompra.documentos)
    )
    
    if estado:
        query = query.filter(OrdenesCompra.estado == estado)
    
    return query.order_by(OrdenesCompra.fecha_creacion.desc()).offset(skip).limit(limit).all()


def get_orden_compra(db: Session, orden_id: int) -> Optional[OrdenesCompra]:
    """Obtener orden de compra por ID con todas las relaciones"""
    return db.query(OrdenesCompra).options(
        joinedload(OrdenesCompra.proveedor),
        joinedload(OrdenesCompra.usuario_creador),
        joinedload(OrdenesCompra.items).joinedload(ItemsOrdenCompra.repuesto),
        joinedload(OrdenesCompra.documentos)
    ).filter(OrdenesCompra.id == orden_id).first()


def get_orden_by_numero_requisicion(db: Session, numero_requisicion: str) -> Optional[OrdenesCompra]:
    """Obtener orden por número de requisición"""
    return db.query(OrdenesCompra).filter(OrdenesCompra.numero_requisicion == numero_requisicion).first()


def create_orden_compra(db: Session, orden: OrdenCompraCreate, usuario_id: int) -> OrdenesCompra:
    """Crear nueva orden de compra con items"""
    db_orden = OrdenesCompra(
        proveedor_id=orden.proveedor_id,
        observaciones=orden.observaciones,
        usuario_creador_id=usuario_id,
        estado='borrador'
    )
    
    db.add(db_orden)
    db.flush()  # Para obtener el ID antes del commit
    
    # Crear items de la orden
    for item_data in orden.items:
        db_item = ItemsOrdenCompra(
            orden_id=db_orden.id,
            repuesto_id=item_data.repuesto_id,
            cantidad_pedida=item_data.cantidad_pedida,
            descripcion_aduana=item_data.descripcion_aduana,
            precio_unitario=item_data.precio_unitario,
            # Campos para items manuales
            es_item_manual=getattr(item_data, 'es_item_manual', False),
            nombre_manual=getattr(item_data, 'nombre_manual', None),
            codigo_manual=getattr(item_data, 'codigo_manual', None),
            detalle_manual=getattr(item_data, 'detalle_manual', None),
            cantidad_minima_manual=getattr(item_data, 'cantidad_minima_manual', None)
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_orden)
    
    # Cargar relaciones
    return get_orden_compra(db, db_orden.id)


def update_orden_compra(db: Session, orden_id: int, orden: OrdenCompraUpdate) -> Optional[OrdenesCompra]:
    """Actualizar orden de compra"""
    db_orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == orden_id).first()
    if not db_orden:
        return None
    
    # Validar cambios de estado
    if orden.estado:
        if not _validar_cambio_estado(db_orden.estado, orden.estado):
            raise ValueError(f"Cambio de estado no válido: {db_orden.estado} -> {orden.estado}")
        
        # Si cambia a cotizado, debe tener numero_requisicion
        if orden.estado == 'cotizado' and not orden.numero_requisicion:
            raise ValueError("Debe proporcionar un número de requisición para cambiar a estado 'cotizado'")
            
        # Si cambia a confirmado, debe tener legajo
        if orden.estado == 'confirmado' and not orden.legajo:
            raise ValueError("Debe proporcionar un legajo para cambiar a estado 'confirmado'")
    
    # Actualizar campos
    update_data = orden.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_orden, field, value)
    
    db.commit()
    db.refresh(db_orden)
    
    return get_orden_compra(db, orden_id)


def delete_orden_compra(db: Session, orden_id: int) -> bool:
    """Eliminar orden de compra (solo si no está confirmada)"""
    db_orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == orden_id).first()
    if not db_orden:
        return False
    
    if db_orden.estado in ['confirmado', 'completado']:
        raise ValueError("No se pueden eliminar órdenes confirmadas o completadas")
    
    db.delete(db_orden)
    db.commit()
    return True


# === ITEMS DE ORDEN ===

def get_items_orden(db: Session, orden_id: int) -> List[ItemsOrdenCompra]:
    """Obtener items de una orden específica"""
    return db.query(ItemsOrdenCompra).options(
        joinedload(ItemsOrdenCompra.repuesto)
    ).filter(ItemsOrdenCompra.orden_id == orden_id).all()


def add_item_orden(db: Session, orden_id: int, item: ItemOrdenCreate) -> Optional[ItemsOrdenCompra]:
    """Agregar item a una orden existente"""
    # Verificar que la orden existe y está editable
    orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == orden_id).first()
    if not orden:
        return None
    
    if orden.estado in ['confirmado', 'completado']:
        raise ValueError("No se pueden agregar items a órdenes confirmadas o completadas")
    
    # Validar item manual
    if item.es_item_manual:
        if not item.nombre_manual or not item.codigo_manual:
            raise ValueError("Items manuales requieren nombre y código")
        
        # Verificar que no existe otro item manual con el mismo código en la orden
        existing_manual = db.query(ItemsOrdenCompra).filter(
            ItemsOrdenCompra.orden_id == orden_id,
            ItemsOrdenCompra.es_item_manual == True,
            ItemsOrdenCompra.codigo_manual == item.codigo_manual
        ).first()
        
        if existing_manual:
            raise ValueError(f"Ya existe un item manual con código '{item.codigo_manual}' en esta orden")
    
    db_item = ItemsOrdenCompra(
        orden_id=orden_id,
        repuesto_id=item.repuesto_id,
        cantidad_pedida=item.cantidad_pedida,
        descripcion_aduana=item.descripcion_aduana,
        precio_unitario=item.precio_unitario,
        es_item_manual=item.es_item_manual,
        nombre_manual=item.nombre_manual,
        codigo_manual=item.codigo_manual,
        detalle_manual=item.detalle_manual,
        cantidad_minima_manual=item.cantidad_minima_manual
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db.query(ItemsOrdenCompra).options(
        joinedload(ItemsOrdenCompra.repuesto)
    ).filter(ItemsOrdenCompra.id == db_item.id).first()


def update_item_orden(db: Session, item_id: int, item: ItemOrdenUpdate) -> Optional[ItemsOrdenCompra]:
    """Actualizar item de orden"""
    db_item = db.query(ItemsOrdenCompra).filter(ItemsOrdenCompra.id == item_id).first()
    if not db_item:
        return None
    
    # Verificar que la orden está editable (excepto para cantidad_recibida)
    orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == db_item.orden_id).first()
    if orden.estado == 'confirmado':
        # Solo permitir actualizar cantidad_recibida
        restricted_fields = ['repuesto_id', 'cantidad_pedida', 'descripcion_aduana', 'precio_unitario']
        if any(field in item.model_dump(exclude_unset=True) for field in restricted_fields):
            raise ValueError("Solo se puede actualizar cantidad_recibida en órdenes en estado 'confirmado'")
    
    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db.query(ItemsOrdenCompra).options(
        joinedload(ItemsOrdenCompra.repuesto)
    ).filter(ItemsOrdenCompra.id == item_id).first()


def delete_item_orden(db: Session, item_id: int) -> bool:
    """Eliminar item de orden"""
    db_item = db.query(ItemsOrdenCompra).filter(ItemsOrdenCompra.id == item_id).first()
    if not db_item:
        return False
    
    # Verificar que la orden está editable
    orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == db_item.orden_id).first()
    if orden.estado in ['confirmado', 'completado']:
        raise ValueError("No se pueden eliminar items de órdenes confirmadas o completadas")
    
    db.delete(db_item)
    db.commit()
    return True


# === DOCUMENTOS DE ORDEN ===

def add_documento_orden(db: Session, orden_id: int, nombre_archivo: str, ruta_archivo: str, 
                       tipo_archivo: str, tamaño_archivo: int, usuario_id: int) -> DocumentosOrden:
    """Agregar documento a una orden"""
    db_documento = DocumentosOrden(
        orden_id=orden_id,
        nombre_archivo=nombre_archivo,
        ruta_archivo=ruta_archivo,
        tipo_archivo=tipo_archivo,
        tamaño_archivo=tamaño_archivo,
        usuario_subida_id=usuario_id
    )
    
    db.add(db_documento)
    db.commit()
    db.refresh(db_documento)
    
    return db_documento


def delete_documento_orden(db: Session, documento_id: int) -> bool:
    """Eliminar documento de orden"""
    db_documento = db.query(DocumentosOrden).filter(DocumentosOrden.id == documento_id).first()
    if not db_documento:
        return False
    
    db.delete(db_documento)
    db.commit()
    return True


# === FUNCIONES ESPECIALES ===

def confirmar_llegada_repuestos(db: Session, orden_id: int, llegada: ConfirmarLlegadaRequest) -> Optional[OrdenesCompra]:
    """Confirmar llegada de repuestos y actualizar inventario"""
    orden = get_orden_compra(db, orden_id)
    if not orden:
        return None
    
    if orden.estado != 'confirmado':
        raise ValueError("Solo se puede confirmar llegada de órdenes en estado 'confirmado'")  
    
    try:
        # Actualizar cantidades recibidas y agregar al inventario
        print(f"Procesando {len(llegada.items_recibidos)} items recibidos para orden {orden_id}")
        
        for item_recibido in llegada.items_recibidos:
            # Manejar tanto dict como object
            if isinstance(item_recibido, dict):
                item_id = item_recibido.get('item_id')
                cantidad_recibida = item_recibido.get('cantidad_recibida', 0)
            else:
                item_id = getattr(item_recibido, 'item_id', None)
                cantidad_recibida = getattr(item_recibido, 'cantidad_recibida', 0)
            
            print(f"Procesando item {item_id} con cantidad {cantidad_recibida}")
            
            # Actualizar item de la orden
            db_item = db.query(ItemsOrdenCompra).filter(ItemsOrdenCompra.id == item_id).first()
            if not db_item:
                print(f"WARNING: Item {item_id} no encontrado en la orden")
                continue
            
            print(f"Item encontrado: {db_item.id}, es_manual: {db_item.es_item_manual}, repuesto_id: {db_item.repuesto_id}")
            try:
                print(f"  --> Descripción aduana: {db_item.descripcion_aduana}")
                print(f"  --> Cantidad pedida: {db_item.cantidad_pedida}")
            except Exception as e:
                print(f"  --> ERROR al acceder a propiedades del item: {e}")
            if db_item.es_item_manual:
                print(f"  --> Datos manuales - Código: {db_item.codigo_manual}, Nombre: {db_item.nombre_manual}")
                print(f"  --> Detalle manual: {db_item.detalle_manual}")
                print(f"  --> Cantidad mínima manual: {db_item.cantidad_minima_manual}")
            db_item.cantidad_recibida = cantidad_recibida
            
            if cantidad_recibida > 0:
                if db_item.es_item_manual:
                    # Para items manuales, crear nuevo repuesto o buscar existente por código
                    if not db_item.codigo_manual or not db_item.nombre_manual:
                        print(f"ERROR: Item manual {item_id} no tiene código ({db_item.codigo_manual}) o nombre ({db_item.nombre_manual})")
                        continue
                    
                    repuesto_existente = None
                    if db_item.codigo_manual:
                        repuesto_existente = db.query(Repuestos).filter(
                            Repuestos.codigo == db_item.codigo_manual
                        ).first()
                    
                    if repuesto_existente:
                        # Actualizar repuesto existente
                        repuesto_existente.cantidad += cantidad_recibida
                        print(f"Agregando {cantidad_recibida} unidades al repuesto existente {repuesto_existente.codigo}")
                    else:
                        # Crear nuevo repuesto desde item manual
                        print(f"Creando nuevo repuesto: código={db_item.codigo_manual}, nombre={db_item.nombre_manual}")
                        nuevo_repuesto = Repuestos(
                            codigo=db_item.codigo_manual,
                            nombre=db_item.nombre_manual,
                            detalle=db_item.detalle_manual or '',
                            cantidad=cantidad_recibida,
                            cantidad_minima=db_item.cantidad_minima_manual,
                            proveedor_id=orden.proveedor_id,
                            descripcion_aduana=db_item.descripcion_aduana  # Guardar descripción de aduana
                        )
                        print(f"ANTES DE db.add() - Repuesto: {nuevo_repuesto.codigo}")
                        db.add(nuevo_repuesto)
                        print(f"DESPUÉS DE db.add() - Antes de flush()")
                        db.flush()  # Para obtener el ID
                        print(f"DESPUÉS DE flush() - Nuevo repuesto ID: {nuevo_repuesto.id}")
                        
                        # Vincular el item con el nuevo repuesto
                        db_item.repuesto_id = nuevo_repuesto.id
                        print(f"CREADO Y VINCULADO repuesto ID:{nuevo_repuesto.id}, Código:{nuevo_repuesto.codigo} con {cantidad_recibida} unidades")
                        
                elif db_item.repuesto_id:
                    # Para items con repuesto existente
                    repuesto = db.query(Repuestos).filter(Repuestos.id == db_item.repuesto_id).first()
                    if repuesto:
                        repuesto.cantidad += cantidad_recibida
                        print(f"Agregando {cantidad_recibida} unidades al repuesto {repuesto.codigo}")
                    else:
                        print(f"WARNING: Repuesto con ID {db_item.repuesto_id} no encontrado")
                else:
                    # Item sin repuesto_id y no manual - crear repuesto automáticamente
                    print(f"WARNING: Item {item_id} no tiene repuesto_id ni es manual - creando repuesto automático")
                    
                    # Generar código único basado en timestamp y orden
                    import time
                    codigo_generado = f"AUTO-{orden_id}-{item_id}-{int(time.time())}"
                    
                    # Usar descripción aduana si existe, sino crear nombre genérico
                    nombre_repuesto = f"Item de orden {orden_id}"
                    detalle_repuesto = f"Creado automáticamente desde orden {orden_id}, item {item_id}"
                    
                    if hasattr(db_item, 'descripcion_aduana') and db_item.descripcion_aduana:
                        nombre_repuesto = db_item.descripcion_aduana
                        detalle_repuesto += f" - Descripción: {db_item.descripcion_aduana}"
                        print(f"  --> Usando descripción aduana: {db_item.descripcion_aduana}")
                    else:
                        print(f"  --> Sin descripción aduana, usando nombre genérico")
                    
                    # Crear nuevo repuesto
                    nuevo_repuesto = Repuestos(
                        codigo=codigo_generado,
                        nombre=nombre_repuesto,
                        detalle=detalle_repuesto,
                        cantidad=cantidad_recibida,
                        proveedor_id=orden.proveedor_id,
                        descripcion_aduana=db_item.descripcion_aduana  # Guardar descripción de aduana
                    )
                    print(f"ANTES DE db.add() - Repuesto automático: {nuevo_repuesto.codigo}")
                    db.add(nuevo_repuesto)
                    print(f"DESPUÉS DE db.add() - Antes de flush() automático")
                    db.flush()  # Para obtener el ID
                    print(f"DESPUÉS DE flush() - Nuevo repuesto automático ID: {nuevo_repuesto.id}")
                    
                    # Vincular el item con el nuevo repuesto
                    db_item.repuesto_id = nuevo_repuesto.id
                    print(f"CREADO repuesto automático ID:{nuevo_repuesto.id}, Código:{nuevo_repuesto.codigo}, Nombre:{nuevo_repuesto.nombre} con {cantidad_recibida} unidades")
        
        # Cambiar estado de la orden a completado
        orden.estado = 'completado'
        
        print(f"ANTES DEL COMMIT - Orden {orden_id} estado: {orden.estado}")
        db.commit()
        db.refresh(orden)
        print(f"DESPUÉS DEL COMMIT - Orden {orden_id} completada exitosamente")
        
        # Verificar repuestos después del commit
        print("=== VERIFICACIÓN FINAL DE REPUESTOS ===")
        total_repuestos = db.query(Repuestos).count()
        print(f"Total de repuestos después de confirmar llegada: {total_repuestos}")
        
        return get_orden_compra(db, orden_id)
        
    except Exception as e:
        db.rollback()
        print(f"ERROR en confirmar_llegada_repuestos: {e}")
        raise e


def reset_orden_estado(db: Session, orden_id: int, nuevo_estado: str) -> Optional[OrdenesCompra]:
    """Función temporal para resetear el estado de una orden para pruebas"""
    orden = db.query(OrdenesCompra).filter(OrdenesCompra.id == orden_id).first()
    if orden:
        orden.estado = nuevo_estado
        db.commit()
        db.refresh(orden)
        print(f"Orden {orden_id} cambiada a estado: {nuevo_estado}")
    return orden


def get_estadisticas_ordenes(db: Session) -> dict:
    """Obtener estadísticas de órdenes de compra"""
    total = db.query(OrdenesCompra).count()
    borradores = db.query(OrdenesCompra).filter(OrdenesCompra.estado == 'borrador').count()
    cotizados = db.query(OrdenesCompra).filter(OrdenesCompra.estado == 'cotizado').count()
    confirmados = db.query(OrdenesCompra).filter(OrdenesCompra.estado == 'confirmado').count()
    completados = db.query(OrdenesCompra).filter(OrdenesCompra.estado == 'completado').count()
    
    return {
        'total': total,
        'borradores': borradores,
        'cotizados': cotizados,
        'confirmados': confirmados,
        'completados': completados
    }


# === FUNCIONES PRIVADAS ===

def _validar_cambio_estado(estado_actual: str, nuevo_estado: str) -> bool:
    """Validar que el cambio de estado es válido"""
    transiciones_validas = {
        'borrador': ['cotizado'],
        'cotizado': ['confirmado'],
        'confirmado': ['completado'],
        'completado': []  # No se puede cambiar desde completado
    }
    
    return nuevo_estado in transiciones_validas.get(estado_actual, [])