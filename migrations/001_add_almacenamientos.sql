-- Migration 001: Agregar tabla de almacenamientos y actualizar repuestos
-- Fecha: 2025-08-21

BEGIN;

-- Crear tabla de almacenamientos
CREATE TABLE IF NOT EXISTS almacenamientos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR UNIQUE NOT NULL,
    nombre VARCHAR NOT NULL,
    descripcion TEXT,
    ubicacion_fisica VARCHAR,
    activo INTEGER DEFAULT 1
);

-- Agregar índices para almacenamientos
CREATE INDEX IF NOT EXISTS idx_almacenamientos_codigo ON almacenamientos(codigo);
CREATE INDEX IF NOT EXISTS idx_almacenamientos_activo ON almacenamientos(activo);

-- Agregar columna almacenamiento_id a repuestos
ALTER TABLE repuestos 
ADD COLUMN IF NOT EXISTS almacenamiento_id INTEGER REFERENCES almacenamientos(id);

-- Crear índice para la nueva foreign key
CREATE INDEX IF NOT EXISTS idx_repuestos_almacenamiento_id ON repuestos(almacenamiento_id);

-- Insertar datos de ejemplo de almacenamientos
INSERT INTO almacenamientos (codigo, nombre, descripcion, ubicacion_fisica, activo)
VALUES 
    ('A1-E1', 'Estante A1', 'Estante principal para componentes pequeños', 'Planta 1 - Zona A - Estante 1', 1),
    ('A1-E2', 'Estante A2', 'Estante para componentes medianos', 'Planta 1 - Zona A - Estante 2', 1),
    ('B1-E1', 'Estante B1', 'Estante para componentes electrónicos', 'Planta 1 - Zona B - Estante 1', 1),
    ('C1-CAJ', 'Cajón C1', 'Cajón para herramientas y consumibles', 'Planta 1 - Zona C - Cajón 1', 1),
    ('DEP-FRI', 'Depósito Refrigerado', 'Depósito con temperatura controlada para componentes sensibles', 'Planta 1 - Depósito Principal', 1)
ON CONFLICT (codigo) DO NOTHING;

COMMIT;