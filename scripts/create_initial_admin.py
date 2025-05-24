import asyncio
import getpass
import logging
import os
import sys
from dotenv import load_dotenv
from passlib.context import CryptContext
# Importar cliente Supabase directamente
from supabase import create_client, Client
from postgrest.exceptions import APIError
from typing import Optional

# Añadir el directorio raíz del proyecto al sys.path para permitir importaciones absolutas
# Asumiendo que el script se ejecuta desde el directorio raíz del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Carga explícita de .env --- 
# Especificar ruta y forzar override para asegurar la carga
dotenv_path = os.path.join(project_root, '.env')
loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
if not loaded:
    print(f"ADVERTENCIA: No se pudo cargar el archivo .env desde {dotenv_path}")
    # Podrías decidir salir si .env es estrictamente necesario
    # sys.exit("Error: Archivo .env no encontrado o no se pudo cargar.")
else:
    print(f"Archivo .env cargado exitosamente desde {dotenv_path}")
# --------------------------------

# Configurar logging básico
log_level_from_env = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level_from_env, format='%(asctime)s - %(levelname)s - %(message)s')

# Verificar variables de Supabase necesarias
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_service_key:
    logging.error("Error: Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY en el entorno (.env).")
    sys.exit(1)

# Crear instancia local de CryptContext para este script
local_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    """Función principal asíncrona para crear el usuario admin (versión autónoma)."""
    logging.info("--- Creación de Usuario Administrador Inicial (Script Autónomo) ---")

    # Solicitar nombre de usuario
    default_username = "admin"
    username = input(f"Introduce el nombre de usuario para el admin (default: {default_username}): ") or default_username
    username = username.lower().strip() # Normalizar a minúsculas y quitar espacios

    if not username:
        logging.error("Error: El nombre de usuario no puede estar vacío.")
        return

    # Solicitar contraseña de forma segura
    while True:
        password = getpass.getpass(f"Introduce la contraseña para '{username}': ")
        if not password:
            logging.warning("La contraseña no puede estar vacía. Inténtalo de nuevo.")
            continue
        password_confirm = getpass.getpass("Confirma la contraseña: ")
        if password == password_confirm:
            break
        else:
            logging.warning("Las contraseñas no coinciden. Inténtalo de nuevo.")

    # Generar hash de la contraseña usando la instancia local
    try:
        logging.info("Generando hash seguro para la contraseña (instancia local)...")
        hashed_password = local_pwd_context.hash(password) # Usar local_pwd_context
        logging.info("Hash generado.")
    except Exception as e:
        logging.error(f"Error al generar el hash de la contraseña: {e}", exc_info=True)
        return

    # Preparar datos del usuario
    user_data = {
        "username": username,
        "hashed_password": hashed_password,
        "roles": ["admin"], # Asignar rol de administrador
        "is_active": True, # Activar por defecto
        # Puedes añadir email o full_name si lo deseas aquí o más tarde desde el panel
        # "email": "admin@example.com",
        # "full_name": "Administrador Principal"
    }

    # --- Interacción directa con Supabase --- 
    supabase_client: Optional[Client] = None
    try:
        logging.info(f"Creando cliente Supabase directo para: {supabase_url}")
        # Usar create_client (síncrono aquí, ya que el script principal es sync -> async)
        # ¡Importante! Usamos la clave de SERVICIO para crear usuarios
        supabase_client = create_client(supabase_url, supabase_service_key)
        logging.info("Cliente Supabase creado.")
        
        logging.info(f"Intentando insertar usuario '{username}'...")
        # Ejecutar la inserción directamente
        response = supabase_client.table("users").insert(user_data).execute()
        
        # Procesar respuesta
        if response.data:
             user_id = response.data[0].get("id", "ID no devuelto")
             logging.info(f"¡Éxito! Usuario administrador '{username}' (ID: {user_id}) creado correctamente.")
             logging.info("Ahora puedes iniciar el panel de administración y usar estas credenciales.")
        else:
            # Si no hay datos, puede haber un error o la inserción no devolvió datos
            logging.error(f"La inserción no devolvió datos. Respuesta completa: {response}")
            # Intentar obtener mensaje de error si existe (aunque no sea APIError)
            error_msg = getattr(response, 'message', 'Error desconocido sin mensaje específico') 
            logging.error(f"Error al crear el usuario: {error_msg}")
            # Comprobación específica de duplicidad si el mensaje lo indica
            if "duplicate key value violates unique constraint" in error_msg:
                 logging.warning(f"Parece que el usuario '{username}' ya existe en la base de datos.")

    except APIError as api_error:
        # Manejo específico de errores de la API de PostgREST
        logging.error(f"Error de API Supabase ({api_error.code}): {api_error.message}")
        if "duplicate key value violates unique constraint" in api_error.message:
            logging.warning(f"Parece que el usuario '{username}' ya existe en la base de datos.")
        # Aquí podrías manejar otros códigos de error específicos si fuera necesario
    except Exception as e:
        # Capturar otros errores inesperados (conexión, configuración, etc.)
        logging.error(f"Error inesperado durante la operación con Supabase: {e}", exc_info=True)
        
    # No necesitamos finally para cerrar cliente aquí, ya que no es una conexión persistente del singleton

if __name__ == "__main__":
    # Solo necesitamos verificar que las variables de Supabase existen
    if not supabase_url or not supabase_service_key:
        logging.error("No se puede continuar sin SUPABASE_URL y SUPABASE_SERVICE_KEY.")
        sys.exit(1)
        
    try:
        # Nota: main sigue siendo async, pero la llamada a Supabase ahora usa el cliente síncrono
        # dentro de la lógica de main. Podríamos hacer main síncrona también si fuera más simple.
        asyncio.run(main()) 
    except KeyboardInterrupt:
        logging.info("\nOperación cancelada por el usuario.")
    except Exception as e:
        logging.error(f"Error fatal ejecutando el script: {e}", exc_info=True) 