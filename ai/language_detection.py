"""
Módulo para la detección del idioma en los mensajes de usuario.
Garantiza que Mark responda siempre en el idioma adecuado.
"""
import logging
import re
from typing import Dict, List, Optional
import unicodedata

# Importación condicional de langdetect
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    # Hacer la detección determinista
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

from core.config import LanguageConfig
from ai.claude.client import generate_claude_response

logger = logging.getLogger("mark-assistant.language")

# Patrones de expresiones comunes en diferentes idiomas
LANGUAGE_PATTERNS = {
    "es": [
        r"\b(hola|buenos días|buenas tardes|buenas noches|gracias|por favor|ayuda|necesito|quiero)\b",
        r"\b(cómo estás|cómo va|qué tal|hasta luego|adiós|nos vemos|vale|sí|no)\b",
        r"\b(hablar|llamar|contactar|preguntar|responder|entender|escuchar)\b"
    ],
    "ca": [
        r"\b(hola|bon dia|bona tarda|bona nit|gràcies|si us plau|ajuda|necessito|vull)\b",
        r"\b(com estàs|com va|què tal|fins aviat|adéu|ens veiem|d'acord|sí|no)\b",
        r"\b(parlar|trucar|contactar|preguntar|respondre|entendre|escoltar)\b"
    ],
    "en": [
        r"\b(hello|hi|good morning|good afternoon|good evening|thanks|thank you|please|help|I need|I want)\b",
        r"\b(how are you|what's up|see you|goodbye|bye|OK|yes|no)\b",
        r"\b(talk|call|contact|ask|answer|understand|listen)\b"
    ],
    "ar": [
        r"(مرحبا|صباح الخير|مساء الخير|شكرا|من فضلك|مساعدة|أحتاج|أريد)",
        r"(كيف حالك|إلى اللقاء|وداعا|نعم|لا)",
        r"(تحدث|اتصل|سؤال|جواب|فهم|استمع)"
    ]
}

# Palabras específicas que son fuertes indicadores de un idioma
LANGUAGE_SPECIFIC_WORDS = {
    "es": ["porque", "aunque", "entonces", "pero", "ahora", "siempre", "nunca", "aquí", "hoy", "mañana", "ayer", "esto", "eso"],
    "ca": ["perquè", "encara", "llavors", "però", "ara", "sempre", "mai", "aquí", "avui", "demà", "ahir", "això", "allò"],
    "en": ["because", "although", "then", "but", "now", "always", "never", "here", "today", "tomorrow", "yesterday", "this", "that"],
    "ar": ["لأن", "رغم أن", "ثم", "لكن", "الآن", "دائما", "أبدا", "هنا", "اليوم", "غدا", "أمس", "هذا", "ذلك"]
}

def normalize_text(text: str) -> str:
    """
    Normaliza el texto eliminando acentos y caracteres especiales
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar acentos (solo para caracteres latinos)
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    
    return text

def count_pattern_matches(text: str, language: str) -> int:
    """
    Cuenta el número de coincidencias de patrones para un idioma específico
    
    Args:
        text: Texto a analizar
        language: Código del idioma a buscar
        
    Returns:
        Número de coincidencias encontradas
    """
    if language not in LANGUAGE_PATTERNS:
        return 0
    
    count = 0
    for pattern in LANGUAGE_PATTERNS[language]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        count += len(matches)
    
    return count

def count_specific_words(text: str, language: str) -> int:
    """
    Cuenta palabras específicas de un idioma en el texto
    
    Args:
        text: Texto a analizar
        language: Código del idioma a buscar
        
    Returns:
        Número de palabras específicas encontradas
    """
    if language not in LANGUAGE_SPECIFIC_WORDS:
        return 0
    
    count = 0
    words = text.lower().split()
    
    for word in LANGUAGE_SPECIFIC_WORDS[language]:
        if word in words:
            count += 1
    
    return count

def detect_language_with_langdetect(text: str) -> Optional[str]:
    """
    Detecta el idioma usando langdetect
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código del idioma detectado o None si no se pudo detectar
    """
    if not LANGDETECT_AVAILABLE:
        return None
    
    try:
        language = detect(text)
        
        # Mapear a nuestros códigos de idioma soportados
        language_mapping = {
            "es": "es",
            "ca": "ca",
            "en": "en",
            "ar": "ar"
        }
        
        return language_mapping.get(language, None)
    except LangDetectException:
        return None
    except Exception as e:
        logger.error(f"Error al detectar idioma con langdetect: {e}")
        return None

def detect_language_with_claude(text: str) -> Optional[str]:
    """
    Detecta el idioma usando Claude
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código del idioma detectado o None si no se pudo detectar
    """
    prompt = f"""
Por favor, analiza el siguiente texto y determina si está escrito en español (es), catalán (ca), inglés (en) o árabe (ar).
Responde únicamente con el código de dos letras correspondiente: "es", "ca", "en" o "ar".

