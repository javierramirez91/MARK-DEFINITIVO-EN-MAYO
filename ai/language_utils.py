import asyncio
# import logging # No usado
from typing import Optional

# Config & Logger
from core.config import logger

# Detección de idioma
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    logger.warning("Librería 'langdetect' no encontrada. La detección de idioma no funcionará. Instalar con: pip install langdetect")
    LANGDETECT_AVAILABLE = False

async def detect_language(text: Optional[str]) -> str:
    """
    Detecta el idioma de un texto de forma asíncrona usando langdetect en un executor.
    
    Args:
        text: Texto a analizar.
        
    Returns:
        Código ISO 639-1 del idioma detectado (ej. 'en', 'es') o 'unknown'.
    """
    if not LANGDETECT_AVAILABLE or not text:
        return "unknown"
        
    loop = asyncio.get_running_loop()
    
    try:
        # Ejecutar la función síncrona detect() en el executor por defecto (ThreadPoolExecutor)
        lang_code = await loop.run_in_executor(
            None, # Usa el executor por defecto
            detect, # La función síncrona a llamar
            text    # El argumento para la función
        )
        logger.debug(f"Idioma detectado (async) para texto '{text[:30]}...': {lang_code}")
        return lang_code
    except LangDetectException:
        # Esto puede ocurrir si el texto es muy corto o ambiguo
        logger.warning(f"No se pudo detectar idioma de forma fiable (async) para: '{text[:50]}...'")
        return "unknown"
    except Exception as e:
        # Capturar otros errores inesperados durante la ejecución en el executor
        logger.error(f"Error inesperado en detect_language (async): {e}", exc_info=True)
        return "unknown" 