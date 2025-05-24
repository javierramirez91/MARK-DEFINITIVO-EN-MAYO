import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
import logging # Añadido para logs más claros

# Configurar logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection():
    logger.info("Cargando variables de entorno desde .env...")
    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") # USA LA SERVICE KEY

    if not supabase_url or not supabase_key:
        logger.error("Error: SUPABASE_URL o SUPABASE_SERVICE_KEY no encontradas en .env")
        return

    logger.info(f"Clave de servicio cargada (primeros 5 y últimos 5): {supabase_key[:5]}...{supabase_key[-5:]}")
    logger.info(f"Intentando conectar a {supabase_url} con clave SERVICE KEY...")


    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Cliente Supabase creado exitosamente.")

        logger.info("Intentando leer de public.usuarios (limit 1, count exact)...")
        # Intenta leer la tabla usuarios
        response = await supabase.table("usuarios").select("id", count='exact').limit(1).execute()

        logger.info("Respuesta recibida de Supabase.")
        # Imprimir la respuesta completa puede ser útil para depurar
        logger.info(f"Respuesta completa: {response}")

        # Verificar éxito basado en la estructura de la respuesta de Supabase
        if hasattr(response, 'data') and hasattr(response, 'count'):
             # Si tiene 'data' y 'count', la consulta probablemente tuvo éxito
             logger.info(f"ÉXITO: Se pudo leer de la tabla 'usuarios'. Número total de filas según 'count': {response.count}")
             if response.data:
                 logger.info(f"Primer ID encontrado en 'data': {response.data[0].get('id', 'N/A')}")
             else:
                 logger.info("La consulta tuvo éxito pero 'data' está vacía (la tabla podría estar vacía).")

        # Algunos casos de error podrían no lanzar una excepción pero devolver un error en la respuesta
        elif hasattr(response, 'error') and response.error:
             logger.error(f"Error en la respuesta de Supabase: {response.error}")
        else:
             # Si no lanza excepción y no tiene estructura esperada, es raro
             logger.warning("Advertencia: La consulta se ejecutó sin excepción, pero la respuesta no tiene el formato esperado (data/count).")


    except Exception as e:
        # Captura cualquier excepción, incluyendo APIError de postgrest
        logger.exception(f"ERROR DURANTE LA PRUEBA: {e}") # Usar logger.exception para incluir traceback

if __name__ == "__main__":
    # Manejo del event loop para Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_connection()) 