Texto a analizar:
```
{text}
```

Código de idioma (solo responde con uno de estos: "es", "ca", "en", "ar"):
"""
    
    try:
        response = generate_claude_response(prompt, max_tokens=10)
        response = response.strip().lower()
        
        # Verificar que la respuesta sea un código de idioma válido
        if response in LanguageConfig.SUPPORTED_LANGUAGES:
            return response
        
        # Intentar extraer un código válido de la respuesta
        for lang in LanguageConfig.SUPPORTED_LANGUAGES:
            if lang in response:
                return lang
        
        return None
    except Exception as e:
        logger.error(f"Error al detectar idioma con Claude: {e}")
        return None

def detect_language(text: str, user_id: Optional[str] = None, session_data: Optional[Dict] = None) -> str:
    """
    Detecta el idioma del texto proporcionado usando múltiples métodos.
    
    Args:
        text: Texto a analizar
        user_id: ID del usuario (para persistencia de idioma)
        session_data: Datos de sesión previos
        
    Returns:
        Código del idioma detectado (es, ca, en, ar)
    """
    # Verificar si ya tenemos un idioma registrado para el usuario
    if session_data and "language" in session_data:
        logger.info(f"Usando idioma previamente detectado: {session_data['language']}")
        return session_data["language"]
    
    # Si el texto es muy corto, usar heurísticas simples
    if len(text.strip()) < 15:
        normalized_text = normalize_text(text)
        
        # Verificar saludos y expresiones comunes
        if re.search(r'\b(hello|hi|hey|good morning|good afternoon)\b', normalized_text):
            return "en"
        elif re.search(r'\b(hola|buenos dias|buenas tardes|buenas noches)\b', normalized_text):
            return "es"
        elif re.search(r'\b(bon dia|hola|bona tarda|bona nit)\b', normalized_text):
            return "ca"
        elif "مرحبا" in text or "صباح الخير" in text or "مساء الخير" in text:
            return "ar"
    
    # Método 1: Contar coincidencias de patrones
    pattern_scores = {}
    for lang in LanguageConfig.SUPPORTED_LANGUAGES:
        pattern_scores[lang] = count_pattern_matches(text, lang)
    
    # Método 2: Contar palabras específicas del idioma
    word_scores = {}
    for lang in LanguageConfig.SUPPORTED_LANGUAGES:
        word_scores[lang] = count_specific_words(text, lang)
    
    # Método 3: Usar langdetect si está disponible
    langdetect_result = detect_language_with_langdetect(text)
    
    # Método 4: Usar Claude para detección definitiva si es necesario
    if langdetect_result:
        # Si langdetect da un resultado, combinarlo con nuestras heurísticas
        pattern_max = max(pattern_scores.values()) if pattern_scores else 0
        word_max = max(word_scores.values()) if word_scores else 0
        
        if pattern_max > 0 or word_max > 0:
            # Hay evidencia de heurísticas
            pattern_best = max(pattern_scores.items(), key=lambda x: x[1]) if pattern_scores else (None, 0)
            word_best = max(word_scores.items(), key=lambda x: x[1]) if word_scores else (None, 0)
            
            # Si hay consenso entre métodos, usar ese resultado
            if langdetect_result == pattern_best[0] or langdetect_result == word_best[0]:
                return langdetect_result
            
            # Si no hay consenso y las heurísticas son fuertes, consultar a Claude
            if pattern_best[1] > 2 or word_best[1] > 1:
                claude_result = detect_language_with_claude(text)
                if claude_result:
                    return claude_result
            
            # Si no, confiar en langdetect
            return langdetect_result
        else:
            # Sin evidencia de heurísticas, confiar en langdetect
            return langdetect_result
    
    # Si llegamos aquí, no tenemos resultado de langdetect
    pattern_max = max(pattern_scores.values()) if pattern_scores else 0
    word_max = max(word_scores.values()) if word_scores else 0
    
    if pattern_max > 0 or word_max > 0:
        # Tomar el mejor resultado de heurísticas
        pattern_best = max(pattern_scores.items(), key=lambda x: x[1]) if pattern_scores else (None, 0)
        word_best = max(word_scores.items(), key=lambda x: x[1]) if word_scores else (None, 0)
        
        # Si hay consenso entre heurísticas, usar ese resultado
        if pattern_best[0] and word_best[0] and pattern_best[0] == word_best[0]:
            return pattern_best[0]
        
        # Si no hay consenso, usar el más fuerte
        if pattern_best[1] > word_best[1]:
            return pattern_best[0]
        else:
            return word_best[0]
    
    # Como último recurso, consultar a Claude
    claude_result = detect_language_with_claude(text)
    if claude_result:
        return claude_result
    
    # Si todo falla, usar el idioma por defecto
    logger.warning(f"No se pudo detectar el idioma, usando idioma por defecto: {LanguageConfig.DEFAULT_LANGUAGE}")
    return LanguageConfig.DEFAULT_LANGUAGE 