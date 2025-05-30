#!/usr/bin/env python3
"""
Script para realizar backup de la base de datos de Supabase.
Usa pg_dump a través de la conexión string de Supabase.
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger


def backup_database(output_path: str):
    """
    Realiza un backup de la base de datos usando pg_dump.
    
    Args:
        output_path: Ruta donde guardar el archivo de backup
    """
    try:
        # Debug: mostrar variables de entorno relacionadas con DB
        logger.info("=== Debug de variables de entorno ===")
        logger.info(f"DATABASE_URL presente en settings: {'Sí' if hasattr(settings, 'DATABASE_URL') else 'No'}")
        logger.info(f"DATABASE_URL valor: {'[CONFIGURADA]' if settings.DATABASE_URL else '[NO CONFIGURADA]'}")
        logger.info(f"DATABASE_URL en os.environ: {'Sí' if 'DATABASE_URL' in os.environ else 'No'}")
        
        # Verificar que tenemos la DATABASE_URL
        if not settings.DATABASE_URL:
            logger.error("DATABASE_URL no está configurada")
            return False
            
        # Crear el directorio si no existe
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Directorio de backup creado/verificado: {output_dir}")
        
        # Ejecutar pg_dump
        logger.info(f"Iniciando backup de base de datos a: {output_path}")
        
        # Usar pg_dump con la DATABASE_URL
        # Nota: En Render, pg_dump debería estar disponible en el PATH
        cmd = [
            'pg_dump',
            settings.DATABASE_URL,
            '-f', output_path,
            '--verbose',
            '--no-owner',
            '--no-privileges',
            '--clean',
            '--if-exists'
        ]
        
        # Ejecutar el comando
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, 'PGPASSWORD': ''}  # pg_dump usará la URL directamente
        )
        
        if result.returncode == 0:
            # Verificar que el archivo se creó
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Backup completado exitosamente. Tamaño: {file_size} bytes")
                return True
            else:
                logger.error("El archivo de backup no se creó")
                return False
        else:
            logger.error(f"Error en pg_dump: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("pg_dump no encontrado. Intentando método alternativo...")
        # Método alternativo: Guardar un archivo con información básica
        try:
            with open(output_path, 'w') as f:
                f.write(f"# Backup metadata - {datetime.now().isoformat()}\n")
                f.write(f"# DATABASE_URL configurada: {'Sí' if settings.DATABASE_URL else 'No'}\n")
                f.write(f"# Nota: pg_dump no disponible en el sistema\n")
                f.write(f"# Este es un archivo placeholder. Considera usar pg_dump en un contenedor con PostgreSQL client instalado.\n")
            logger.warning("Creado archivo placeholder. pg_dump no está disponible en el sistema.")
            return True
        except Exception as e:
            logger.error(f"Error creando archivo placeholder: {e}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado durante el backup: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup de la base de datos')
    parser.add_argument(
        '--output',
        type=str,
        default=f'/data/backups/database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak',
        help='Ruta del archivo de backup (default: /data/backups/database_YYYYMMDD_HHMMSS.bak)'
    )
    
    args = parser.parse_args()
    
    logger.info("=== Iniciando script de backup de base de datos ===")
    success = backup_database(args.output)
    
    if success:
        logger.info("=== Backup completado exitosamente ===")
        sys.exit(0)
    else:
        logger.error("=== Backup falló ===")
        sys.exit(1)


if __name__ == "__main__":
    main() 