#!/bin/bash

echo "🚀 Iniciando aplicación ERP Mantia..."

# Cambiar al directorio de la aplicación
cd /app

# Esperar a que la base de datos esté disponible
echo "⏳ Esperando conexión a la base de datos..."
for i in {1..30}; do
    if python -c "
import os
import sys
try:
    import psycopg2
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✅ Base de datos conectada')
    sys.exit(0)
except Exception as e:
    print(f'❌ Base de datos no disponible (intento {i}/30): {e}')
    sys.exit(1)
    "; then
        break
    fi
    sleep 3
    if [ $i -eq 30 ]; then
        echo "❌ No se pudo conectar a la base de datos después de 30 intentos"
        exit 1
    fi
done

# Crear un archivo Python temporal para la inicialización
cat > /tmp/init_db.py << 'EOF'
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.models import Usuarios, Roles
from passlib.context import CryptContext

try:
    print('📋 Creando tablas...')
    engine = create_engine(os.environ['DATABASE_URL'])
    Base.metadata.create_all(bind=engine)
    print('✅ Tablas creadas/verificadas')
    
    print('👤 Verificando usuario administrador...')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Verificar si ya existe el usuario admin
    admin_exists = db.query(Usuarios).filter(Usuarios.username == 'admin').first()
    
    if not admin_exists:
        print('🔨 Creando datos iniciales...')
        
        # Crear rol de administrador si no existe
        admin_role = db.query(Roles).filter(Roles.nombre == 'Administrador').first()
        if not admin_role:
            admin_role = Roles(
                nombre='Administrador',
                descripcion='Rol con acceso completo al sistema',
                activo=True
            )
            db.add(admin_role)
            db.flush()
        
        # Crear usuario admin
        pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        
        admin_user = Usuarios(
            username='admin',
            email='admin@empresa.com',
            hashed_password=pwd_context.hash('admin123'),
            nombre_completo='Administrador del Sistema',
            activo=True,
            es_admin=True,
            rol_id=admin_role.id,
            debe_cambiar_password=True
        )
        db.add(admin_user)
        db.commit()
        
        print('✅ Usuario administrador creado:')
        print('   Usuario: admin')
        print('   Contraseña: admin123')
        print('   ⚠️  IMPORTANTE: Cambiar contraseña en primer login')
    else:
        print('✅ Usuario administrador ya existe')
    
    db.close()
    print('🎉 Inicialización de base de datos completada')
    
except Exception as e:
    print(f'❌ Error al inicializar datos: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

# Ejecutar la inicialización
python /tmp/init_db.py

# Limpiar archivo temporal
rm -f /tmp/init_db.py

echo "🎉 Inicialización completada. Iniciando servidor..."

# Iniciar la aplicación
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload