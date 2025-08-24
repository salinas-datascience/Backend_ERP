#!/usr/bin/env python3
"""
Script para probar el sistema de control de acceso por páginas
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio app al path
sys.path.insert(0, '/app')

from models.models import Usuarios, Paginas

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL no está configurada")
    sys.exit(1)

def test_page_access():
    """Prueba el sistema de control de acceso"""
    print("🧪 Testing Page Access Control System...")
    
    # Crear conexión
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Verificar que las páginas existan
        print("\n📋 1. Verificando páginas creadas...")
        paginas = db.query(Paginas).all()
        print(f"Total páginas: {len(paginas)}")
        
        for pagina in paginas:
            admin_only = " (Solo Admin)" if pagina.solo_admin else ""
            print(f"  - {pagina.titulo} ({pagina.ruta}){admin_only}")
        
        # 2. Verificar usuarios existentes
        print("\n👥 2. Verificando usuarios...")
        usuarios = db.query(Usuarios).all()
        print(f"Total usuarios: {len(usuarios)}")
        
        for usuario in usuarios:
            admin_status = " (ADMIN)" if usuario.es_admin else ""
            activo_status = " (ACTIVO)" if usuario.activo else " (INACTIVO)"
            print(f"  - {usuario.username}{admin_status}{activo_status}")
        
        # 3. Crear usuario de prueba si no existe
        print("\n🧪 3. Creando usuario de prueba...")
        test_user = db.query(Usuarios).filter(Usuarios.username == 'testuser').first()
        
        if not test_user:
            # Crear usuario de prueba
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            test_user = Usuarios(
                username='testuser',
                email='test@test.com',
                hashed_password=pwd_context.hash('test123'),
                nombre_completo='Usuario de Prueba',
                activo=True,
                es_admin=False,
                debe_cambiar_password=False
            )
            db.add(test_user)
            db.commit()
            print("✅ Usuario de prueba creado: testuser / test123")
        else:
            print("✅ Usuario de prueba ya existe")
        
        # 4. Asignar solo algunas páginas al usuario de prueba
        print("\n🔧 4. Configurando acceso restringido...")
        
        # Limpiar asignaciones existentes
        test_user.paginas_permitidas.clear()
        
        # Asignar solo repuestos e historial
        pagina_repuestos = db.query(Paginas).filter(Paginas.ruta == '/repuestos').first()
        pagina_historial = db.query(Paginas).filter(Paginas.ruta == '/historial').first()
        
        if pagina_repuestos:
            test_user.paginas_permitidas.append(pagina_repuestos)
            print(f"✅ Asignada: {pagina_repuestos.titulo}")
        
        if pagina_historial:
            test_user.paginas_permitidas.append(pagina_historial)
            print(f"✅ Asignada: {pagina_historial.titulo}")
        
        db.commit()
        
        # 5. Mostrar configuración final
        print("\n📋 5. Configuración de prueba:")
        print("="*50)
        print("USUARIO DE PRUEBA:")
        print(f"  Usuario: testuser")
        print(f"  Contraseña: test123")
        print(f"  Es Admin: {test_user.es_admin}")
        print(f"  Páginas permitidas:")
        
        for pagina in test_user.paginas_permitidas:
            print(f"    ✅ {pagina.titulo} ({pagina.ruta})")
        
        # Páginas NO permitidas
        paginas_no_permitidas = [p for p in paginas if p not in test_user.paginas_permitidas]
        print(f"  Páginas NO permitidas:")
        for pagina in paginas_no_permitidas:
            print(f"    ❌ {pagina.titulo} ({pagina.ruta})")
        
        print("\n🧪 PRUEBAS PARA REALIZAR:")
        print("="*50)
        print("1. Login con testuser/test123")
        print("2. Verificar que solo ve 'Repuestos' e 'Historial' en navegación")
        print("3. Intentar acceder a /proveedores directamente -> Debe bloquearlo")
        print("4. Intentar acceder a /maquinas directamente -> Debe bloquearlo")
        print("5. Intentar acceder a /admin directamente -> Debe bloquearlo")
        print("6. Acceder a /repuestos -> Debe permitirlo")
        print("7. Acceder a /historial -> Debe permitirlo")
        
        print("\n🔑 USUARIO ADMIN:")
        print("="*50)
        admin_user = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
        if admin_user:
            print(f"  Usuario: admin")
            print(f"  Contraseña: admin123 (cambiar en primer login)")
            print(f"  Es Admin: {admin_user.es_admin}")
            print(f"  Debe ver TODAS las páginas")
        
        print("\n✅ Sistema de control de acceso configurado y listo para pruebas!")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = test_page_access()
    if success:
        print("\n🎉 ¡Sistema listo para pruebas!")
        print("Frontend: http://localhost:5175")
        print("Backend: http://localhost:8000")
    else:
        print("\n❌ Hubo errores en la configuración")
        sys.exit(1)