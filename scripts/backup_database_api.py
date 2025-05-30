#!/usr/bin/env python3
"""
Script alternativo para realizar backup de la base de datos usando la API REST de Supabase.
Exporta las tablas principales a formato JSON cuando pg_dump no está disponible.
"""
import os
import sys
import argparse
import json
from datetime import datetime
import asyncio
from typing import List, Dict, Any

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger
from database.d1_client import get_supabase_client


# Tablas principales a respaldar
TABLES_TO_BACKUP = [
    'patients',
    'appointments', 
    'notifications',
    'payment_transactions',
    'sessions',
    'system_config',
    'webhook_logs'
]


async def export_table(table_name: str) -> Dict[str, Any]:
    """
    Exporta todos los registros de una tabla.
    
    Args:
        table_name: Nombre de la tabla a exportar
        
    Returns:
        Dict con los datos de la tabla y metadatos
    """
    try:
        logger.info(f"Exportando tabla: {table_name}")
        
        # Obtener cliente Supabase
        supabase = get_supabase_client()
        
        # Realizar consulta para obtener todos los registros
        # Nota: Para tablas muy grandes, considera usar paginación
        result = await asyncio.to_thread(
            lambda: supabase.table(table_name).select("*").execute()
        )
        
        if result.data is not None:
            record_count = len(result.data)
            logger.info(f"Tabla {table_name}: {record_count} registros exportados")
            
            return {
                'table_name': table_name,
                'record_count': record_count,
                'exported_at': datetime.now().isoformat(),
                'data': result.data
            }
        else:
            logger.warning(f"No se pudieron obtener datos de la tabla {table_name}")
            return {
                'table_name': table_name,
                'record_count': 0,
                'exported_at': datetime.now().isoformat(),
                'data': [],
                'error': 'No data returned'
            }
            
    except Exception as e:
        logger.error(f"Error exportando tabla {table_name}: {e}")
        return {
            'table_name': table_name,
            'record_count': 0,
            'exported_at': datetime.now().isoformat(),
            'data': [],
            'error': str(e)
        }


async def backup_database_via_api(output_path: str):
    """
    Realiza un backup de la base de datos usando la API REST de Supabase.
    
    Args:
        output_path: Ruta donde guardar el archivo de backup
    """
    try:
        logger.info("=== Iniciando backup de base de datos vía API REST ===")
        
        # Verificar que tenemos las credenciales de Supabase
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.error("SUPABASE_URL o SUPABASE_KEY no están configuradas")
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
        
        # Exportar cada tabla
        backup_data = {
            'backup_timestamp': datetime.now().isoformat(),
            'backup_type': 'supabase_api_export',
            'environment': settings.ENVIRONMENT,
            'app_version': settings.APP_VERSION,
            'tables': {}
        }
        
        total_records = 0
        successful_tables = 0
        
        for table_name in TABLES_TO_BACKUP:
            table_data = await export_table(table_name)
            backup_data['tables'][table_name] = table_data
            
            if table_data.get('error'):
                logger.warning(f"Tabla {table_name} exportada con errores")
            else:
                successful_tables += 1
                total_records += table_data['record_count']
        
        backup_data['summary'] = {
            'total_tables': len(TABLES_TO_BACKUP),
            'successful_tables': successful_tables,
            'total_records': total_records
        }
        
        # Guardar el archivo JSON
        logger.info(f"Guardando backup en: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
            
        # Verificar que el archivo se creó
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Backup completado exitosamente vía API REST")
            logger.info(f"Archivo guardado en: {os.path.abspath(output_path)}")
            logger.info(f"Tamaño del archivo: {file_size} bytes")
            logger.info(f"Tablas respaldadas: {successful_tables}/{len(TABLES_TO_BACKUP)}")
            logger.info(f"Total de registros: {total_records}")
            
            # Advertencia sobre el formato
            logger.warning("NOTA: Este es un backup en formato JSON, no es un dump SQL completo.")
            logger.warning("Para restaurar, será necesario procesar el JSON e insertar los datos.")
            
            return True
        else:
            logger.error("El archivo de backup no se creó")
            return False
            
    except Exception as e:
        logger.error(f"Error inesperado durante el backup vía API: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup de la base de datos vía API REST de Supabase')
    parser.add_argument(
        '--output',
        type=str,
        default=f'./backups/database_api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        help='Ruta del archivo de backup (default: ./backups/database_api_YYYYMMDD_HHMMSS.json)'
    )
    
    args = parser.parse_args()
    
    logger.info("=== Iniciando script de backup de base de datos vía API ===")
    
    # Ejecutar la función asíncrona
    success = asyncio.run(backup_database_via_api(args.output))
    
    if success:
        logger.info("=== Backup vía API completado exitosamente ===")
        sys.exit(0)
    else:
        logger.error("=== Backup vía API falló ===")
        sys.exit(1)


if __name__ == "__main__":
    main() 