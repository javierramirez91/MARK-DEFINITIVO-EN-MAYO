"""
Módulo de acceso a la base de datos para el proyecto Mark Assistant.
Proporciona clases y utilidades para interactuar con Supabase y otros sistemas de base de datos.
"""

from database.supabase_client import SupabaseClient
from database.sqlalchemy_client import SupabaseAlchemyClient, Base

# Exportar clases para facilitar la importación
__all__ = ['SupabaseClient', 'SupabaseAlchemyClient', 'Base'] 