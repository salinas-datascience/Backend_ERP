-- Migración 002: Agregar sistema de usuarios, roles y permisos
-- Fecha: 2025-01-XX
-- Descripción: Crea las tablas para gestión de usuarios, autenticación y autorización

BEGIN;

-- Crear tabla de roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR UNIQUE NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de permisos
CREATE TABLE IF NOT EXISTS permisos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR UNIQUE NOT NULL,
    descripcion TEXT,
    recurso VARCHAR NOT NULL,
    accion VARCHAR NOT NULL,
    activo BOOLEAN DEFAULT true
);

-- Crear tabla de páginas
CREATE TABLE IF NOT EXISTS paginas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR UNIQUE NOT NULL,
    ruta VARCHAR UNIQUE NOT NULL,
    titulo VARCHAR NOT NULL,
    descripcion TEXT,
    icono VARCHAR,
    orden INTEGER DEFAULT 0,
    activa BOOLEAN DEFAULT true,
    solo_admin BOOLEAN DEFAULT false
);

-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    nombre_completo VARCHAR,
    activo BOOLEAN DEFAULT true,
    es_admin BOOLEAN DEFAULT false,
    rol_id INTEGER REFERENCES roles(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_conexion TIMESTAMP,
    debe_cambiar_password BOOLEAN DEFAULT true,
    fecha_cambio_password TIMESTAMP,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP
);

-- Crear tabla de asociación roles-permisos
CREATE TABLE IF NOT EXISTS roles_permisos (
    rol_id INTEGER REFERENCES roles(id),
    permiso_id INTEGER REFERENCES permisos(id),
    PRIMARY KEY (rol_id, permiso_id)
);

-- Crear tabla de asociación usuarios-páginas
CREATE TABLE IF NOT EXISTS usuarios_paginas (
    usuario_id INTEGER REFERENCES usuarios(id),
    pagina_id INTEGER REFERENCES paginas(id),
    PRIMARY KEY (usuario_id, pagina_id)
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX IF NOT EXISTS idx_paginas_ruta ON paginas(ruta);
CREATE INDEX IF NOT EXISTS idx_paginas_activa ON paginas(activa);
CREATE INDEX IF NOT EXISTS idx_roles_nombre ON roles(nombre);
CREATE INDEX IF NOT EXISTS idx_permisos_nombre ON permisos(nombre);

-- Insertar rol de administrador por defecto
INSERT INTO roles (nombre, descripcion, activo) 
VALUES ('Administrador', 'Rol con acceso completo al sistema', true)
ON CONFLICT (nombre) DO NOTHING;

-- Insertar permisos básicos
INSERT INTO permisos (nombre, descripcion, recurso, accion, activo) VALUES 
    ('usuarios_leer', 'Ver usuarios del sistema', 'usuarios', 'leer', true),
    ('usuarios_crear', 'Crear nuevos usuarios', 'usuarios', 'crear', true),
    ('usuarios_editar', 'Editar usuarios existentes', 'usuarios', 'editar', true),
    ('usuarios_eliminar', 'Eliminar/desactivar usuarios', 'usuarios', 'eliminar', true),
    ('repuestos_leer', 'Ver repuestos', 'repuestos', 'leer', true),
    ('repuestos_crear', 'Crear repuestos', 'repuestos', 'crear', true),
    ('repuestos_editar', 'Editar repuestos', 'repuestos', 'editar', true),
    ('repuestos_eliminar', 'Eliminar repuestos', 'repuestos', 'eliminar', true),
    ('maquinas_leer', 'Ver máquinas', 'maquinas', 'leer', true),
    ('maquinas_crear', 'Crear máquinas', 'maquinas', 'crear', true),
    ('maquinas_editar', 'Editar máquinas', 'maquinas', 'editar', true),
    ('maquinas_eliminar', 'Eliminar máquinas', 'maquinas', 'eliminar', true)
ON CONFLICT (nombre) DO NOTHING;

-- Insertar páginas básicas del sistema
INSERT INTO paginas (nombre, ruta, titulo, descripcion, icono, orden, activa, solo_admin) VALUES 
    ('repuestos', '/repuestos', 'Repuestos', 'Gestión de repuestos y inventario', 'package', 1, true, false),
    ('maquinas', '/maquinas', 'Máquinas', 'Gestión de máquinas SMT', 'cpu', 2, true, false),
    ('historial', '/historial', 'Historial', 'Historial de uso de repuestos', 'history', 3, true, false),
    ('proveedores', '/proveedores', 'Proveedores', 'Gestión de proveedores', 'truck', 4, true, false),
    ('modelos-maquinas', '/modelos-maquinas', 'Modelos de Máquinas', 'Gestión de modelos de máquinas', 'settings', 5, true, false),
    ('almacenamientos', '/almacenamientos', 'Almacenamientos', 'Gestión de ubicaciones de almacenamiento', 'warehouse', 6, true, false),
    ('usuarios', '/admin/usuarios', 'Usuarios', 'Gestión de usuarios del sistema', 'users', 7, true, true),
    ('roles', '/admin/roles', 'Roles y Permisos', 'Gestión de roles y permisos', 'shield', 8, true, true)
ON CONFLICT (nombre) DO NOTHING;

-- Asignar todos los permisos al rol de administrador
INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id 
FROM roles r, permisos p 
WHERE r.nombre = 'Administrador'
ON CONFLICT DO NOTHING;

-- Crear usuario administrador por defecto (contraseña: admin123)
-- Hash bcrypt para 'admin123': $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
INSERT INTO usuarios (username, email, hashed_password, nombre_completo, activo, es_admin, rol_id, debe_cambiar_password)
SELECT 'admin', 'admin@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Administrador del Sistema', true, true, r.id, true
FROM roles r 
WHERE r.nombre = 'Administrador'
ON CONFLICT (username) DO NOTHING;

COMMIT;