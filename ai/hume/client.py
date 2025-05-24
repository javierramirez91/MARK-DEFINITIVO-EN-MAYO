"""
Cliente para la API de Hume EVI
Gestiona el reconocimiento y síntesis de voz
"""
import os
import json
import base64
import httpx
from typing import Dict, List, Any, Optional, BinaryIO, Union
from core.config import settings

class HumeEVIClient:
    """Cliente para interactuar con la API de Hume EVI"""
    
    def __init__(self, api_key: Optional[str] = None, config_id: Optional[str] = None):
        """
        Inicializa el cliente de Hume EVI
        
        Args:
            api_key: Clave API de Hume (opcional, por defecto usa la de settings)
            config_id: ID de configuración de EVI (opcional, por defecto usa la de settings)
        """
        self.api_key = api_key or settings.HUME_API_KEY
        self.config_id = config_id or settings.HUME_CONFIG_ID
        self.base_url = "https://api.hume.ai/v0"
        self.headers = {
            "Content-Type": "application/json",
            "X-Hume-Api-Key": self.api_key
        }
    
    async def speech_to_text(
        self,
        audio_file: Union[str, BinaryIO],
        language: str = "es",
        model: str = "whisper-large-v3",
    ) -> Dict[str, Any]:
        """
        Convierte audio a texto utilizando Hume EVI
        
        Args:
            audio_file: Ruta al archivo de audio o objeto de archivo binario
            language: Código de idioma (es, ca, en, ar)
            model: Modelo de reconocimiento de voz a utilizar
            
        Returns:
            Respuesta con la transcripción del audio
        """
        # Preparar el audio
        if isinstance(audio_file, str):
            with open(audio_file, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
        else:
            audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
        
        # Mapear códigos de idioma a los códigos que acepta Whisper
        language_map = {
            "es": "es",
            "ca": "ca",
            "en": "en",
            "ar": "ar"
        }
        
        whisper_language = language_map.get(language, "es")
        
        payload = {
            "data": audio_data,
            "model": model,
            "language": whisper_language
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/speech-to-text",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.json() if response.content else "No error details"
                raise Exception(f"Error en la API de Hume EVI (STT): {response.status_code} - {error_detail}")
                
            return response.json()
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: str = "evi_female_es",
        output_format: str = "mp3",
    ) -> bytes:
        """
        Convierte texto a voz utilizando Hume EVI
        
        Args:
            text: Texto a convertir a voz
            voice_id: ID de la voz a utilizar
            output_format: Formato de salida (mp3, wav)
            
        Returns:
            Datos binarios del audio generado
        """
        # Mapeo de idiomas a voces de EVI
        voice_map = {
            "es": "evi_female_es",
            "ca": "evi_female_ca",
            "en": "evi_female_en",
            "ar": "evi_female_ar"
        }
        
        # Si el voice_id es un código de idioma, usar el mapeo
        if voice_id in voice_map:
            voice_id = voice_map[voice_id]
        
        payload = {
            "text": text,
            "voice_id": voice_id,
            "output_format": output_format,
            "config_id": self.config_id
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.json() if response.content else "No error details"
                raise Exception(f"Error en la API de Hume EVI (TTS): {response.status_code} - {error_detail}")
                
            # La respuesta contiene los datos de audio en base64
            response_data = response.json()
            audio_data = base64.b64decode(response_data["audio"])
            
            return audio_data
    
    async def detect_language(self, audio_file: Union[str, BinaryIO]) -> str:
        """
        Detecta el idioma de un archivo de audio
        
        Args:
            audio_file: Ruta al archivo de audio o objeto de archivo binario
            
        Returns:
            Código de idioma detectado (es, ca, en, ar)
        """
        # Primero convertimos el audio a texto sin especificar idioma
        result = await self.speech_to_text(audio_file, language="")
        
        # Extraer el idioma detectado
        detected_language = result.get("language", "es")
        
        # Mapear el idioma detectado a nuestros códigos de idioma
        language_map = {
            "spanish": "es",
            "catalan": "ca",
            "english": "en",
            "arabic": "ar"
        }
        
        return language_map.get(detected_language.lower(), "es")

# Instancia global del cliente
hume_evi = HumeEVIClient() 