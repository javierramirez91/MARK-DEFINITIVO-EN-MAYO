"""
Script de instalación para el asistente virtual Mark
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    required_version = (3, 9)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Se requiere Python {required_version[0]}.{required_version[1]} o superior.")
        print(f"Versión actual: {current_version[0]}.{current_version[1]}.{current_version[2]}")
        sys.exit(1)
    
    print(f"✓ Versión de Python compatible: {current_version[0]}.{current_version[1]}.{current_version[2]}")

def create_virtual_env():
    """Crea un entorno virtual si no existe"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Entorno virtual ya existe")
        return
    
    print("Creando entorno virtual...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Entorno virtual creado correctamente")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el entorno virtual: {e}")
        sys.exit(1)

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print("Instalando dependencias...")
    
    # Determinar el ejecutable de pip según el sistema operativo
    if sys.platform == "win32":
        pip_path = Path("venv") / "Scripts" / "pip"
    else:
        pip_path = Path("venv") / "bin" / "pip"
    
    try:
        # Actualizar pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # Instalar dependencias
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar dependencias: {e}")
        sys.exit(1)

def setup_env_file():
    """Configura el archivo .env si no existe"""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if env_path.exists():
        print("✓ Archivo .env ya existe")
        return
    
    if not example_path.exists():
        print("Error: No se encontró el archivo .env.example")
        sys.exit(1)
    
    print("Creando archivo .env a partir de .env.example...")
    shutil.copy(example_path, env_path)
    print("✓ Archivo .env creado correctamente")
    print("⚠️ No olvides editar el archivo .env con tus claves API y configuraciones")

def create_database():
    """Crea la base de datos SQLite si no existe"""
    db_path = Path("mark.db")
    
    if db_path.exists():
        print("✓ Base de datos ya existe")
        return
    
    print("Creando base de datos SQLite...")
    try:
        # Importar SQLAlchemy y crear la base de datos
        from sqlalchemy import create_engine
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine("sqlite:///mark.db")
        Base = declarative_base()
        Base.metadata.create_all(engine)
        
        print("✓ Base de datos creada correctamente")
    except Exception as e:
        print(f"Error al crear la base de datos: {e}")
        print("⚠️ La base de datos se creará automáticamente al iniciar la aplicación")

def main():
    """Función principal de instalación"""
    print("=== Instalación del Asistente Virtual Mark ===")
    
    # Verificar versión de Python
    check_python_version()
    
    # Crear entorno virtual
    create_virtual_env()
    
    # Instalar dependencias
    install_dependencies()
    
    # Configurar archivo .env
    setup_env_file()
    
    # Crear base de datos
    create_database()
    
    print("\n=== Instalación completada ===")
    print("\nPara activar el entorno virtual:")
    if sys.platform == "win32":
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    
    print("\nPara iniciar la aplicación:")
    print("  python main.py")
    
    print("\n¡Gracias por instalar Mark! 🚀")

if __name__ == "__main__":
    main() 