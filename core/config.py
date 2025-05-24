"""
Configuración central para el asistente Mark.
Carga variables de entorno y proporciona configuración global.
"""
import os
import logging
import json # Necesario para el manejo del JSON en el validador
from typing import Dict, List, Any, Optional # Eliminado Set
from pydantic import validator, ValidationError, BaseSettings # Cambiado field_validator a validator y BaseSettings importada desde pydantic
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (primero)
load_dotenv()

# Configurar logger
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"), # Aún puede venir de .env o sistema
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mark-assistant")

# Clase base para configuración con Pydantic (mejor manejo y validación)
class Settings(BaseSettings):
    # General App Settings
    APP_NAME: str = "Mark Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development" # 'development' o 'production'
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ADMIN_PORT: int = 8001 # Puerto para el panel admin

    # Secret Key (Render inyecta esta automáticamente, o defínela en .env)
    # Usada para sesiones, firmas JWT, etc.
    SECRET_KEY: str # ¡Obligatoria! No poner valor por defecto aquí.

    # JWT Settings (usando SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 horas

    # Encryption Settings
    ENCRYPTION_KEY: str # ¡Obligatoria! Clave principal para derivación
    ENCRYPTION_SALT: str # ¡Obligatoria! Salt único para derivación

    # Admin Panel Credentials (Obsoleto)
    ADMIN_USERNAME: Optional[str] = None 
    ADMIN_PASSWORD_HASH: Optional[str] = None 

    # WhatsApp / Meta
    WHATSAPP_VERIFY_TOKEN: str # ¡Obligatoria!
    WHATSAPP_ACCESS_TOKEN: str # ¡Obligatoria!
    WHATSAPP_PHONE_NUMBER_ID: str # ¡Obligatoria!
    WHATSAPP_APP_SECRET: Optional[str] = None # Opcional pero recomendada

    # OpenRouter / AI Model
    OPENROUTER_API_KEY: str # ¡Obligatoria!
    OPENROUTER_MODEL: str # ¡Obligatoria! Modelo a usar (ej: "google/gemma-2-9b-it")
    OPENROUTER_TIMEOUT: float = 60.0 # Timeout para llamadas a la API
    OPENROUTER_HTTP_REFERER: Optional[str] = None # Opcional: URL de tu sitio

    # Stripe
    STRIPE_API_KEY: str # ¡Obligatoria!
    STRIPE_WEBHOOK_SECRET: str # ¡Obligatoria!
    STRIPE_PRICE_ID_STANDARD: str # ¡Obligatoria!
    STRIPE_PRICE_ID_REDUCIDA: str # ¡Obligatoria!
    STRIPE_PRICE_ID_PAREJA: str # ¡Obligatoria!
    STRIPE_PRICE_ID_CANCELLATION: str # ¡Obligatoria! ID de precio para cargos por cancelación
    STRIPE_LINK_SUCCESS: str # ¡Obligatoria! URL de redirección tras pago exitoso
    STRIPE_LINK_CANCEL: str # ¡Obligatoria! URL de redirección tras pago cancelado

    # Supabase / Database
    SUPABASE_URL: str # ¡Obligatoria!
    SUPABASE_KEY: str # ¡Obligatoria! (Anon key)
    SUPABASE_SERVICE_KEY: str # ¡Obligatoria! (Service role key)
    DATABASE_URL: Optional[str] = None

    # Calendly
    CALENDLY_API_KEY: Optional[str] = None
    CALENDLY_USER_URI: Optional[str] = None
    CALENDLY_WEBHOOK_URL: Optional[str] = None

    # Zoom (Server-to-Server OAuth)
    ZOOM_ACCOUNT_ID: Optional[str] = None
    ZOOM_S2S_CLIENT_ID: Optional[str] = None
    ZOOM_S2S_CLIENT_SECRET: Optional[str] = None

    # Contacto Emergencia
    EMERGENCY_CONTACT: Optional[str] = None # Número WhatsApp para notificaciones

    # Info Centro (para Admin Panel, etc.)
    CENTER_NAME: str = "Centro de Psicologia Jaume I"
    CENTER_ADDRESS: str = "Gran Via Jaume I, 41-43, Entresol 1a, 17001, Girona, España"
    CENTER_EMAIL: str = "info@centrepsicologiajaumeprimer.com"
    CENTER_WEBSITE: str = "https://centrepsicologiajaume1.com"

    # Language Settings
    # Usamos Any temporalmente y un validador para manejar el parseo de JSON desde env
    SUPPORTED_LANGUAGES: Any = ["es", "ca", "en", "ar"] # Default si falla la validación
    DEFAULT_LANGUAGE: str = "es"
    LANGUAGE_NAMES: Dict[str, str] = {
        "es": "Español",
        "ca": "Català",
        "en": "English",
        "ar": "العربية"
    }

    # Validador para SUPPORTED_LANGUAGES para intentar parsear desde env como JSON
    @validator('SUPPORTED_LANGUAGES', pre=True, always=True)
    @classmethod
    def parse_supported_languages(cls, v: Any) -> List[str]:
        default_languages = ["es", "ca", "en", "ar"] # Valor predeterminado explícito
        if isinstance(v, list): # Si ya es una lista (del default o código), usarla
            # Validar que los elementos sean strings
            if all(isinstance(lang, str) for lang in v):
                return v
            else:
                logger.warning(f"Valor de SUPPORTED_LANGUAGES (lista) contiene elementos no string. Usando default: {default_languages}")
                return default_languages
        if isinstance(v, str):
            try:
                # Intentar parsear como JSON
                parsed_list = json.loads(v)
                # Verificar que el resultado sea una lista de strings
                if isinstance(parsed_list, list) and all(isinstance(lang, str) for lang in parsed_list):
                    logger.info(f"SUPPORTED_LANGUAGES cargado desde variable de entorno: {parsed_list}")
                    return parsed_list
                else:
                     logger.warning(f"Valor de SUPPORTED_LANGUAGES ('{v}') no es una lista JSON de strings. Usando default: {default_languages}")
                     return default_languages
            except json.JSONDecodeError:
                # Si falla el parseo JSON, intentar split por coma como fallback (si tiene sentido)
                langs_from_split = [lang.strip() for lang in v.split(',') if lang.strip()]
                if langs_from_split:
                     logger.warning(f"No se pudo parsear SUPPORTED_LANGUAGES ('{v}') como JSON. Interpretado como CSV: {langs_from_split}. Considera usar formato JSON '[\"es\", \"ca\"]'.")
                     return langs_from_split
                else:
                     logger.warning(f"No se pudo parsear SUPPORTED_LANGUAGES ('{v}') como JSON ni CSV. Usando default: {default_languages}")
                     return default_languages
        # Si no es string ni lista, o es None/vacío, usar default
        if v is not None and v != '': # Solo loguear si había un valor inesperado
            logger.warning(f"Tipo inesperado o valor vacío para SUPPORTED_LANGUAGES ('{v}', tipo: {type(v)}). Usando default: {default_languages}")
        return default_languages

    # Pydantic model config
    class Config:
        env_file = '.env' # Carga desde .env si existe
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignorar variables extra del entorno

