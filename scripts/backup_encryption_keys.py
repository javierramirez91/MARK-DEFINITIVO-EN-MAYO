#!/usr/bin/env python3
"""
Script para realizar backup de las claves de encriptación y secretos del sistema.
Guarda las claves en un archivo JSON con permisos restrictivos.
"""
import os
import sys
import argparse
import json
from datetime import datetime
import stat

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger


def backup_encryption_keys(output_path: str):
    """
    Realiza un backup de todas las claves de encriptación y secretos importantes.
    
    Args:
        output_path: Ruta donde guardar el archivo de backup
    """
    try:
        logger.info("=== Iniciando backup de claves de encriptación ===")
        
        # Recopilar todas las claves importantes
        # Solo incluimos las que están configuradas (no None)
        keys_to_backup = {}
        
        # Claves críticas (obligatorias)
        if settings.SECRET_KEY:
            keys_to_backup['SECRET_KEY'] = settings.SECRET_KEY
        if settings.ENCRYPTION_KEY:
            keys_to_backup['ENCRYPTION_KEY'] = settings.ENCRYPTION_KEY
        if settings.ENCRYPTION_SALT:
            keys_to_backup['ENCRYPTION_SALT'] = settings.ENCRYPTION_SALT
            
        # API Keys de servicios externos
        if settings.WHATSAPP_VERIFY_TOKEN:
            keys_to_backup['WHATSAPP_VERIFY_TOKEN'] = settings.WHATSAPP_VERIFY_TOKEN
        if settings.WHATSAPP_ACCESS_TOKEN:
            keys_to_backup['WHATSAPP_ACCESS_TOKEN'] = settings.WHATSAPP_ACCESS_TOKEN
        if settings.WHATSAPP_APP_SECRET:
            keys_to_backup['WHATSAPP_APP_SECRET'] = settings.WHATSAPP_APP_SECRET
            
        if settings.OPENROUTER_API_KEY:
            keys_to_backup['OPENROUTER_API_KEY'] = settings.OPENROUTER_API_KEY
            
        if settings.STRIPE_API_KEY:
            keys_to_backup['STRIPE_API_KEY'] = settings.STRIPE_API_KEY
        if settings.STRIPE_WEBHOOK_SECRET:
            keys_to_backup['STRIPE_WEBHOOK_SECRET'] = settings.STRIPE_WEBHOOK_SECRET
            
        if settings.SUPABASE_URL:
            keys_to_backup['SUPABASE_URL'] = settings.SUPABASE_URL
        if settings.SUPABASE_KEY:
            keys_to_backup['SUPABASE_KEY'] = settings.SUPABASE_KEY
        if settings.SUPABASE_SERVICE_KEY:
            keys_to_backup['SUPABASE_SERVICE_KEY'] = settings.SUPABASE_SERVICE_KEY
        if settings.DATABASE_URL:
            keys_to_backup['DATABASE_URL'] = settings.DATABASE_URL
            
        if settings.CALENDLY_API_KEY:
            keys_to_backup['CALENDLY_API_KEY'] = settings.CALENDLY_API_KEY
            
        if settings.ZOOM_ACCOUNT_ID:
            keys_to_backup['ZOOM_ACCOUNT_ID'] = settings.ZOOM_ACCOUNT_ID
        if settings.ZOOM_S2S_CLIENT_ID:
            keys_to_backup['ZOOM_S2S_CLIENT_ID'] = settings.ZOOM_S2S_CLIENT_ID
        if settings.ZOOM_S2S_CLIENT_SECRET:
            keys_to_backup['ZOOM_S2S_CLIENT_SECRET'] = settings.ZOOM_S2S_CLIENT_SECRET
            
        if settings.INTERNAL_API_KEY:
            keys_to_backup['INTERNAL_API_KEY'] = settings.INTERNAL_API_KEY
            
        # Información adicional del backup
        backup_data = {
            'backup_timestamp': datetime.now().isoformat(),
            'environment': settings.ENVIRONMENT,
            'app_version': settings.APP_VERSION,
            'total_keys_backed_up': len(keys_to_backup),
            'keys': keys_to_backup
        }
        
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
        
        # Guardar el archivo JSON
        logger.info(f"Guardando backup de claves en: {output_path}")
        with open(output_path, 'w') as f:
            json.dump(backup_data, f, indent=2, sort_keys=True)
            
        # Establecer permisos restrictivos (solo lectura para el propietario)
        try:
            # En Windows, chmod tiene comportamiento limitado
            os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR)  # 600 en Unix
            logger.info("Permisos restrictivos establecidos en el archivo de backup")
        except Exception as e:
            logger.warning(f"No se pudieron establecer permisos restrictivos: {e}")
            
        # Verificar que el archivo se creó
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Backup completado exitosamente. Tamaño: {file_size} bytes")
            logger.info(f"Archivo guardado en: {os.path.abspath(output_path)}")
            logger.info(f"Total de claves respaldadas: {len(keys_to_backup)}")
            
            # Advertencia de seguridad
            logger.warning("¡ADVERTENCIA! Este archivo contiene información ALTAMENTE SENSIBLE.")
            logger.warning("Asegúrate de almacenarlo en un lugar seguro y eliminar copias no necesarias.")
            
            return True
        else:
            logger.error("El archivo de backup no se creó")
            return False
            
    except Exception as e:
        logger.error(f"Error inesperado durante el backup de claves: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup de claves de encriptación y secretos')
    parser.add_argument(
        '--output',
        type=str,
        default=f'./backups/encryption_keys_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        help='Ruta del archivo de backup (default: ./backups/encryption_keys_YYYYMMDD_HHMMSS.json)'
    )
    
    args = parser.parse_args()
    
    logger.info("=== Iniciando script de backup de claves de encriptación ===")
    success = backup_encryption_keys(args.output)
    
    if success:
        logger.info("=== Backup de claves completado exitosamente ===")
        sys.exit(0)
    else:
        logger.error("=== Backup de claves falló ===")
        sys.exit(1)


if __name__ == "__main__":
    main() 