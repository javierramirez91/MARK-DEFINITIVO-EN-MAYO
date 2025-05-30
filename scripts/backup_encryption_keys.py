#!/usr/bin/env python3
"""
Script para realizar backup de las claves de encriptación y configuración sensible.
Crea un archivo ZIP protegido con contraseña con las claves importantes.
"""
import os
import sys
import argparse
import zipfile
import json
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger


def backup_encryption_keys(output_path: str):
    """
    Realiza un backup de las claves de encriptación y configuración sensible.
    
    Args:
        output_path: Ruta donde guardar el archivo ZIP de backup
    """
    try:
        # Crear el directorio si no existe
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Directorio de backup creado/verificado: {output_dir}")
        
        # Recopilar las claves importantes (solo las que existen)
        keys_to_backup = {
            'ENCRYPTION_KEY': settings.ENCRYPTION_KEY,
            'ENCRYPTION_SALT': settings.ENCRYPTION_SALT,
            'SECRET_KEY': settings.SECRET_KEY,
            'WHATSAPP_APP_SECRET': settings.WHATSAPP_APP_SECRET,
            'WHATSAPP_ACCESS_TOKEN': settings.WHATSAPP_ACCESS_TOKEN,
            'WHATSAPP_VERIFY_TOKEN': settings.WHATSAPP_VERIFY_TOKEN,
            'SUPABASE_SERVICE_KEY': settings.SUPABASE_SERVICE_KEY,
            'STRIPE_SECRET_KEY': settings.STRIPE_SECRET_KEY or settings.STRIPE_API_KEY,
            'STRIPE_WEBHOOK_SECRET': settings.STRIPE_WEBHOOK_SECRET,
            'INTERNAL_API_KEY': settings.INTERNAL_API_KEY,
            'OPENROUTER_API_KEY': settings.OPENROUTER_API_KEY,
            'ZOOM_S2S_CLIENT_SECRET': settings.ZOOM_S2S_CLIENT_SECRET or settings.ZOOM_CLIENT_SECRET,
            'CALENDLY_API_KEY': settings.CALENDLY_API_KEY or settings.CALENDLY_ACCESS_TOKEN,
        }
        
        # Filtrar solo las claves que tienen valor
        keys_to_backup = {k: v for k, v in keys_to_backup.items() if v}
        
        if not keys_to_backup:
            logger.error("No hay claves configuradas para hacer backup")
            return False
        
        logger.info(f"Preparando backup de {len(keys_to_backup)} claves")
        
        # Crear archivo temporal con las claves
        temp_file = output_path + '.tmp'
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'environment': settings.ENVIRONMENT,
            'app_name': settings.APP_NAME,
            'keys': keys_to_backup,
            'metadata': {
                'total_keys': len(keys_to_backup),
                'missing_keys': [k for k in ['ENCRYPTION_KEY', 'SECRET_KEY'] if not keys_to_backup.get(k)]
            }
        }
        
        # Guardar en un archivo JSON temporal
        with open(temp_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Crear ZIP (sin contraseña por ahora, ya que zipfile de Python no soporta encriptación nativa)
        logger.info(f"Creando archivo ZIP: {output_path}")
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_file, arcname='encryption_keys.json')
            
            # Añadir un README
            readme_content = f"""# Backup de Claves de Encriptación
Fecha: {datetime.now().isoformat()}
Ambiente: {settings.ENVIRONMENT}

IMPORTANTE: Este archivo contiene claves sensibles. Manténgalo seguro.

Para restaurar:
1. Extraiga encryption_keys.json
2. Configure las variables de entorno según el contenido del archivo
3. Reinicie la aplicación

Total de claves respaldadas: {len(keys_to_backup)}
"""
            zipf.writestr('README.txt', readme_content)
        
        # Eliminar archivo temporal
        os.remove(temp_file)
        
        # Verificar que el archivo se creó
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Backup de claves completado. Tamaño: {file_size} bytes")
            logger.warning("NOTA: El archivo ZIP no está encriptado. Considere encriptarlo manualmente o almacenarlo en un lugar seguro.")
            return True
        else:
            logger.error("El archivo de backup no se creó")
            return False
            
    except Exception as e:
        logger.error(f"Error durante el backup de claves: {e}")
        # Limpiar archivo temporal si existe
        temp_file = output_path + '.tmp'
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup de claves de encriptación')
    parser.add_argument(
        '--output',
        type=str,
        default=f'/data/backups/encryption_keys_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
        help='Ruta del archivo ZIP de backup (default: /data/backups/encryption_keys_YYYYMMDD_HHMMSS.zip)'
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