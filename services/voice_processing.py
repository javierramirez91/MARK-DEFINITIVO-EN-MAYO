"""
Servicio de procesamiento de voz para el asistente Mark.
Permite recibir mensajes de audio y generar respuestas de voz.
"""
import logging
import os
import tempfile
from typing import Dict, Optional, Tuple, Any

import aiofiles
import aiohttp
import asyncio
from fastapi import UploadFile
from pydub import AudioSegment

# Configurar logging
logger = logging.getLogger("mark.voice-processing")

class VoiceProcessingService:
    """
    Servicio para procesar mensajes de voz y generar respuestas de audio.
    Permite a los pacientes enviar notas de voz y recibir respuestas de audio.
    """
    
    def __init__(self):
        """Inicializar el servicio de procesamiento de voz"""
        # Comprobar si las dependencias están disponibles
        try:
            from core.config import settings
            
            # Configurar APIs para STT y TTS
            self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
            self.google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)
            self.azure_speech_key = getattr(settings, 'AZURE_SPEECH_KEY', None)
            self.azure_speech_region = getattr(settings, 'AZURE_SPEECH_REGION', None)
            
            # Determinar qué servicios están disponibles
            self.stt_service = None
            self.tts_service = None
            
            if self.openai_api_key:
                self.stt_service = "openai"
                self.tts_service = "openai"
            elif self.azure_speech_key and self.azure_speech_region:
                self.stt_service = "azure"
                self.tts_service = "azure"
            elif self.google_api_key:
                self.stt_service = "google"
                self.tts_service = "google"
                
            # Si no hay servicios disponibles, deshabilitar
            if not self.stt_service or not self.tts_service:
                logger.warning("No hay servicios de STT/TTS configurados. Funcionalidad de voz deshabilitada.")
                self.voice_enabled = False
            else:
                self.voice_enabled = True
                logger.info(f"Servicio de voz inicializado. STT: {self.stt_service}, TTS: {self.tts_service}")
                
        except ImportError as e:
            logger.error(f"Error al inicializar servicio de voz: {e}")
            self.voice_enabled = False
    
    async def save_temp_audio(self, audio_file: UploadFile) -> Optional[str]:
        """
        Guarda un archivo de audio recibido en un archivo temporal.
        
        Args:
            audio_file: Archivo de audio recibido
            
        Returns:
            Ruta al archivo temporal o None si hay error
        """
        if not self.voice_enabled:
            return None
            
        try:
            # Crear archivo temporal
            temp_dir = os.path.join(tempfile.gettempdir(), "mark_audio")
            os.makedirs(temp_dir, exist_ok=True)
            
            file_path = os.path.join(temp_dir, f"voice_input_{os.urandom(8).hex()}.ogg")
            
            # Guardar el archivo
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await audio_file.read()
                await out_file.write(content)
                
            logger.debug(f"Audio guardado temporalmente en {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error al guardar archivo de audio: {e}")
            return None
    
    async def convert_audio_format(self, input_path: str, target_format: str = "wav") -> Optional[str]:
        """
        Convierte un archivo de audio a otro formato.
        
        Args:
            input_path: Ruta al archivo de audio original
            target_format: Formato de destino (wav, mp3, etc.)
            
        Returns:
            Ruta al archivo convertido o None si hay error
        """
        try:
            # Determinar el formato del archivo original
            input_format = input_path.split('.')[-1].lower()
            
            # Generar ruta para el archivo convertido
            output_path = input_path.rsplit('.', 1)[0] + f".{target_format}"
            
            # Convertir el archivo
            audio = AudioSegment.from_file(input_path, format=input_format)
            audio.export(output_path, format=target_format)
            
            logger.debug(f"Audio convertido de {input_format} a {target_format}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error al convertir formato de audio: {e}")
            return None
    
    async def transcribe_audio_openai(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio usando la API de OpenAI.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            import openai
            
            # Configurar API key
            openai.api_key = self.openai_api_key
            
            # Convertir a formato compatible si es necesario
            if not audio_path.endswith('.mp3') and not audio_path.endswith('.wav'):
                audio_path = await self.convert_audio_format(audio_path, "mp3")
                if not audio_path:
                    return None
            
            # Transcribir con Whisper
            with open(audio_path, "rb") as audio_file:
                response = await openai.Audio.atranscribe(
                    file=audio_file,
                    model="whisper-1",
                    language="es"  # Podríamos detectar automáticamente
                )
                
            if response and 'text' in response:
                return response['text'].strip()
            return None
            
        except Exception as e:
            logger.error(f"Error al transcribir audio con OpenAI: {e}")
            return None
    
    async def transcribe_audio_azure(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio usando Azure Speech Services.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Convertir a formato compatible si es necesario
            if not audio_path.endswith('.wav'):
                audio_path = await self.convert_audio_format(audio_path, "wav")
                if not audio_path:
                    return None
            
            # Configurar el reconocedor de voz
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key, 
                region=self.azure_speech_region
            )
            
            # Configurar el idioma (podríamos detectarlo automáticamente)
            speech_config.speech_recognition_language = "es-ES"
            
            # Crear reconocedor con audio desde archivo
            audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Iniciar reconocimiento
            result = speech_recognizer.recognize_once_async().get()
            
            # Procesar resultado
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No se pudo reconocer el habla en el audio")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speechsdk.CancellationDetails(result)
                logger.error(f"Reconocimiento cancelado: {cancellation.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Error al transcribir audio con Azure: {e}")
            return None
    
    async def transcribe_audio_google(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio usando Google Speech-to-Text.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            from google.cloud import speech
            
            # Convertir a formato compatible si es necesario
            if not audio_path.endswith('.wav'):
                audio_path = await self.convert_audio_format(audio_path, "wav")
                if not audio_path:
                    return None
            
            # Configurar cliente
            client = speech.SpeechClient()
            
            # Cargar audio
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
                
            # Configurar reconocimiento
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="es-ES",  # Podríamos detectar automáticamente
                enable_automatic_punctuation=True
            )
            
            # Realizar transcripción
            response = client.recognize(config=config, audio=audio)
            
            # Extraer texto
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
                
            return transcript if transcript else None
            
        except Exception as e:
            logger.error(f"Error al transcribir audio con Google: {e}")
            return None
    
    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe el audio a texto utilizando el servicio configurado.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Texto transcrito o None si hay error
        """
        if not self.voice_enabled or not self.stt_service:
            return None
            
        # Seleccionar el servicio adecuado
        if self.stt_service == "openai":
            return await self.transcribe_audio_openai(audio_path)
        elif self.stt_service == "azure":
            return await self.transcribe_audio_azure(audio_path)
        elif self.stt_service == "google":
            return await self.transcribe_audio_google(audio_path)
        else:
            logger.error(f"Servicio STT '{self.stt_service}' no implementado")
            return None
    
    async def generate_audio_openai(self, text: str, language: str = "es") -> Optional[str]:
        """
        Genera audio a partir de texto usando OpenAI TTS.
        
        Args:
            text: Texto para convertir a audio
            language: Código de idioma
            
        Returns:
            Ruta al archivo de audio generado o None si hay error
        """
        try:
            import openai
            
            # Configurar API key
            openai.api_key = self.openai_api_key
            
            # Determinar voz según idioma
            voice_map = {
                "es": "alloy",
                "ca": "alloy",
                "en": "echo",
                "ar": "alloy"
            }
            voice = voice_map.get(language, "alloy")
            
            # Generar archivo temporal para guardar audio
            temp_dir = os.path.join(tempfile.gettempdir(), "mark_audio")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"voice_output_{os.urandom(8).hex()}.mp3")
            
            # Generar audio con OpenAI
            response = await openai.Audio.aspeech(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Guardar audio en archivo
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.content)
                
            logger.debug(f"Audio generado con OpenAI: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error al generar audio con OpenAI: {e}")
            return None
    
    async def generate_audio_azure(self, text: str, language: str = "es") -> Optional[str]:
        """
        Genera audio a partir de texto usando Azure Speech Services.
        
        Args:
            text: Texto para convertir a audio
            language: Código de idioma
            
        Returns:
            Ruta al archivo de audio generado o None si hay error
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Mapeo de idiomas a voces y configuraciones regionales
            voice_map = {
                "es": ("es-ES-ElviraNeural", "es-ES"),
                "ca": ("ca-ES-JoanaNeural", "ca-ES"),
                "en": ("en-US-JaneNeural", "en-US"),
                "ar": ("ar-EG-SalmaNeural", "ar-EG")
            }
            
            voice, locale = voice_map.get(language, ("es-ES-ElviraNeural", "es-ES"))
            
            # Configurar servicio de voz
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key, 
                region=self.azure_speech_region
            )
            speech_config.speech_synthesis_voice_name = voice
            
            # Generar archivo temporal para guardar audio
            temp_dir = os.path.join(tempfile.gettempdir(), "mark_audio")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"voice_output_{os.urandom(8).hex()}.wav")
            
            # Configurar salida de audio a archivo
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            
            # Crear sintetizador y generar audio
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_text_async(text).get()
            
            # Verificar resultado
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.debug(f"Audio generado con Azure: {output_path}")
                return output_path
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speechsdk.CancellationDetails(result)
                logger.error(f"Síntesis cancelada: {cancellation.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Error al generar audio con Azure: {e}")
            return None
    
    async def generate_audio_google(self, text: str, language: str = "es") -> Optional[str]:
        """
        Genera audio a partir de texto usando Google Text-to-Speech.
        
        Args:
            text: Texto para convertir a audio
            language: Código de idioma
            
        Returns:
            Ruta al archivo de audio generado o None si hay error
        """
        try:
            from google.cloud import texttospeech
            
            # Mapeo de idiomas a configuraciones
            language_map = {
                "es": "es-ES",
                "ca": "ca-ES",
                "en": "en-US",
                "ar": "ar-XA"
            }
            locale = language_map.get(language, "es-ES")
            
            # Inicializar cliente
            client = texttospeech.TextToSpeechClient()
            
            # Configurar entrada de texto
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configurar voz
            voice = texttospeech.VoiceSelectionParams(
                language_code=locale,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Configurar audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Generar audio
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Guardar en archivo
            temp_dir = os.path.join(tempfile.gettempdir(), "mark_audio")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"voice_output_{os.urandom(8).hex()}.mp3")
            
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                
            logger.debug(f"Audio generado con Google: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error al generar audio con Google: {e}")
            return None
    
    async def generate_audio(self, text: str, language: str = "es") -> Optional[str]:
        """
        Genera audio a partir de texto utilizando el servicio configurado.
        
        Args:
            text: Texto para convertir a audio
            language: Código de idioma
            
        Returns:
            Ruta al archivo de audio generado o None si hay error
        """
        if not self.voice_enabled or not self.tts_service:
            return None
            
        # Seleccionar el servicio adecuado
        if self.tts_service == "openai":
            return await self.generate_audio_openai(text, language)
        elif self.tts_service == "azure":
            return await self.generate_audio_azure(text, language)
        elif self.tts_service == "google":
            return await self.generate_audio_google(text, language)
        else:
            logger.error(f"Servicio TTS '{self.tts_service}' no implementado")
            return None
    
    async def process_voice_message(self, audio_file: UploadFile, language: str = "es") -> Optional[Dict[str, Any]]:
        """
        Procesa un mensaje de voz completo.
        
        Args:
            audio_file: Archivo de audio recibido
            language: Código de idioma
            
        Returns:
            Diccionario con texto transcrito o None si hay error
        """
        if not self.voice_enabled:
            return None
            
        try:
            # Guardar archivo temporal
            temp_path = await self.save_temp_audio(audio_file)
            if not temp_path:
                return None
                
            # Transcribir audio
            transcribed_text = await self.transcribe_audio(temp_path)
            if not transcribed_text:
                return None
                
            # Eliminar archivo temporal
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return {
                "text": transcribed_text,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje de voz: {e}")
            return None
            
    async def create_voice_response(self, text: str, language: str = "es") -> Optional[Dict[str, Any]]:
        """
        Crea una respuesta de voz a partir de texto.
        
        Args:
            text: Texto para convertir a audio
            language: Código de idioma
            
        Returns:
            Diccionario con información del audio generado o None si hay error
        """
        if not self.voice_enabled:
            return None
            
        try:
            # Generar audio
            audio_path = await self.generate_audio(text, language)
            if not audio_path:
                return None
                
            # Get file size and basic info
            file_size = os.path.getsize(audio_path)
            duration = 0  # Podríamos calcular la duración exacta
            
            return {
                "audio_path": audio_path,
                "file_size": file_size,
                "duration": duration,
                "format": audio_path.split('.')[-1],
                "text": text
            }
            
        except Exception as e:
            logger.error(f"Error al crear respuesta de voz: {e}")
            return None


# Crear instancia del servicio para exportar
voice_processing_service = VoiceProcessingService() 