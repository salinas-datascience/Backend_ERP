#!/usr/bin/env python3
"""
Script para crear páginas usando la API REST del backend
"""

import requests
import json
import sys

# Configuración
API_BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {
    "username": "admin",  # Cambiar si es necesario
    "password": "admin123"  # Cambiar si es necesario
}

def get_auth_token():
    """Obtiene el token de autenticación del admin"""
    login_url = f"{API_BASE_URL}/auth/login"
    
    # Preparar datos para login
    login_data = {
        "username": ADMIN_CREDENTIALS["username"],
        "password": ADMIN_CREDENTIALS["password"]
    }
    
    try:
        response = requests.post(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"❌ Error al autenticar: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def create_page(token, page_data):
    """Crea una página usando la API"""
    url = f"{API_BASE_URL}/admin/paginas"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=page_data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error al crear página '{page_data['titulo']}': {response.status_code}")
            if response.status_code == 400:
                error_detail = response.json().get("detail", "Error desconocido")
                print(f"   Detalle: {error_detail}")
            return None
            
    except Exception as e:
        print(f"❌ Error al crear página '{page_data['titulo']}': {e}")
        return None

def get_existing_pages(token):
    """Obtiene las páginas existentes"""
    url = f"{API_BASE_URL}/admin/paginas"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error al obtener páginas: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error al obtener páginas: {e}")
        return []

def main():
    """Función principal"""
    print("🚀 Creador de Páginas del Sistema ERP via API")
    print("=" * 50)
    
    # Obtener token de autenticación
    print("🔐 Autenticando...")
    token = get_auth_token()
    if not token:
        print("❌ No se pudo autenticar. Verifica las credenciales.")
        sys.exit(1)
    
    print("✅ Autenticación exitosa!")
    
    # Verificar páginas existentes
    print("\n📋 Verificando páginas existentes...")
    existing_pages = get_existing_pages(token)
    existing_names = [page["nombre"] for page in existing_pages]
    existing_routes = [page["ruta"] for page in existing_pages]
    
    print(f"Páginas existentes: {len(existing_pages)}")
    
    # Definir páginas del sistema
    paginas_sistema = [
        {
            "nombre": "repuestos",
            "ruta": "/repuestos",
            "titulo": "Gestión de Repuestos",
            "descripcion": "Administrar inventario de repuestos y componentes",
            "icono": "Package",
            "orden": 1,
            "activa": True,
            "solo_admin": False
        },
        {
            "nombre": "proveedores",
            "ruta": "/proveedores",
            "titulo": "Gestión de Proveedores", 
            "descripcion": "Administrar proveedores y contactos",
            "icono": "Users",
            "orden": 2,
            "activa": True,
            "solo_admin": False
        },
        {
            "nombre": "maquinas",
            "ruta": "/maquinas",
            "titulo": "Gestión de Máquinas",
            "descripcion": "Administrar máquinas y equipos",
            "icono": "Settings",
            "orden": 3,
            "activa": True,
            "solo_admin": False
        },
        {
            "nombre": "modelos_maquinas",
            "ruta": "/modelos-maquinas",
            "titulo": "Modelos de Máquinas",
            "descripcion": "Administrar modelos y tipos de máquinas",
            "icono": "Cpu",
            "orden": 4,
            "activa": True,
            "solo_admin": False
        },
        {
            "nombre": "historial",
            "ruta": "/historial",
            "titulo": "Historial del Sistema",
            "descripcion": "Ver historial de movimientos y cambios",
            "icono": "History",
            "orden": 5,
            "activa": True,
            "solo_admin": False
        },
        # Páginas administrativas
        {
            "nombre": "admin_dashboard",
            "ruta": "/admin",
            "titulo": "Panel de Administración",
            "descripcion": "Dashboard principal de administración",
            "icono": "Shield",
            "orden": 10,
            "activa": True,
            "solo_admin": True
        },
        {
            "nombre": "admin_usuarios",
            "ruta": "/admin/usuarios",
            "titulo": "Gestión de Usuarios",
            "descripcion": "Administrar usuarios del sistema",
            "icono": "Users",
            "orden": 11,
            "activa": True,
            "solo_admin": True
        },
        {
            "nombre": "admin_roles",
            "ruta": "/admin/roles",
            "titulo": "Gestión de Roles",
            "descripcion": "Administrar roles del sistema",
            "icono": "Shield",
            "orden": 12,
            "activa": True,
            "solo_admin": True
        },
        {
            "nombre": "admin_permisos",
            "ruta": "/admin/permisos",
            "titulo": "Gestión de Permisos",
            "descripcion": "Administrar permisos granulares",
            "icono": "Key",
            "orden": 13,
            "activa": True,
            "solo_admin": True
        }
    ]
    
    # Crear páginas
    print("\n🏗️ Creando páginas...")
    created_count = 0
    skipped_count = 0
    
    for page_data in paginas_sistema:
        # Verificar si ya existe
        if page_data["nombre"] in existing_names or page_data["ruta"] in existing_routes:
            print(f"⏭️  Saltando '{page_data['titulo']}' (ya existe)")
            skipped_count += 1
            continue
        
        # Crear página
        result = create_page(token, page_data)
        if result:
            print(f"✅ Creada: {page_data['titulo']}")
            created_count += 1
        else:
            print(f"❌ Error creando: {page_data['titulo']}")
    
    # Mostrar resumen final
    print(f"\n🎉 Proceso completado:")
    print(f"   - Páginas creadas: {created_count}")
    print(f"   - Páginas saltadas: {skipped_count}")
    
    # Obtener estado final
    final_pages = get_existing_pages(token)
    print(f"   - Total páginas en sistema: {len(final_pages)}")
    
    # Mostrar páginas por categoría
    if final_pages:
        system_pages = [p for p in final_pages if not p["solo_admin"]]
        admin_pages = [p for p in final_pages if p["solo_admin"]]
        
        print(f"\n📋 Páginas del Sistema ({len(system_pages)}):")
        for page in sorted(system_pages, key=lambda x: x["orden"]):
            print(f"   - {page['titulo']} ({page['ruta']})")
        
        print(f"\n🔐 Páginas Administrativas ({len(admin_pages)}):")
        for page in sorted(admin_pages, key=lambda x: x["orden"]):
            print(f"   - {page['titulo']} ({page['ruta']})")
    
    print(f"\n✅ ¡Páginas inicializadas! Ahora puedes asignar páginas a usuarios desde /admin/usuarios")

if __name__ == "__main__":
    main()