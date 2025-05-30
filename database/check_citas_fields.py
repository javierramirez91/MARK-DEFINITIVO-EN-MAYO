#!/usr/bin/env python3
"""
Script para verificar los campos de la tabla citas.
"""
import os
import sys
import asyncio

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger
from database.supabase_client import SupabaseClient


async def check_citas_structure():
    """Verifica la estructura de la tabla citas."""
    try:
        supabase = SupabaseClient()
        await supabase._ensure_initialized()
        
        # Obtener una cita de ejemplo para ver su estructura
        logger.info("Verificando estructura de la tabla 'citas'...")
        
        result = supabase.client.table('citas').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            cita = result.data[0]
            logger.info("\nCampos encontrados en la tabla 'citas':")
            for campo, valor in cita.items():
                tipo = type(valor).__name__ if valor is not None else "None"
                logger.info(f"- {campo}: {tipo} (ejemplo: {str(valor)[:50]}...)")
        else:
            logger.info("No hay citas en la tabla para examinar.")
            
            # Intentar obtener información de la estructura de otra forma
            # Crear una cita temporal para ver los campos
            logger.info("\nIntentando obtener estructura mediante insert vacío...")
            try:
                # Este insert fallará pero nos dará información sobre los campos requeridos
                test_result = supabase.client.table('citas').insert({}).execute()
            except Exception as insert_error:
                error_msg = str(insert_error)
                logger.info(f"\nError esperado del insert: {error_msg[:500]}")
                
    except Exception as e:
        logger.error(f"Error verificando estructura de citas: {e}")


if __name__ == "__main__":
    asyncio.run(check_citas_structure()) 