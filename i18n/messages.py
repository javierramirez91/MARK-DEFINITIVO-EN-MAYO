"""
Sistema de mensajes multilingües para el asistente Mark.
Proporciona funciones para cargar, validar y obtener mensajes en diferentes idiomas.
"""
import os
import json
import importlib
import logging
from typing import Dict, List, Any, Optional, Set
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.config import settings, logger

# Diccionario global para almacenar mensajes por idioma
# Formato: {idioma: {clave: mensaje}}
_MESSAGES: Dict[str, Dict[str, Any]] = {}

# Definir textos específicos para la notificación de Zoom aquí
# Esto es un workaround. Idealmente, estos deberían estar en los archivos i18n/{lang}.py
_ZOOM_NOTIFICATIONS = {
    "es": "Hola {name}, tu cita para el {date} a las {time} está confirmada. \nEnlace de Zoom: {link}",
    "ca": "Hola {name}, la teva cita pel {date} a les {time} està confirmada. \nEnllaç de Zoom: {link}",
    "en": "Hello {name}, your appointment for {date} at {time} is confirmed. \nZoom link: {link}",
    "ar": "مرحبًا {name}، تم تأكيد موعدك بتاريخ {date} الساعة {time}. \nرابط زوم: {link}"
}

def load_messages() -> None:
    """
    Carga los mensajes de todos los idiomas soportados
    """
    for lang_code in settings.SUPPORTED_LANGUAGES:
        try:
            # Intentar importar el módulo del idioma
            module_name = f"i18n.{lang_code}"
            module = importlib.import_module(module_name)
            
            # Verificar si el módulo tiene un diccionario MESSAGES
            if hasattr(module, "MESSAGES"):
                _MESSAGES[lang_code] = module.MESSAGES
                logger.info(f"Mensajes cargados para idioma: {lang_code}")
            else:
                logger.warning(f"El módulo {module_name} no contiene un diccionario MESSAGES")
        
        except ImportError:
            logger.warning(f"No se pudo importar el módulo para el idioma: {lang_code}")
        
        except Exception as e:
            logger.error(f"Error al cargar mensajes para {lang_code}: {e}")

def get_message(key: str, language: str = None) -> str:
    """
    Obtiene un mensaje en el idioma especificado
    
    Args:
        key: Clave del mensaje (puede usar notación de punto para acceder a mensajes anidados)
        language: Código de idioma (si es None, se usa el idioma por defecto)
        
    Returns:
        Mensaje en el idioma especificado o la clave si no se encuentra
    """
    # Si no se especifica idioma, usar el predeterminado
    target_language = language if language else settings.DEFAULT_LANGUAGE
    
    # Si el idioma no está soportado, usar el predeterminado
    if target_language not in settings.SUPPORTED_LANGUAGES:
        logger.warning(f"Idioma no soportado: {target_language}, usando {settings.DEFAULT_LANGUAGE}")
        target_language = settings.DEFAULT_LANGUAGE

    # ---- WORKAROUND para notificación de Zoom ----
    if key == "zoom_link_notification":
        return _ZOOM_NOTIFICATIONS.get(target_language, _ZOOM_NOTIFICATIONS[settings.DEFAULT_LANGUAGE])
    # ---- FIN WORKAROUND ----

    # Si los mensajes no están cargados, cargarlos
    if not _MESSAGES:
        load_messages()
    
    # Si el idioma no está cargado, intentar cargarlo
    if target_language not in _MESSAGES:
        try:
            module_name = f"i18n.{target_language}"
            module = importlib.import_module(module_name)
            if hasattr(module, "MESSAGES"):
                _MESSAGES[target_language] = module.MESSAGES
            else:
                logger.warning(f"El módulo {module_name} no contiene un diccionario MESSAGES")
                return key
        except Exception as e:
            logger.error(f"Error al cargar mensajes para {target_language}: {e}")
            return key
    
    # Obtener el mensaje usando notación de punto
    parts = key.split(".")
    current = _MESSAGES[target_language]
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            # Si no se encuentra el mensaje, intentar en el idioma predeterminado
            if target_language != settings.DEFAULT_LANGUAGE:
                default_lang_messages = _MESSAGES.get(settings.DEFAULT_LANGUAGE, {})
                fallback_current = default_lang_messages
                for fb_part in parts:
                    if isinstance(fallback_current, dict) and fb_part in fallback_current:
                        fallback_current = fallback_current[fb_part]
                    else:
                        return key # No encontrado ni en target ni en default
                current = fallback_current # Usar el valor del idioma por defecto
                # Romper el bucle for ya que encontramos el valor
                break 
            else:
                # Ya estamos en el idioma por defecto y no se encontró
                return key
    
    # Si el resultado no es un string, convertirlo a JSON
    if not isinstance(current, str):
        try:
             # Asegurar que los diccionarios/listas se devuelvan como JSON
             return json.dumps(current, ensure_ascii=False)
        except TypeError:
             # Si no se puede serializar, devolver representación string
             return str(current)
    
    return current

