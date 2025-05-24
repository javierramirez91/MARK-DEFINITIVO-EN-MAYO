import os
import asyncio
import logging
from dotenv import load_dotenv # Re-activar
from supabase import create_client, Client
from core.security_utils import pwd_context # Importar el contexto de hashing de la app

# Configurar un logger básico para el script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_or_reset_password():
    logger.info("Cargando variables de entorno desde .env...")
    load_dotenv() # Re-activar

    # Leer de os.environ de nuevo
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    # --- Eliminar valores hardcodeados ---
    # supabase_url = "https://vtfyydqigxiowkswgreu.supabase.co"
    # supabase_service_key = "eyJhbG...UhA" # Clave regenerada
    # --- Fin eliminación ---

    admin_username = "admin"  # Asumiendo que el username es 'admin'
    new_password = "changeme123" # CONTRASEÑA TEMPORAL
    admin_email = "admin@example.com" # Email por defecto para creación
    admin_roles = ["admin"] # Roles por defecto para creación

    if not supabase_url or not supabase_service_key:
        logger.error("Error: SUPABASE_URL o SUPABASE_SERVICE_KEY no encontradas en .env. Verifica el archivo.")
        return

    # Re-activar impresión de clave leída (opcional, pero útil)
    logger.info(f"Clave de servicio cargada (primeros 5 y últimos 5 caracteres): {supabase_service_key[:5]}...{supabase_service_key[-5:]}")

    logger.info(f"Asegurando existencia y contraseña para el usuario: '{admin_username}'")
    logger.info(f"Contraseña objetivo (temporal): '{new_password}'")

    try:
        # Hashear la nueva contraseña
        logger.info("Generando hash para la contraseña...")
        hashed_password = pwd_context.hash(new_password)
        logger.info("Hash de contraseña generado exitosamente.")

        # Conectar a Supabase usando la clave de servicio leída del env
        logger.info(f"Conectando a Supabase en {supabase_url}...")
        supabase: Client = create_client(supabase_url, supabase_service_key)
        logger.info("Conectado a Supabase con la clave de servicio.") # Mensaje restaurado

        # 1. Buscar si el usuario ya existe (usando "usuarios")
        logger.info(f"Buscando usuario '{admin_username}' en tabla 'usuarios'...")
        get_response = supabase.table("usuarios").select("id").eq("username", admin_username).limit(1).execute() # SIN await

        user_exists = bool(get_response.data)

        if user_exists:
            # 2a. Si existe, actualizar contraseña
            user_id = get_response.data[0]['id']
            logger.info(f"Usuario '{admin_username}' (ID: {user_id}) encontrado. Actualizando contraseña...")
            update_response = supabase.table("usuarios") \
                .update({
                    "hashed_password": hashed_password,
                }) \
                .eq("username", admin_username) \
                .execute() # SIN await
            response = update_response # Usar la respuesta de update para logs
        else:
            # 2b. Si no existe, crear usuario
            logger.info(f"Usuario '{admin_username}' no encontrado. Creando nuevo usuario...")
            # Asegúrate de que estos campos coincidan con tu tabla 'usuarios'
            # El ID uuid debería generarse automáticamente por Supabase si está configurado
            user_data_to_create = {
                "username": admin_username,
                "email": admin_email,
                "hashed_password": hashed_password,
                "roles": admin_roles,
                "is_active": True,
                "is_locked": False,
                # created_at y updated_at suelen manejarse automáticamente
            }
            create_response = supabase.table("usuarios").insert(user_data_to_create).execute() # SIN await
            response = create_response # Usar la respuesta de insert para logs

        # 3. Verificar la respuesta de la operación (update o insert)
        if response.data:
            if user_exists:
                logger.info(f"¡Contraseña actualizada exitosamente para el usuario '{admin_username}'!")
            else:
                new_user_id = response.data[0].get('id', 'N/A')
                logger.info(f"¡Usuario '{admin_username}' (ID: {new_user_id}) creado exitosamente!")

            logger.info(f"Ahora puedes iniciar sesión con:")
            logger.info(f"  Usuario: {admin_username}")
            logger.info(f"  Contraseña: {new_password}")
            logger.warning("¡IMPORTANTE! Cambia esta contraseña temporal inmediatamente después de iniciar sesión.")
        else:
            # Intentar obtener más detalles del error si están disponibles
            operation_type = "actualizar" if user_exists else "crear"
            error_message = "Respuesta inesperada o vacía."
            status_code = "N/A"
            if hasattr(response, 'status_code'):
                status_code = response.status_code
                if status_code == 404 and user_exists: # Error buscando al actualizar?
                     error_message = f"Usuario '{admin_username}' no encontrado al intentar actualizar (raro)."
                elif status_code == 409: # Conflicto, probablemente al insertar
                    error_message = f"Conflicto al crear usuario '{admin_username}'. ¿Ya existe (verificar constraint UNIQUE)?"
                elif status_code == 401:
                     error_message = f"No autorizado al {operation_type}. Verifica que SUPABASE_SERVICE_KEY sea correcta y tenga permisos."
                # Añadir otros códigos de error relevantes si es necesario
            if hasattr(response, 'error') and response.error:
                 error_message += f" Detalle API: {response.error.message} (Code: {response.error.code}, Hint: {response.error.hint})"

            logger.error(f"Error al {operation_type} el usuario (Status: {status_code}): {error_message}")
            logger.error(f"Respuesta completa de Supabase: {response}")


    except ImportError as ie:
        logger.error(f"Error de importación. Asegúrate de que 'passlib', 'supabase', 'python-dotenv' están instalados ({ie})")
    except Exception as e:
        logger.exception(f"Ocurrió un error inesperado durante el proceso: {e}")

if __name__ == "__main__":
    # Asegura que el event loop se maneje correctamente al ejecutar el script
    if os.name == 'nt': # Para Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_or_reset_password()) # Llamar a la función renombrada 