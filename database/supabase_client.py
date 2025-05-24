import os
from dotenv import load_dotenv
from supabase import create_client
from postgrest.exceptions import APIError
import logging
import asyncio
from functools import wraps

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supabase_client")

# Cargar variables de entorno
load_dotenv()

# Decorador para reintentos asíncrono
def with_retry(max_retries=3, retry_delay=2, retry_errors=None):
    """
    Decorador asíncrono para reintentar operaciones en caso de errores específicos.

    Args:
        max_retries (int): Número máximo de reintentos
        retry_delay (int): Retraso inicial entre reintentos (se incrementa exponencialmente)
        retry_errors (list): Lista de clases de error que deben provocar un reintento
    """
    if retry_errors is None:
        # Errores por defecto que deberían provocar un reintento
        retry_errors = (APIError, ConnectionError, TimeoutError, OSError)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    # Esperar la ejecución de la función asíncrona
                    return await func(*args, **kwargs)
                except retry_errors as e:
                    last_error = e

                    # No reintentar si es un error 404 o 400 (probablemente un error de lógica)
                    if isinstance(e, APIError) and hasattr(e, 'code') and e.code in (404, 400):
                        logger.error(f"Error no recuperable (no se reintentará): {e}")
                        raise

                    # No reintentar si ya estamos en el último intento
                    if attempt == max_retries - 1:
                        logger.error(f"Error después de {max_retries} intentos: {e}")
                        raise

                    # Calcular tiempo de espera con backoff exponencial
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Error recuperable, reintentando ({attempt+1}/{max_retries}) en {wait_time} segundos: {e}")
                    # Usar asyncio.sleep para no bloquear el event loop
                    await asyncio.sleep(wait_time)

            # Este código no debería ejecutarse nunca, pero por si acaso
            if last_error:
                raise last_error
        return wrapper
    return decorator

