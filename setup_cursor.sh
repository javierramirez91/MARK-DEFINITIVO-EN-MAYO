#!/bin/bash
# Script de configuración para el desarrollo en Cursor

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir encabezados
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Función para imprimir mensajes de éxito
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Función para imprimir advertencias
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Función para imprimir errores
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Detectar el sistema operativo
OS="$(uname)"
print_header "Configurando entorno para $OS"

# Verificar si Python 3.11+ está instalado
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
    print_error "Se requiere Python 3.11 o superior. Versión detectada: $python_version"
    exit 1
else
    print_success "Python $python_version detectado"
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    print_header "Creando entorno virtual..."
    python3 -m venv venv
    print_success "Entorno virtual creado"
else
    print_warning "El entorno virtual ya existe"
fi

# Activar entorno virtual
print_header "Activando entorno virtual..."
if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    source venv/bin/activate
elif [ "$OS" = "Windows_NT" ]; then
    source venv/Scripts/activate
else
    print_error "Sistema operativo no soportado: $OS"
    exit 1
fi
print_success "Entorno virtual activado"

# Instalar dependencias
print_header "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencias instaladas"

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    print_header "Creando archivo .env..."
    cp .env.example .env
    print_success "Archivo .env creado"
    print_warning "¡IMPORTANTE! Edita el archivo .env con tus propias claves API"
else
    print_warning "El archivo .env ya existe"
fi

# Crear base de datos SQLite local si no existe
if [ ! -f "local_database.db" ]; then
    print_header "Creando base de datos SQLite local..."
    python3 -c "
import sqlite3
from database.schema import schema
conn = sqlite3.connect('local_database.db')
conn.executescript(schema)
conn.close()
print('Base de datos creada exitosamente')
    "
    if [ $? -eq 0 ]; then
        print_success "Base de datos local creada"
    else
        print_error "Error al crear la base de datos local"
    fi
else
    print_warning "La base de datos local ya existe"
fi

# Configurar Git
print_header "Configurando Git..."
if [ ! -d ".git" ]; then
    git init
    print_success "Git inicializado"
else
    print_warning "Git ya está inicializado"
fi

# Configurar pre-commit hooks
if [ ! -f ".git/hooks/pre-commit" ]; then
    print_header "Configurando pre-commit hooks..."
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook para verificar errores básicos

# Verificar formato de código Python
echo "Verificando formato de código Python..."
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    if [ -f "$file" ]; then
        python -m autopep8 --exit-code "$file"
        if [ $? -ne 0 ]; then
            echo "Error de formato en $file"
            exit 1
        fi
    fi
done

# Verificar importaciones no utilizadas
echo "Verificando importaciones no utilizadas..."
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    if [ -f "$file" ]; then
        python -m pyflakes "$file"
        if [ $? -ne 0 ]; then
            echo "Importaciones no utilizadas en $file"
            exit 1
        fi
    fi
done

# Todos los checks pasaron
echo "Pre-commit checks pasados!"
exit 0
EOF
    chmod +x .git/hooks/pre-commit
    print_success "Pre-commit hooks configurados"
else
    print_warning "Pre-commit hooks ya configurados"
fi

# Instalar herramientas de desarrollo si no están ya
print_header "Instalando herramientas de desarrollo..."
pip install autopep8 pyflakes pytest
print_success "Herramientas de desarrollo instaladas"

# Mensaje final
print_header "Configuración completada"
echo -e "Para iniciar el servidor de desarrollo, ejecuta: ${GREEN}uvicorn main:app --reload${NC}"
echo -e "Para ejecutar pruebas, ejecuta: ${GREEN}pytest${NC}"
echo -e "Para obtener ayuda de IA en Cursor, presiona: ${GREEN}Ctrl+K / Cmd+K${NC}"
echo -e "\n${YELLOW}¡No olvides editar el archivo .env con tus propias claves API!${NC}\n" 