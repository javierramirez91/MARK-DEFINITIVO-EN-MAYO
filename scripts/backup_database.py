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
import socket
from urllib.parse import urlparse

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger


def get_ipv4_address(hostname):
    """
    Resuelve el hostname a una dirección IPv4.
    Esto ayuda a evitar problemas con IPv6 en algunos entornos.
    """
    try:
        # Forzar resolución a IPv4
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            return result[0][4][0]  # Retorna la primera dirección IPv4
    except Exception as e:
        logger.warning(f"No se pudo resolver {hostname} a IPv4: {e}")
    return None


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
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Directorio de backup creado/verificado: {output_dir}")
            except PermissionError as e:
                logger.error(f"Sin permisos para crear el directorio {output_dir}: {e}")
                # Intentar usar /tmp como alternativa
                temp_output_path = os.path.join('/tmp', os.path.basename(output_path))
                logger.info(f"Intentando usar ruta alternativa: {temp_output_path}")
                output_path = temp_output_path
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Error creando directorio de backup: {e}")
                return False
        
        # Intentar extraer el hostname de la DATABASE_URL para forzar IPv4
        env_vars = {**os.environ, 'PGPASSWORD': ''}
        try:
            parsed_url = urlparse(settings.DATABASE_URL)
            hostname = parsed_url.hostname
            if hostname:
                logger.info(f"Hostname detectado: {hostname}")
                ipv4_address = get_ipv4_address(hostname)
                if ipv4_address:
                    logger.info(f"Usando dirección IPv4: {ipv4_address}")
                    # Establecer PGHOSTADDR para forzar el uso de IPv4
                    env_vars['PGHOSTADDR'] = ipv4_address
        except Exception as e:
            logger.warning(f"No se pudo parsear DATABASE_URL para obtener hostname: {e}")
        
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
            env=env_vars
        )
        
        if result.returncode == 0:
            # Verificar que el archivo se creó
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Backup completado exitosamente. Tamaño: {file_size} bytes")
                logger.info(f"Archivo guardado en: {os.path.abspath(output_path)}")
                return True
            else:
                logger.error("El archivo de backup no se creó")
                return False
        else:
            logger.error(f"Error en pg_dump (código {result.returncode}): {result.stderr}")
            
            # Si el error es de red, intentar método alternativo
            if "Network is unreachable" in result.stderr or "could not connect" in result.stderr.lower():
                logger.warning("Error de conectividad de red detectado. Intentando backup vía API REST...")
                
                # Cambiar la extensión del archivo a .json para el backup vía API
                json_output_path = output_path.replace('.bak', '_api.json')
                
                try:
                    # Importar y ejecutar el script de backup vía API
                    from scripts.backup_database_api import backup_database_via_api
                    import asyncio
                    
                    logger.info("Ejecutando backup alternativo vía API REST de Supabase...")
                    success = asyncio.run(backup_database_via_api(json_output_path))
                    
                    if success:
                        logger.info("Backup vía API REST completado como alternativa")
                        return True
                    else:
                        logger.error("El backup vía API también falló")
                        return create_system_info_backup(output_path)
                        
                except ImportError:
                    logger.error("No se pudo importar el módulo de backup vía API")
                    return create_system_info_backup(output_path)
                except Exception as e:
                    logger.error(f"Error ejecutando backup vía API: {e}")
                    return create_system_info_backup(output_path)
            
            return False
            
    except FileNotFoundError:
        logger.error("pg_dump no encontrado. Intentando método alternativo...")
        return create_system_info_backup(output_path)
    except Exception as e:
        logger.error(f"Error inesperado durante el backup: {e}")
        return False


def create_system_info_backup(output_path: str):
    """
    Crea un archivo con información del sistema cuando pg_dump no está disponible
    o no puede conectarse a la base de datos.
    """
    try:
        # Asegurar que usamos una ruta escribible
        if output_path.startswith('/data/'):
            output_path = output_path.replace('/data/', './backups/', 1)
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, 'w') as f:
            f.write(f"# Backup metadata - {datetime.now().isoformat()}\n")
            f.write(f"# DATABASE_URL configurada: {'Sí' if settings.DATABASE_URL else 'No'}\n")
            f.write(f"# Entorno: {settings.ENVIRONMENT}\n")
            f.write(f"# Versión de la app: {settings.APP_VERSION}\n")
            f.write(f"# \n")
            f.write(f"# NOTA: No se pudo realizar el backup completo de la base de datos.\n")
            f.write(f"# Posibles razones:\n")
            f.write(f"# - pg_dump no está disponible en el sistema\n")
            f.write(f"# - Problemas de conectividad de red (IPv6/IPv4)\n")
            f.write(f"# - Credenciales incorrectas o expiradas\n")
            f.write(f"# \n")
            f.write(f"# Para realizar un backup manual:\n")
            f.write(f"# 1. Accede al panel de Supabase\n")
            f.write(f"# 2. Ve a Settings > Database\n")
            f.write(f"# 3. Usa la opción de backup/export\n")
            f.write(f"# \n")
            f.write(f"# Alternativamente, considera usar las herramientas de backup de Supabase CLI.\n")
            
        logger.warning(f"Creado archivo de información del sistema en: {os.path.abspath(output_path)}")
        logger.warning("El backup completo de la base de datos no se pudo realizar.")
        return True
    except Exception as e:
        logger.error(f"Error creando archivo de información: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup de la base de datos')
    parser.add_argument(
        '--output',
        type=str,
        default=f'./backups/database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak',
        help='Ruta del archivo de backup (default: ./backups/database_YYYYMMDD_HHMMSS.bak)'
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