# Instanciar la configuración global
# Pydantic leerá las variables de entorno y .env al crear la instancia
try:
    settings = Settings()
    # Configurar Stripe globalmente después de cargar settings
    if settings.STRIPE_API_KEY:
        import stripe
        stripe.api_key = settings.STRIPE_API_KEY
        logger.info("API key de Stripe configurada correctamente.")
    else:
        logger.warning("STRIPE_API_KEY no encontrada en la configuración.")

except ValidationError as e:
    # Captura errores de validación específicos de Pydantic
    logger.error(f"Errores de validación al cargar la configuración: {e}")
    # Mostrar detalles de errores de validación
    for error in e.errors():
         logger.error(f"  Campo: {'.'.join(map(str,error['loc'])) if error['loc'] else 'N/A'}, Error: {error['msg']}")
    raise SystemExit(f"Errores de validación en configuración. Revisa los logs.")
except Exception as e:
     # Error grave si falta una variable requerida sin default o error inesperado
     logger.exception(f"Error fatal al cargar la configuración: {e}")
     raise SystemExit(f"Error de configuración: {e}")


# Función de verificación (ahora usa el objeto 'settings')
def verify_config() -> Dict[str, List[str]]:
    """
    Verifica la configuración cargada en 'settings' para advertencias.
    Las variables requeridas ya son validadas por Pydantic al instanciar Settings.

    Returns:
        Diccionario con advertencias encontradas.
    """
    warnings = []

    # Advertencias sobre opcionales recomendados
    if not settings.WHATSAPP_APP_SECRET:
        warnings.append("WHATSAPP_APP_SECRET no está configurado (recomendado para verificar webhooks).")
    if not settings.CALENDLY_API_KEY:
        warnings.append("CALENDLY_API_KEY no está configurado (funcionalidad de Calendly limitada).")
    if not settings.EMERGENCY_CONTACT:
         warnings.append("EMERGENCY_CONTACT no está configurado (no se enviarán notificaciones de pago).")

    # Verificar si SUPPORTED_LANGUAGES tiene elementos
    if not settings.SUPPORTED_LANGUAGES:
         warnings.append("SUPPORTED_LANGUAGES está vacío. Se usará el default ['es'] implícitamente en algunas funciones, pero debería definirse.")
    # Verificar si DEFAULT_LANGUAGE está en SUPPORTED_LANGUAGES
    elif settings.DEFAULT_LANGUAGE not in settings.SUPPORTED_LANGUAGES:
         warnings.append(f"DEFAULT_LANGUAGE ('{settings.DEFAULT_LANGUAGE}') no está incluido en SUPPORTED_LANGUAGES ({settings.SUPPORTED_LANGUAGES}).")

    return {"warnings": warnings}

# Ejecutar verificación al importar el módulo (opcional)
config_warnings = verify_config()
if config_warnings["warnings"]:
    logger.warning("Problemas encontrados en la configuración:")
    for warning in config_warnings["warnings"]:
        logger.warning(f"- {warning}")

def get_language_name(language_code: str) -> str:
    return settings.LANGUAGE_NAMES.get(language_code, language_code)

# Eliminar clases antiguas (ApiConfig, AdminConfig, LanguageConfig) ya que todo está en Settings
# ... (código de clases antiguas eliminado) ...