class SupabaseClient:
    """
    Cliente asíncrono para interactuar con Supabase.

    Esta clase proporciona métodos asíncronos para conectar y operar con Supabase,
    tanto con la clave anónima (para operaciones de usuario normal) como
    con la clave de servicio (para operaciones administrativas).
    Utiliza el patrón Singleton para asegurar una única instancia.
    """

    _instance = None
    _initialized = False
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    async def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado, de forma asíncrona y segura."""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    load_dotenv()

                    self.is_production = os.getenv("ENVIRONMENT") == "production" or "RENDER" in os.environ
                    logger.info(f"Inicializando cliente Supabase en entorno: {'producción' if self.is_production else 'desarrollo'}")

                    self.supabase_url = os.getenv("SUPABASE_URL")
                    self.supabase_key = os.getenv("SUPABASE_KEY")
                    self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
                    self.project_id = os.getenv("SUPABASE_PROJECT_ID", "vtfyydqigxiowkswgreu")

                    # Verificar si las claves se cargaron correctamente
                    if not self.supabase_url:
                        logger.error("SUPABASE_URL no encontrada tras load_dotenv().")
                    if not self.supabase_key:
                        logger.error("SUPABASE_KEY no encontrada tras load_dotenv().")
                    # No lanzar error inmediatamente, esperar a la verificación completa

                    if not self.supabase_url or not self.supabase_key:
                        logger.error("Faltan credenciales de Supabase (URL o KEY anónima) en el entorno. Verifica el archivo .env y su carga.")
                        # Lanzar excepción aquí es crucial, ya que el cliente anónimo es esencial
                        raise ValueError("Faltan credenciales esenciales de Supabase (URL/KEY). Verifica el archivo .env y su carga.")

                    self.max_retries = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))
                    self.retry_delay = int(os.getenv("SUPABASE_RETRY_DELAY", "2"))

                    self.client = None
                    self.admin_client = None

                    # Crear el cliente anónimo
                    try:
                        self.client = create_client(self.supabase_url, self.supabase_key)
                        logger.info(f"Cliente Supabase anónimo creado para {self.supabase_url}")
                    except Exception as e:
                        logger.error(f"Error al crear el cliente Supabase anónimo: {e}")
                        # Podríamos querer lanzar el error aquí si el cliente anónimo es esencial
                        # raise

                    # Crear el cliente admin si la clave de servicio está disponible
                    if self.supabase_service_key:
                        try:
                            self.admin_client = create_client(self.supabase_url, self.supabase_service_key)
                            logger.info(f"Cliente Supabase de servicio creado para {self.supabase_url}")
                        except Exception as e:
                            logger.error(f"Error al crear el cliente Supabase de servicio: {e}")
                            # No lanzar error aquí, puede que solo necesitemos el anónimo
                    else:
                        logger.warning("SUPABASE_SERVICE_KEY no encontrada. El cliente admin no estará disponible.")

                    self.http_options = {}
                    if self.is_production:
                        self.http_options = {
                            "timeout": float(os.getenv("SUPABASE_TIMEOUT", "30")),
                        }
                        logger.info(f"Configuración HTTP para producción: {self.http_options}")

                    try:
                        await self._test_connection()
                    except Exception as e:
                        logger.warning(f"La verificación inicial de conexión falló: {e} (se reintentará en la primera operación)")

                    self._initialized = True
                    logger.info(f"Cliente Supabase inicializado para URL: {self.supabase_url}")

    def _mask_api_key(self, key):
        """Enmascara la API key para registro seguro."""
        if not key:
            return "[No disponible]"
        return key[:6] + "..." + key[-6:]

    async def _test_connection(self):
        """Prueba la conexión inicial a Supabase de forma asíncrona."""
        try:
            client_to_test = self.client
            if not client_to_test:
                logger.warning("Cliente anónimo no disponible para prueba de conexión.")
                if self.admin_client:
                    client_to_test = self.admin_client
                    logger.info("Intentando prueba de conexión con cliente admin.")
                else:
                    logger.error("No hay clientes disponibles para probar la conexión.")
                    return

            try:
                logger.info("Verificando la instancia del cliente Supabase...")
                assert client_to_test is not None
                logger.info("Instancia del cliente Supabase verificada.")
            except APIError as api_err:
                logger.warning(f"Prueba de conexión encontró un APIError (puede ser esperado si la tabla/rpc no existe o faltan permisos): {api_err}")
            except Exception as e:
                logger.error(f"La verificación de conexión falló con una excepción inesperada: {e}")
                raise

        except Exception as e:
            logger.error(f"Error durante _test_connection: {e}")
            raise

    async def connect(self, use_service_key=False):
        """
        Asegura que el cliente Supabase esté inicializado y devuelve el cliente apropiado (anónimo o admin).

        Args:
            use_service_key (bool): Si es True, devuelve el cliente de servicio.
                                   Por defecto es False (devuelve cliente anónimo).

        Returns:
            El cliente de Supabase apropiado (tipo inferido).

        Raises:
            ValueError: Si se solicita la clave de servicio y no está configurada.
            Exception: Si la inicialización falla.
        """
        await self._ensure_initialized()

        if use_service_key:
            if not self.admin_client:
                logger.error("Se solicitó cliente admin, pero no está inicializado (falta SUPABASE_SERVICE_KEY?).")
                raise ValueError("Clave de servicio de Supabase no disponible o no inicializada.")
            return self.admin_client
        else:
            if not self.client:
                logger.error("Se solicitó cliente anónimo, pero no está inicializado.")
                raise ValueError("Cliente anónimo de Supabase no inicializado.")
            return self.client

    @with_retry()
    async def query_table(self, table_name, query_fn=None, use_service_key=False, handle_error=True):
        """
        Realiza una consulta asíncrona en una tabla de Supabase.

        Args:
            table_name (str): Nombre de la tabla a consultar.
            query_fn (callable): Función asíncrona que recibe el objeto tabla y realiza la consulta.
                               Debe retornar el resultado de `await ...execute()`.
                               Si es None, seleccionará todos los registros ('*').
            use_service_key (bool): Si es True, usa la clave de servicio.
            handle_error (bool): Si es True, maneja los errores internamente y devuelve None.

        Returns:
            PostgrestAPIResponse | None: Resultado de la consulta o None si hay un error y handle_error es True.
        """
        try:
            client = await self.connect(use_service_key)
            table = client.table(table_name)

            if query_fn:
                if asyncio.iscoroutinefunction(query_fn):
                    result = await query_fn(table)
                else:
                    logger.warning("query_fn no es una corutina. Esperando una función async que llame a .execute()")
                    query_builder = query_fn(table)
                    if hasattr(query_builder, 'execute'):
                        result = query_builder.execute()
                    else:
                        raise TypeError("query_fn debe ser una función async que llame a .execute() o devolver un query builder")

            else:
                result = table.select("*").execute()

            if self.is_production and hasattr(result, 'data'):
                logger.info(f"Consulta async a tabla '{table_name}' completada: {len(result.data)} registros")

            return result
        except Exception as e:
            logger.error(f"Error al consultar async tabla '{table_name}': {e}")
            if handle_error:
                return None
            raise

    @with_retry()
    async def execute_rpc(self, function_name, params=None, use_service_key=False, handle_error=True):
        """
        Ejecuta una función RPC en Supabase de forma asíncrona.

        Args:
            function_name (str): Nombre de la función a ejecutar.
            params (dict): Parámetros para la función.
            use_service_key (bool): Si es True, usa la clave de servicio.
            handle_error (bool): Si es True, maneja los errores internamente y devuelve None.

        Returns:
            APIResponse | None: Resultado de la función RPC o None si hay error y handle_error es True.
        """
        try:
            client = await self.connect(use_service_key)

            if params is not None:
                result = await client.rpc(function_name, params).execute()
            else:
                result = await client.rpc(function_name, {}).execute()

            logger.debug(f"RPC async '{function_name}' ejecutada con éxito.")

            return result
        except Exception as e:
            logger.error(f"Error al ejecutar RPC async '{function_name}': {e}")
            if handle_error:
                return None
            raise

    @with_retry()
    async def get_table_names(self, schema="public", use_service_key=True):
        """
        Obtiene los nombres de las tablas en un esquema de forma asíncrona.
        Esto requiere permisos adecuados, usualmente la clave de servicio.

        Args:
            schema (str): Nombre del esquema (por defecto 'public').
            use_service_key (bool): Usar clave de servicio (recomendado).

        Returns:
            list[str] | None: Lista de nombres de tablas o None si hay error.
        """
        try:
            client = await self.connect(use_service_key)

            rpc_params = {'schema_name': schema}
            result = await client.rpc('list_tables_in_schema', rpc_params).execute()

            if hasattr(result, 'data') and isinstance(result.data, list):
                table_names = [item if isinstance(item, str) else item.get('table_name') for item in result.data]
                table_names = [name for name in table_names if name]
                logger.info(f"Tablas encontradas en esquema '{schema}': {len(table_names)}")
                return table_names
            else:
                logger.warning(f"No se pudieron obtener nombres de tabla del esquema '{schema}'. Respuesta: {result}")
                return None

        except Exception as e:
            logger.error(f"Error al obtener nombres de tabla async para esquema '{schema}': {e}")
            raise

    async def get_render_connection_info(self):
        """
        Obtiene información de conexión específica de Render (si aplica).
        Este método es un placeholder, necesita implementación real si se usa.
        Si llama a Supabase, debe ser async.
        """
        logger.warning("El método get_render_connection_info necesita implementación específica.")
        return {"status": "not_implemented"}

async def main_example():
    supabase_client = SupabaseClient()

    try:
        async def get_users(table):
            return await table.select("id, email").limit(10).execute()

        print("Consultando usuarios...")
        user_response = await supabase_client.query_table('users', query_fn=get_users)

        if user_response and hasattr(user_response, 'data'):
            print("Usuarios encontrados:", user_response.data)
        elif user_response:
            print("Respuesta de consulta recibida, pero sin datos:", user_response)
        else:
            print("Error al consultar usuarios.")

        print("\nEjecutando RPC 'hello_world'...")
        rpc_response = await supabase_client.execute_rpc('hello_world')

        if rpc_response and hasattr(rpc_response, 'data'):
            print("Respuesta RPC:", rpc_response.data)
        elif rpc_response:
            print("Respuesta RPC recibida, pero sin datos:", rpc_response)
        else:
            print("Error al ejecutar RPC.")

    except Exception as e:
        print(f"Ocurrió un error en el ejemplo: {e}")

if __name__ == "__main__":
    print("Ejecutando ejemplo asíncrono (esto normalmente no se ejecuta directamente aquí)...")
    asyncio.run(main_example())
    pass

# Ejemplo de uso:
if __name__ == "__main__":
    # Crear instancia del cliente
    supabase = SupabaseClient()
    
    try:
        # Conexión con clave anónima
        client = supabase.connect()
        print("Conexión exitosa con clave anónima")
        
        # Listar tablas disponibles
        tables = supabase.get_table_names()
        if tables:
            print(f"Tablas disponibles: {', '.join(tables)}")
        else:
            print("No se encontraron tablas o no se pudieron listar")
        
        # Ejemplo de consulta con una función personalizada
        try:
            # Intentar obtener un registro de alguna tabla disponible
            if tables:
                result = supabase.query_table(
                    tables[0],  # Primera tabla disponible
                    lambda table: table.select("*").limit(1),
                    use_service_key=True,
                    handle_error=False
                )
                print(f"Muestra de datos: {result.data if hasattr(result, 'data') else 'Sin datos'}")
        except Exception as e:
            print(f"Error al consultar datos: {e}")
        
        # Ejemplo con clave de servicio para operaciones administrativas
        admin_client = supabase.connect(use_service_key=True)
        print("Conexión exitosa con clave de servicio")
        
        # Ver información de conexión para Render
        render_info = supabase.get_render_connection_info()
        print(f"Info para Render: Proyecto {render_info['project_id']} en {render_info['supabase_url']}")
        
    except Exception as e:
        print(f"Error: {e}") 