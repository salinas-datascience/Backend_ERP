# Etapa única - instalación directa
FROM python:3.9.23-slim

WORKDIR /app

# Instalar curl para healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root primero
RUN useradd -m fastapi

# Copiar y instalar dependencias directamente
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY ./app .
COPY init_user_system.py /app/init_user_system.py

# Dar permisos al usuario fastapi
RUN chown -R fastapi:fastapi /app
USER fastapi

EXPOSE 8000

# Comando para ejecutar con inicialización
CMD ["sh", "-c", "python init_user_system.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]