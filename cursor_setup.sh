#!/bin/bash

# Script de configuración para el asistente virtual Mark en Cursor
echo "Iniciando configuración del entorno para el asistente virtual Mark..."

# Crear entorno virtual
echo "Creando entorno virtual..."
python -m venv venv

# Activar entorno virtual (Windows)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Activando entorno virtual (Windows)..."
    source venv/Scripts/activate
# Activar entorno virtual (Unix/Linux/MacOS)
else
    echo "Activando entorno virtual (Unix/Linux/MacOS)..."
    source venv/bin/activate
fi

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "Creando archivo .env con valores por defecto..."
    cat > .env << EOL
# Configuración general
DEBUG=True

# Claves API
CLAUDE_API_KEY=${CLAUDE_API_KEY:-"sk-ant-api03-..."}
CLOUDFLARE_API_TOKEN=
HUME_API_KEY=
HUME_CONFIG_ID=

# Base de datos
DATABASE_URL=
EOL
    echo "Archivo .env creado. Por favor, edita el archivo con tus propias claves API."
else
    echo "El archivo .env ya existe. No se ha modificado."
fi

# Crear directorios necesarios si no existen
echo "Verificando estructura de directorios..."
mkdir -p core ai/claude ai/hume ai/langsmith ai/langgraph ai/serper backend/services i18n database

echo "Configuración completada. Para iniciar el servidor de desarrollo, ejecuta:"
echo "uvicorn main:app --reload" 