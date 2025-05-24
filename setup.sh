#!/bin/bash
# Script de configuración para el desarrollo del asistente Mark

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

# Verificar si Python 3.9+ está instalado
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]); then
    print_error "Se requiere Python 3.9 o superior. Versión detectada: $python_version"
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

# Crear base de datos SQLite si no existe
if [ ! -f "mark.db" ]; then
    print_header "Creando base de datos SQLite..."
    python3 -c "
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///mark.db')
Base = declarative_base()
Base.metadata.create_all(engine)
print('Base de datos creada exitosamente')
    "
    if [ $? -eq 0 ]; then
        print_success "Base de datos creada"
    else
        print_error "Error al crear la base de datos"
    fi
else
    print_warning "La base de datos ya existe"
fi

# Configurar Git
print_header "Configurando Git..."
if [ ! -d ".git" ]; then
    git init
    print_success "Git inicializado"
else
    print_warning "Git ya está inicializado"
fi

# Crear archivo .gitignore si no existe
if [ ! -f ".gitignore" ]; then
    print_header "Creando archivo .gitignore..."
    cat > .gitignore << 'EOF'
# Entorno virtual
venv/
env/
ENV/

# Archivos de configuración
.env
*.db
*.sqlite3

# Archivos de caché de Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Archivos de distribución
dist/
build/
*.egg-info/

# Archivos de sistema
.DS_Store
Thumbs.db

# Archivos de IDE
.idea/
.vscode/
*.swp
*.swo

# Archivos de log
*.log
logs/
EOF
    print_success "Archivo .gitignore creado"
else
    print_warning "El archivo .gitignore ya existe"
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
        python -m black --check "$file"
        if [ $? -ne 0 ]; then
            echo "Error de formato en $file"
            echo "Ejecuta 'black $file' para formatear el código"
            exit 1
        fi
    fi
done

# Verificar importaciones y errores con ruff
echo "Verificando código con ruff..."
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    if [ -f "$file" ]; then
        python -m ruff check "$file"
        if [ $? -ne 0 ]; then
            echo "Errores detectados en $file"
            exit 1
        fi
    fi
done

# Ejecutar pruebas unitarias
echo "Ejecutando pruebas unitarias..."
python -m pytest -xvs
if [ $? -ne 0 ]; then
    echo "Las pruebas unitarias fallaron"
    exit 1
fi

# Todos los checks pasaron
echo "Pre-commit checks pasados!"
exit 0
EOF
    chmod +x .git/hooks/pre-commit
    print_success "Pre-commit hooks configurados"
else
    print_warning "Pre-commit hooks ya configurados"
fi

# Crear estructura de directorios si no existe
print_header "Verificando estructura de directorios..."
directories=(
    "ai/claude"
    "ai/hume"
    "ai/langgraph"
    "ai/langsmith"
    "ai/serper"
    "api/endpoints"
    "api/middleware"
    "api/models"
    "core"
    "db/models"
    "db/repositories"
    "services"
    "utils"
    "tests"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Directorio $dir creado"
    else
        print_warning "Directorio $dir ya existe"
    fi
done

# Crear archivo __init__.py en cada directorio
print_header "Creando archivos __init__.py..."
for dir in "${directories[@]}"; do
    if [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
        print_success "Archivo $dir/__init__.py creado"
    else
        print_warning "Archivo $dir/__init__.py ya existe"
    fi
done

# Mensaje final
print_header "Configuración completada"
echo -e "Para iniciar el servidor de desarrollo, ejecuta: ${GREEN}python main.py${NC}"
echo -e "Para ejecutar pruebas, ejecuta: ${GREEN}pytest${NC}"
echo -e "Para formatear el código, ejecuta: ${GREEN}black .${NC}"
echo -e "Para verificar errores, ejecuta: ${GREEN}ruff check .${NC}"
echo -e "\n${YELLOW}¡No olvides editar el archivo .env con tus propias claves API!${NC}\n"
echo -e "${BLUE}Documentación disponible en README.md${NC}\n" 