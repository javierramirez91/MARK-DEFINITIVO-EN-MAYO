"""
Servicio para integración con WhatsApp a través de Twilio.
Permite enviar y recibir mensajes de WhatsApp y manejar mensajes de voz.
"""
import logging
import json
import base64
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Union
import os
import asyncio
from urllib.parse import urlparse, parse_qs

import httpx
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from pydantic import BaseModel

from core.config import settings, VIRTUAL_ASSISTANT_NAME, VIRTUAL_ASSISTANT_NUMBER
from ai.language_detection import detect_language
from ai.claude.client import handle_conversation
from ai.hume.voice_handler import process_voice_message
from database.d1_client import get_patient_by_phone, update_patient_last_contact

logger = logging.getLogger("mark-assistant.whatsapp")

# Inicializar cliente de Twilio si las credenciales están disponibles
twilio_client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        logger.info("Cliente Twilio inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar cliente Twilio: {e}")

class WhatsAppMessage(BaseModel):
    """Modelo para un mensaje de WhatsApp"""
    body: Optional[str] = None
    from_number: str
    to_number: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    is_voice: bool = False
    message_sid: Optional[str] = None

def verify_twilio_signature(signature: str, request_url: str, request_body: Dict[str, Any]) -> bool:
    """
    Verifica la firma de Twilio para asegurar que la solicitud es auténtica
    
    Args:
        signature: Firma de Twilio
        request_url: URL completa de la solicitud
        request_body: Cuerpo de la solicitud
        
    Returns:
        True si la firma es válida, False en caso contrario
    """
    if not settings.TWILIO_AUTH_TOKEN:
        logger.warning("No se puede verificar la firma de Twilio: auth token no configurado")
        return False
    
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(request_url, request_body, signature)

