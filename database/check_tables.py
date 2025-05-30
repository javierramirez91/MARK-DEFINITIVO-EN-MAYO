#!/usr/bin/env python3
"""
Script para verificar las tablas existentes en la base de datos de Supabase.
"""
import os
import sys
import asyncio

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger
from database.supabase_client import SupabaseClient


async def check_tables():
    """Verifica qué tablas existen en la base de datos."""
    try:
        supabase = SupabaseClient()
        await supabase._ensure_initialized()
        
        # Query para obtener todas las tablas del schema public
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        # Ejecutar query usando RPC
        response = await supabase.rpc('check_tables', query)
        
        logger.info("Tablas encontradas en la base de datos:")
        for table in response.data:
            logger.info(f"- {table['table_name']}")
            
        return response.data
        
    except Exception as e:
        logger.error(f"Error verificando tablas: {e}")
        # Intentar método alternativo
        try:
            # Listar las tablas conocidas y verificar si existen
            known_tables = [
                'appointments',
                'pacientes', 
                'notifications',
                'usuarios',
                'sessions',
                'system_config',
                'webhook_logs',
                'payment_transactions'
            ]
            
            logger.info("\nVerificando tablas conocidas:")
            for table in known_tables:
                try:
                    result = supabase.client.table(table).select('id').limit(1).execute()
                    logger.info(f"✓ {table} - EXISTE")
                except Exception as table_error:
                    logger.error(f"✗ {table} - NO EXISTE o error: {str(table_error)[:100]}")
                    
        except Exception as alt_error:
            logger.error(f"Error en método alternativo: {alt_error}")


if __name__ == "__main__":
    asyncio.run(check_tables()) 