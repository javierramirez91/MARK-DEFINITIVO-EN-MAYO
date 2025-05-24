"""
Integración con Hume EVI para la generación de voz.
Permite convertir texto a voz utilizando las voces de Hume.
"""
import os
import logging
import json
import asyncio
import base64
from typing import Dict, List, Optional, Any, Union
import httpx
import uuid

# Configurar logging
logger = logging.getLogger("mark.hume")

class HumeVoice:
    """
    Cliente para interactuar con la API de Hume EVI para la generación de voz.
    Permite convertir texto a voz utilizando las voces de Hume.
    """
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Inicializar el cliente de Hume EVI.
        
        Args:
            api_key: Clave API de Hume (opcional, por defecto usa la de settings)
            voice_id: ID de la voz a utilizar (opcional, por defecto usa la de settings)
        """
        # Intentar importar configuración
        try:
            from core.config import settings
            self.settings = settings
            self.api_key = api_key or settings.HUME_API_KEY
            self.voice_id = voice_id or settings.HUME_VOICE_ID
            self.config_id = settings.HUME_CONFIG_ID
            self.secret_key = settings.HUME_SECRET_KEY
        except ImportError:
            self.settings = None
            self.api_key = api_key or os.getenv("HUME_API_KEY")
            self.voice_id = voice_id or os.getenv("HUME_VOICE_ID", "default")
            self.config_id = os.getenv("HUME_CONFIG_ID")
            self.secret_key = os.getenv("HUME_SECRET_KEY")
        
        # Validar API key
        if not self.api_key:
            logger.error("No se ha proporcionado una clave API para Hume")
            raise ValueError("Se requiere una clave API para Hume")
        
        # Configurar cliente HTTP
        self.base_url = "https://api.hume.ai/v0"
        self.headers = {
            "Content-Type": "application/json",
            "X-Hume-Api-Key": self.api_key
        }
        
        # Configurar directorio para archivos de audio
        self.audio_dir = "static/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        logger.info(f"Cliente de Hume EVI inicializado con voz {self.voice_id}")
    
    async def generate_speech(
        self,
        text: str,
        language: str = "es",
        voice_id: Optional[str] = None,
        output_format: str = "mp3",
        save_to_file: bool = True
    ) -> str:
        """
        Genera audio a partir de texto utilizando la API de Hume EVI.
        
        Args:
            text: Texto a convertir en voz
            language: Código de idioma (es, ca, en, ar)
            voice_id: ID de la voz a utilizar (opcional)
            output_format: Formato de salida del audio (mp3, wav)
            save_to_file: Si es True, guarda el audio en un archivo
            
        Returns:
            URL o ruta al archivo de audio generado
        """
        # Usar la voz proporcionada o la predeterminada
        voice_id = voice_id or self.voice_id
        
        # Ajustar el texto según el idioma si es necesario
        text = self._prepare_text_for_language(text, language)
        
        # Preparar la solicitud
        payload = {
            "text": text,
            "voice_id": voice_id,
            "output_format": output_format
        }
        
        # Añadir configuración adicional si está disponible
        if self.config_id:
            payload["config_id"] = self.config_id
        
        logger.debug(f"Enviando solicitud a Hume EVI: {text[:50]}...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/speech/synthesis",
                    headers=self.headers,
                    json=payload
                )
                
                # Verificar respuesta
                if response.status_code != 200:
                    logger.error(f"Error en la API de Hume: {response.status_code} - {response.text}")
                    return ""
                
                # Procesar respuesta
                response_data = response.json()
                audio_data = response_data.get("audio", {}).get("data")
                
                if not audio_data:
                    logger.error("No se recibieron datos de audio de Hume")
                    return ""
                
                # Decodificar datos de audio
                audio_bytes = base64.b64decode(audio_data)
                
                # Guardar en archivo si se solicita
                if save_to_file:
                    file_name = f"{uuid.uuid4()}.{output_format}"
                    file_path = os.path.join(self.audio_dir, file_name)
                    
                    with open(file_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    # Construir URL relativa
                    audio_url = f"/static/audio/{file_name}"
                    logger.info(f"Audio guardado en {file_path}")
                    return audio_url
                else:
                    # Devolver datos codificados en base64
                    return f"data:audio/{output_format};base64,{audio_data}"
                
        except Exception as e:
            logger.error(f"Error al comunicarse con la API de Hume: {e}")
            return ""
    
    def _prepare_text_for_language(self, text: str, language: str) -> str:
        """
        Prepara el texto para la síntesis según el idioma.
        Puede aplicar ajustes específicos para cada idioma.
        
        Args:
            text: Texto a preparar
            language: Código de idioma
            
        Returns:
            Texto preparado para la síntesis
        """
        # Por ahora, simplemente devolvemos el texto sin modificar
        # Aquí se podrían aplicar ajustes específicos para cada idioma
        return text

# Crear instancia global del cliente
hume_voice = HumeVoice() 