async def send_whatsapp_message(
    to: str,
    message: str,
    media_url: Optional[str] = None,
    from_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envía un mensaje de WhatsApp utilizando Twilio
    
    Args:
        to: Número de teléfono destinatario en formato E.164 (ej. +34612345678)
        message: Contenido del mensaje
        media_url: URL opcional de un archivo multimedia a enviar
        from_number: Número de origen (por defecto usa VIRTUAL_ASSISTANT_NUMBER)
        
    Returns:
        Respuesta de Twilio como diccionario
    """
    if not twilio_client:
        error_msg = "No se puede enviar mensaje de WhatsApp: cliente Twilio no inicializado"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Asegurar que los números estén en formato WhatsApp
    from_whatsapp = from_number or VIRTUAL_ASSISTANT_NUMBER
    if not from_whatsapp.startswith("whatsapp:"):
        from_whatsapp = f"whatsapp:{from_whatsapp}"
    
    to_whatsapp = to
    if not to_whatsapp.startswith("whatsapp:"):
        to_whatsapp = f"whatsapp:{to_whatsapp}"
    
    try:
        # Preparar los parámetros del mensaje
        message_params = {
            "body": message,
            "from_": from_whatsapp,
            "to": to_whatsapp,
        }
        
        # Añadir media_url si está presente
        if media_url:
            message_params["media_url"] = [media_url]
        
        # Enviar el mensaje
        twilio_message = twilio_client.messages.create(**message_params)
        
        logger.info(f"Mensaje WhatsApp enviado a {to}, SID: {twilio_message.sid}")
        
        return {
            "sid": twilio_message.sid,
            "status": twilio_message.status,
            "to": to,
            "from": from_whatsapp,
        }
    
    except Exception as e:
        error_message = f"Error al enviar mensaje WhatsApp a {to}: {e}"
        logger.error(error_message)
        return {"error": error_message}

async def download_media(media_url: str) -> Optional[bytes]:
    """
    Descarga contenido multimedia desde una URL de Twilio
    
    Args:
        media_url: URL del contenido multimedia
        
    Returns:
        Contenido como bytes o None si hay error
    """
    # Twilio requiere autenticación para descargar medios
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, auth=auth)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"Error al descargar multimedia desde {media_url}: {e}")
        return None

async def process_media_message(message: WhatsAppMessage) -> Optional[str]:
    """
    Procesa un mensaje multimedia de WhatsApp
    
    Args:
        message: Mensaje de WhatsApp con contenido multimedia
        
    Returns:
        Texto extraído o procesado del contenido multimedia
    """
    if not message.media_url:
        return None
    
    # Descargar el contenido multimedia
    media_content = await download_media(message.media_url)
    if not media_content:
        return None
    
    # Procesar según el tipo de contenido
    if message.is_voice or message.media_type in ["audio/ogg", "audio/mpeg", "audio/mp4"]:
        # Mensaje de voz: transcribir con Hume
        transcript = await process_voice_message(media_content)
        return transcript
    
    # Para otros tipos de contenido, podríamos implementar procesamiento adicional
    # Por ejemplo, OCR para imágenes, etc.
    
    return None

async def handle_whatsapp_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un webhook de WhatsApp de Twilio
    
    Args:
        webhook_data: Datos del webhook
        
    Returns:
        Resultado del procesamiento
    """
    try:
        # Extraer datos relevantes del webhook
        message_sid = webhook_data.get("MessageSid", webhook_data.get("SmsSid"))
        from_number = webhook_data.get("From", "")
        to_number = webhook_data.get("To", "")
        body = webhook_data.get("Body", "")
        
        # Verificar si hay contenido multimedia
        num_media = int(webhook_data.get("NumMedia", "0"))
        media_url = None
        media_type = None
        is_voice = False
        
        if num_media > 0:
            media_url = webhook_data.get("MediaUrl0")
            media_type = webhook_data.get("MediaContentType0")
            
            # Determinar si es un mensaje de voz
            if media_type in ["audio/ogg", "audio/mpeg", "audio/mp4"]:
                is_voice = True
        
        # Crear objeto de mensaje
        whatsapp_message = WhatsAppMessage(
            body=body,
            from_number=from_number,
            to_number=to_number,
            media_url=media_url,
            media_type=media_type,
            is_voice=is_voice,
            message_sid=message_sid
        )
        
        # Procesar mensaje
        response = await process_whatsapp_message(whatsapp_message)
        return response
    
    except Exception as e:
        logger.error(f"Error al procesar webhook de WhatsApp: {e}")
        return {"status": "error", "message": str(e)}

async def process_whatsapp_message(message: WhatsAppMessage) -> Dict[str, Any]:
    """
    Procesa un mensaje de WhatsApp y genera una respuesta
    
    Args:
        message: Mensaje de WhatsApp a procesar
        
    Returns:
        Resultado del procesamiento
    """
    try:
        # Obtener número de teléfono sin el prefijo 'whatsapp:'
        phone = message.from_number
        if phone.startswith("whatsapp:"):
            phone = phone[9:]  # Quitar 'whatsapp:'
        
        # Buscar datos existentes del paciente
        patient_data = get_patient_by_phone(phone)
        
        # Variable para almacenar el texto a procesar
        message_text = message.body or ""
        
        # Si hay contenido multimedia, procesarlo
        if message.media_url:
            media_text = await process_media_message(message)
            if media_text:
                # Si el cuerpo del mensaje está vacío, usar solo el texto del multimedia
                if not message_text:
                    message_text = media_text
                else:
                    # Si hay texto en el cuerpo, combinar con el texto del multimedia
                    message_text = f"{message_text}\n\n[Contenido multimedia: {media_text}]"
        
        # Si después de procesar todo, no hay texto, usar un mensaje por defecto
        if not message_text.strip():
            message_text = "[Mensaje sin texto]"
        
        # Detectar el idioma del mensaje
        language = detect_language(message_text)
        
        # Construir contexto
        context = ""
        if patient_data:
            context = f"""
Información del paciente:
- Nombre: {patient_data.get('name', 'Desconocido')}
- Teléfono: {phone}
- Motivo de consulta: {patient_data.get('consultation_reason', 'No disponible')}
- Formato preferido: {patient_data.get('session_format', 'No especificado')}
"""
        
        # Procesar el mensaje con Claude
        session_data = {
            "messages": [],  # Iniciar una nueva conversación cada vez
            "context": context,
            "language": language,
            "user_id": patient_data.get("patient_id") if patient_data else None,
            "patient_name": patient_data.get("name") if patient_data else None,
        }
        
        # Seleccionar el playbook según el mensaje
        playbook_id = "1"  # Playbook por defecto
        message_lower = message_text.lower()
        
        if any(keyword in message_lower for keyword in ["urgencia", "urgent", "crisis", "emergencia", "emergency", "dina"]):
            playbook_id = "2"
        elif any(keyword in message_lower for keyword in ["cita", "sesión", "appointment", "pago", "payment"]):
            playbook_id = "3"
        
        # Procesar con Claude
        response_data = handle_conversation(
            user_input=message_text,
            language=language,
            conversation_id=message.message_sid or "",
            session_data=session_data,
            playbook_id=playbook_id
        )
        
        # Obtener la respuesta
        assistant_response = response_data["response"]
        
        # Enviar respuesta por WhatsApp
        whatsapp_response = await send_whatsapp_message(
            to=message.from_number,
            message=assistant_response
        )
        
        # Actualizar último contacto del paciente si existe
        if patient_data:
            update_patient_last_contact(patient_data.get("patient_id"))
        
        # Devolver resultado
        return {
            "status": "success",
            "language": language,
            "patient_id": patient_data.get("patient_id") if patient_data else None,
            "message_processed": True,
            "whatsapp_response": whatsapp_response,
            "playbook_used": playbook_id
        }
    
    except Exception as e:
        logger.error(f"Error al procesar mensaje de WhatsApp: {e}")
        
        # Intentar enviar un mensaje de error al usuario
        try:
            error_message = "Lo sentimos, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo más tarde."
            await send_whatsapp_message(
                to=message.from_number,
                message=error_message
            )
        except Exception as e2:
            logger.error(f"Error al enviar mensaje de error: {e2}")
        
        return {"status": "error", "message": str(e)} 