def update_message(key: str, value: Any, language: str) -> bool:
    """
    Actualiza un mensaje en el idioma especificado
    
    Args:
        key: Clave del mensaje (puede usar notación de punto para acceder a mensajes anidados)
        value: Nuevo valor para el mensaje
        language: Código de idioma
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    if language not in settings.SUPPORTED_LANGUAGES:
        logger.warning(f"Idioma no soportado: {language}")
        return False
    
    # Si los mensajes no están cargados, cargarlos
    if not _MESSAGES:
        load_messages()
    
    # Si el idioma no está cargado, intentar cargarlo
    if language not in _MESSAGES:
        try:
            module_name = f"i18n.{language}"
            module = importlib.import_module(module_name)
            if hasattr(module, "MESSAGES"):
                _MESSAGES[language] = module.MESSAGES
            else:
                logger.warning(f"El módulo {module_name} no contiene un diccionario MESSAGES")
                return False
        except Exception as e:
            logger.error(f"Error al cargar mensajes para {language}: {e}")
            return False
    
    # Actualizar el mensaje usando notación de punto
    parts = key.split(".")
    current = _MESSAGES[language]
    
    # Navegar hasta el penúltimo nivel
    for i, part in enumerate(parts[:-1]):
        if isinstance(current, dict):
            if part not in current:
                current[part] = {}
            current = current[part]
        else:
            logger.error(f"No se puede actualizar {key} en {language}: la ruta no es válida")
            return False
    
    # Actualizar el último nivel
    if isinstance(current, dict):
        current[parts[-1]] = value
        return True
    else:
        logger.error(f"No se puede actualizar {key} en {language}: la ruta no es válida")
        return False

def save_messages_to_json() -> Dict[str, Any]:
    """
    Guarda los mensajes de todos los idiomas en archivos JSON
    
    Returns:
        Diccionario con resultados de la operación
    """
    # Si los mensajes no están cargados, cargarlos
    if not _MESSAGES:
        load_messages()
    
    results = {
        "success": [],
        "error": []
    }
    
    # Crear directorio si no existe
    json_dir = os.path.join(os.path.dirname(__file__), "json")
    os.makedirs(json_dir, exist_ok=True)
    
    # Guardar cada idioma en un archivo JSON
    for lang_code, messages in _MESSAGES.items():
        try:
            file_path = os.path.join(json_dir, f"{lang_code}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            results["success"].append(lang_code)
        except Exception as e:
            logger.error(f"Error al guardar mensajes para {lang_code}: {e}")
            results["error"].append(f"{lang_code}: {str(e)}")
    
    return results

def load_messages_from_json() -> Dict[str, Any]:
    """
    Carga los mensajes desde archivos JSON
    
    Returns:
        Diccionario con resultados de la operación
    """
    results = {
        "success": [],
        "error": []
    }
    
    # Verificar si existe el directorio
    json_dir = os.path.join(os.path.dirname(__file__), "json")
    if not os.path.exists(json_dir):
        logger.warning(f"El directorio {json_dir} no existe")
        return results
    
    # Cargar cada archivo JSON
    for lang_code in settings.SUPPORTED_LANGUAGES:
        try:
            file_path = os.path.join(json_dir, f"{lang_code}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    _MESSAGES[lang_code] = json.load(f)
                results["success"].append(lang_code)
            else:
                logger.warning(f"No existe el archivo JSON para el idioma: {lang_code}")
        except Exception as e:
            logger.error(f"Error al cargar mensajes JSON para {lang_code}: {e}")
            results["error"].append(f"{lang_code}: {str(e)}")
    
    return results

def add_language(language_code: str, language_name: str) -> bool:
    """
    Añade un nuevo idioma al sistema
    
    Args:
        language_code: Código del nuevo idioma
        language_name: Nombre completo del idioma
        
    Returns:
        True si se añadió correctamente, False en caso contrario
    """
    if language_code in settings.SUPPORTED_LANGUAGES:
        logger.warning(f"El idioma {language_code} ya está soportado")
        return False
    
    try:
        # Añadir al diccionario de nombres de idiomas
        settings.LANGUAGE_NAMES[language_code] = language_name
        
        # Añadir a la lista de idiomas soportados
        settings.SUPPORTED_LANGUAGES.append(language_code)
        
        # Crear un diccionario vacío para los mensajes
        _MESSAGES[language_code] = {}
        
        logger.info(f"Idioma añadido: {language_code} ({language_name})")
        return True
    
    except Exception as e:
        logger.error(f"Error al añadir idioma {language_code}: {e}")
        return False

async def translate_missing_keys(
    source_language: str = None, 
    target_languages: List[str] = None,
    auto_update: bool = False
) -> Dict[str, Any]:
    """
    Traduce las claves que faltan en los idiomas de destino
    
    Args:
        source_language: Idioma fuente (si es None, se usa el idioma por defecto)
        target_languages: Lista de idiomas destino (si es None, se usan todos los soportados)
        auto_update: Si es True, actualiza automáticamente los mensajes
        
    Returns:
        Diccionario con resultados de la operación
    """
    # Si no se especifica idioma fuente, usar el predeterminado
    if source_language is None:
        source_language = settings.DEFAULT_LANGUAGE
    
    # Si no se especifican idiomas destino, usar todos los soportados excepto el fuente
    if target_languages is None:
        target_languages = [lang for lang in settings.SUPPORTED_LANGUAGES if lang != source_language]
    
    # Si los mensajes no están cargados, cargarlos
    if not _MESSAGES:
        load_messages()
    
    # Verificar que el idioma fuente esté cargado
    if source_language not in _MESSAGES:
        logger.error(f"El idioma fuente {source_language} no está cargado")
        return {"error": f"El idioma fuente {source_language} no está cargado"}
    
    results = {
        "translated": {},
        "errors": {}
    }
    
    # Obtener todas las claves del idioma fuente
    source_keys = get_all_keys(_MESSAGES[source_language])
    
    # Para cada idioma destino, traducir las claves que faltan
    for target_lang in target_languages:
        # Verificar que el idioma destino esté soportado
        if not settings.is_supported(target_lang):
            results["errors"][target_lang] = f"Idioma no soportado: {target_lang}"
            continue
        
        # Si el idioma destino no está cargado, intentar cargarlo
        if target_lang not in _MESSAGES:
            try:
                module_name = f"i18n.{target_lang}"
                module = importlib.import_module(module_name)
                if hasattr(module, "MESSAGES"):
                    _MESSAGES[target_lang] = module.MESSAGES
                else:
                    _MESSAGES[target_lang] = {}
            except Exception:
                _MESSAGES[target_lang] = {}
        
        # Obtener todas las claves del idioma destino
        target_keys = get_all_keys(_MESSAGES[target_lang])
        
        # Encontrar las claves que faltan en el idioma destino
        missing_keys = source_keys - target_keys
        
        if not missing_keys:
            results["translated"][target_lang] = []
            continue
        
        # Traducir las claves que faltan
        translated_keys = []
        translation_errors = []
        
        # Usar ThreadPoolExecutor para traducir en paralelo
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for key in missing_keys:
                futures.append(
                    executor.submit(
                        translate_key, 
                        key, 
                        source_language, 
                        target_lang, 
                        auto_update
                    )
                )
            
            for future in futures:
                try:
                    result = future.result()
                    if result["success"]:
                        translated_keys.append(result["key"])
                    else:
                        translation_errors.append(f"{result['key']}: {result['error']}")
                except Exception as e:
                    translation_errors.append(f"Error inesperado: {str(e)}")
        
        results["translated"][target_lang] = translated_keys
        if translation_errors:
            results["errors"][target_lang] = translation_errors
    
    return results

def translate_key(
    key: str, 
    source_language: str, 
    target_language: str, 
    auto_update: bool = False
) -> Dict[str, Any]:
    """
    Traduce una clave específica de un idioma a otro
    
    Args:
        key: Clave a traducir
        source_language: Idioma fuente
        target_language: Idioma destino
        auto_update: Si es True, actualiza automáticamente los mensajes
        
    Returns:
        Diccionario con resultado de la operación
    """
    try:
        # Obtener el valor en el idioma fuente
        source_value = get_message(key, source_language)
        
        # Si el valor es la misma clave, es que no existe
        if source_value == key:
            return {
                "success": False,
                "key": key,
                "error": "La clave no existe en el idioma fuente"
            }
        
        # Traducir el valor
        translated_value = translate_text(source_value, source_language, target_language)
        
        # Si se debe actualizar automáticamente
        if auto_update and translated_value:
            update_message(key, translated_value, target_language)
        
        return {
            "success": True,
            "key": key,
            "source_value": source_value,
            "translated_value": translated_value
        }
    
    except Exception as e:
        return {
            "success": False,
            "key": key,
            "error": str(e)
        }

def translate_text(text: str, source_language: str, target_language: str) -> str:
    """
    Traduce un texto de un idioma a otro
    
    Args:
        text: Texto a traducir
        source_language: Idioma fuente
        target_language: Idioma destino
        
    Returns:
        Texto traducido
    """
    # Intentar usar Claude para traducir si está disponible
    try:
        from ai.claude.client import generate_claude_response
        
        prompt = f"""
        Traduce el siguiente texto de {settings.get_language_name(source_language)} a {settings.get_language_name(target_language)}:
        
        "{text}"
        
        Devuelve solo el texto traducido, sin comillas ni explicaciones adicionales.
        """
        
        translated = generate_claude_response(prompt, max_tokens=1000)
        
        # Limpiar la respuesta
        translated = translated.strip().strip('"\'')
        
        return translated
    
    except ImportError:
        logger.warning("No se pudo importar el cliente de Claude para traducción")
        return text
    
    except Exception as e:
        logger.error(f"Error al traducir texto con Claude: {e}")
        return text

def get_all_keys(messages: Dict[str, Any], prefix: str = "") -> Set[str]:
    """
    Obtiene todas las claves de un diccionario de mensajes, incluyendo claves anidadas
    
    Args:
        messages: Diccionario de mensajes
        prefix: Prefijo para las claves anidadas
        
    Returns:
        Conjunto de claves
    """
    keys = set()
    
    for key, value in messages.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Recursivamente obtener claves de diccionarios anidados
            nested_keys = get_all_keys(value, full_key)
            keys.update(nested_keys)
        else:
            keys.add(full_key)
    
    return keys

def validate_messages() -> Dict[str, Any]:
    """
    Valida que todos los idiomas tengan las mismas claves
    
    Returns:
        Diccionario con resultados de la validación
    """
    # Si los mensajes no están cargados, cargarlos
    if not _MESSAGES:
        load_messages()
    
    results = {
        "languages": list(_MESSAGES.keys()),
        "missing_keys": {},
        "extra_keys": {}
    }
    
    # Si no hay idiomas cargados, no hay nada que validar
    if not _MESSAGES:
        return results
    
    # Usar el primer idioma como referencia
    reference_lang = settings.DEFAULT_LANGUAGE
    if reference_lang not in _MESSAGES:
        reference_lang = list(_MESSAGES.keys())[0]
    
    reference_keys = get_all_keys(_MESSAGES[reference_lang])
    
    # Comparar cada idioma con la referencia
    for lang_code, messages in _MESSAGES.items():
        if lang_code == reference_lang:
            continue
        
        lang_keys = get_all_keys(messages)
        
        # Claves que faltan en este idioma
        missing = reference_keys - lang_keys
        if missing:
            results["missing_keys"][lang_code] = list(missing)
        
        # Claves extra en este idioma
        extra = lang_keys - reference_keys
        if extra:
            results["extra_keys"][lang_code] = list(extra)
    
    return results

# Cargar mensajes al importar el módulo
load_messages() 