"""
Módulo mejorado para la detección del idioma en los mensajes de usuario.
Implementa un sistema basado en Machine Learning para una detección más precisa.
"""
import logging
from typing import Dict, List, Optional, Any, Union
import unicodedata

# Importaciones para ML
try:
    import fasttext
    import numpy as np
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    ML_LIBRARIES_AVAILABLE = True
except ImportError:
    ML_LIBRARIES_AVAILABLE = False

# Fallback
from ai.language_detection import detect_language as legacy_detect_language

logger = logging.getLogger("mark-assistant.language-ml")

# Ruta al modelo preentrenado de FastText (se descargará automáticamente si no existe)
FASTTEXT_MODEL_PATH = "models/lid.176.bin"

# Modelo de Hugging Face para detección de idioma
HF_MODEL_NAME = "papluca/xlm-roberta-base-language-detection"

class LanguageDetectorML:
    """Detector de idioma basado en técnicas de Machine Learning"""
    
    def __init__(self):
        """Inicializa el detector de idioma con modelos ML"""
        self.models_loaded = False
        self.fasttext_model = None
        self.transformer_pipeline = None
        
        if ML_LIBRARIES_AVAILABLE:
            try:
                # Intentar cargar el modelo FastText
                self.fasttext_model = fasttext.load_model(FASTTEXT_MODEL_PATH)
                
                # Configurar pipeline de transformers
                self.transformer_pipeline = pipeline(
                    "text-classification", 
                    model=HF_MODEL_NAME,
                    tokenizer=HF_MODEL_NAME
                )
                
                self.models_loaded = True
                logger.info("Modelos de ML para detección de idioma cargados correctamente")
            except Exception as e:
                logger.error(f"Error al cargar modelos de ML para detección de idioma: {e}")
    
    def normalize_text(self, text: str) -> str:
        """Normaliza el texto para mejorar la detección"""
        # Eliminar acentos
        text = ''.join(c for c in unicodedata.normalize('NFD', text)
                      if unicodedata.category(c) != 'Mn')
        # Convertir a minúsculas
        text = text.lower()
        return text
    
    def detect_with_fasttext(self, text: str) -> Optional[str]:
        """Detecta el idioma usando FastText"""
        if not self.models_loaded or not self.fasttext_model:
            return None
        
        try:
            # FastText requiere texto con al menos algunos caracteres
            if len(text.strip()) < 3:
                return None
                
            # Obtener predicción de FastText
            predictions = self.fasttext_model.predict(text, k=3)
            languages = [lang.replace('__label__', '') for lang in predictions[0]]
            scores = predictions[1]
            
            # Mapear ISO 639-1 codes
            language_map = {
                'es': 'es',
                'ca': 'ca',
                'en': 'en',
                'ar': 'ar',
                'spa': 'es',
                'cat': 'ca',
                'eng': 'en',
                'ara': 'ar'
            }
            
            # Retornar el idioma con mayor confianza (si supera un umbral)
            if scores[0] > 0.6:
                detected = languages[0].lower()
                return language_map.get(detected, detected)
            
            return None
        except Exception as e:
            logger.error(f"Error en detección con FastText: {e}")
            return None
    
    def detect_with_transformers(self, text: str) -> Optional[str]:
        """Detecta el idioma usando Transformers"""
        if not self.models_loaded or not self.transformer_pipeline:
            return None
        
        try:
            # Transformers funciona mejor con textos más largos
            if len(text.strip()) < 5:
                return None
                
            # Obtener predicción con el pipeline de transformers
            result = self.transformer_pipeline(text, top_k=3)
            
            # Verificar resultado y retornar si la confianza es alta
            if result and result[0]['score'] > 0.75:
                # Mapear etiquetas al formato requerido
                language_map = {
                    'spanish': 'es',
                    'catalan': 'ca',
                    'english': 'en',
                    'arabic': 'ar',
                    'es': 'es',
                    'ca': 'ca',
                    'en': 'en',
                    'ar': 'ar'
                }
                detected = result[0]['label'].lower()
                return language_map.get(detected, None)
            
            return None
        except Exception as e:
            logger.error(f"Error en detección con Transformers: {e}")
            return None
    
    def detect_language(self, text: str, user_id: Optional[str] = None, session_data: Optional[Dict] = None) -> str:
        """
        Detecta el idioma del texto utilizando múltiples modelos y técnicas.
        
        Args:
            text: Texto para detectar el idioma
            user_id: ID del usuario (opcional)
            session_data: Datos de la sesión (opcional)
            
        Returns:
            Código ISO 639-1 del idioma detectado ('es', 'ca', 'en', 'ar')
            Por defecto 'es' si no se puede determinar
        """
        # Caso especial: texto vacío o muy corto
        if not text or len(text.strip()) < 3:
            # Si tenemos datos de sesión, usar el idioma anterior
            if session_data and 'language' in session_data:
                return session_data['language']
            return 'es'  # Valor por defecto
        
        # Normalizar texto
        normalized_text = self.normalize_text(text)
        
        # Intentar con FastText (rápido y eficiente)
        fasttext_result = self.detect_with_fasttext(normalized_text)
        if fasttext_result in ['es', 'ca', 'en', 'ar']:
            logger.debug(f"Idioma detectado con FastText: {fasttext_result}")
            return fasttext_result
            
        # Intentar con Transformers (más preciso pero más lento)
        transformer_result = self.detect_with_transformers(normalized_text)
        if transformer_result in ['es', 'ca', 'en', 'ar']:
            logger.debug(f"Idioma detectado con Transformers: {transformer_result}")
            return transformer_result
        
        # Si los modelos ML no pueden determinar el idioma, usar el método legacy
        legacy_result = legacy_detect_language(text, user_id, session_data)
        logger.debug(f"Fallback a detección legacy: {legacy_result}")
        return legacy_result

# Instanciar el detector
language_detector_ml = LanguageDetectorML()

# Función principal para exportar
def detect_language_ml(text: str, user_id: Optional[str] = None, session_data: Optional[Dict] = None) -> str:
    """
    Función principal para detectar el idioma del texto.
    
    Args:
        text: Texto para detectar el idioma
        user_id: ID del usuario (opcional)
        session_data: Datos de la sesión (opcional)
        
    Returns:
        Código ISO 639-1 del idioma detectado ('es', 'ca', 'en', 'ar')
    """
    return language_detector_ml.detect_language(text, user_id, session_data) 