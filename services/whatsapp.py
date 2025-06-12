"""
Servicio de WhatsApp para el asistente Mark utilizando la API de Meta (WABA).
Proporciona funciones para enviar mensajes y procesar webhooks entrantes de Meta.
"""
# logging es importado como logger desde core.config más abajo
import json
import hmac
import hashlib
import httpx
import asyncio # Necesario para asyncio.create_task
from typing import Dict, Any, Optional, Tuple # Eliminado List
# import os # Eliminado
# import requests # Eliminado
# import logging # ELIMINADO
# from dotenv import load_dotenv # ELIMINADO
# from functools import lru_cache # Eliminado

# Importar configuración necesaria
# from core.config import ApiConfig, logger, settings # ApiConfig no usada
from core.config import logger, settings # ApiConfig eliminada
from ai.gemma.client import generate_chat_response

# --- Funciones eliminadas relacionadas con Twilio ---
# TwilioClientSingleton
# verify_twilio_signature
# send_whatsapp_message (versión Twilio)
# download_media (versión Twilio)
# process_media_message (versión Twilio)
# handle_twilio_webhook (versión Twilio)
# check_message_status (versión Twilio)

# --- Nuevas funciones (esqueleto) para la integración con Meta WABA ---

async def send_whatsapp_message_meta(
    to: str,
    message: str,
    message_type: str = "text",
    template_name: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Envía un mensaje de WhatsApp a través de la API de Meta (WABA) de forma asíncrona.

    Args:
        to: Número de teléfono del destinatario (formato E.164)
        message: Contenido del mensaje (puede ser texto, ID de plantilla, etc.)
        message_type: Tipo de mensaje ('text', 'template', 'image', etc.)
        template_name: Nombre de la plantilla (si message_type='template')
        **kwargs: Argumentos adicionales para la API de Meta.

    Returns:
        Diccionario con información del mensaje enviado o error.
    """
    logger.info(f"Intentando enviar mensaje a {to}: '{message}'")
    
    # Obtener token de acceso y phone number ID
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", None)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)
    
    if not access_token or not phone_number_id:
        logger.error("Falta WHATSAPP_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID en la configuración")
        return {
            "success": False,
            "error": "Configuración incompleta",
            "to": to
        }
    
    # URL de la API de Graph de Meta (v18.0)
    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    # Preparar encabezados
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Preparar payload según el tipo de mensaje
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
    }
    
    # Mensaje de texto simple
    if message_type == "text":
        payload["type"] = "text"
        payload["text"] = {"body": message}
    
    # Mensaje de plantilla
    elif message_type == "template" and template_name:
        payload["type"] = "template"
        payload["template"] = {
            "name": template_name,
            "language": {"code": kwargs.get("language_code", "es")},
            "components": kwargs.get("components", [])
        }
    
    # Mensaje con imagen (por URL)
    elif message_type == "image" and "image_url" in kwargs:
        payload["type"] = "image"
        payload["image"] = {
            "link": kwargs.get("image_url"),
            "caption": message # Opcional: texto debajo de la imagen
        }
        
    # Mensaje con imagen (por ID subido)
    elif message_type == "image" and "image_id" in kwargs:
         payload["type"] = "image"
         payload["image"] = {
             "id": kwargs.get("image_id"),
             "caption": message
         }
    
    # Otros tipos de mensaje (para futura implementación)
    else:
        logger.error(f"Tipo de mensaje no soportado o faltan argumentos: {message_type}")
        return {
            "success": False,
            "error": f"Tipo de mensaje no soportado o faltan argumentos: {message_type}",
            "to": to
        }
    
    try:
        # Usar httpx.AsyncClient para la solicitud
        async with httpx.AsyncClient(timeout=settings.HTTPX_TIMEOUT) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status() # Lanza excepción para errores HTTP >= 400
            response_data = response.json()

            # Meta API devuelve 200 OK incluso si hay errores a nivel de mensaje
            if "messages" in response_data and response_data["messages"]:
                message_id = response_data["messages"][0].get("id")
                logger.info(f"Mensaje enviado con éxito a {to}. Respuesta de Meta: {response_data}")
                return {
                    "success": True,
                    "message_id": message_id,
                    "to": to
                }
            elif "error" in response_data:
                 error_details = response_data["error"]
                 error_message = error_details.get("message", "Error desconocido")
                 logger.error(f"Error de API Meta al enviar a {to}: {error_message} (Code: {error_details.get('code')}, Subcode: {error_details.get('error_subcode')}, FBTrace: {error_details.get('fbtrace_id')}) ")
                 return {
                     "success": False,
                     "error": error_message,
                     "details": error_details, # Incluir detalles del error
                     "to": to
                 }
            else:
                # Respuesta 200 pero inesperada
                 logger.error(f"Respuesta inesperada de Meta API (200 OK) al enviar a {to}: {response_data}")
                 return {
                     "success": False,
                     "error": "Respuesta inesperada de la API",
                     "details": response_data,
                     "to": to
                 }

    except httpx.HTTPStatusError as e:
        # Error HTTP (4xx, 5xx)
        error_message = f"Error HTTP {e.response.status_code}"
        details = e.response.text
        try:
             # Intentar parsear el JSON del error
             error_data = e.response.json()
             if "error" in error_data:
                  error_message = error_data["error"].get("message", error_message)
                  details = error_data["error"] # Guardar el objeto de error completo
        except json.JSONDecodeError:
             pass # Mantener el texto plano si no es JSON

        logger.error(f"Error HTTP al enviar mensaje a {to}: {error_message}. Detalles: {details}")
        return {
            "success": False,
            "error": error_message,
            "details": details,
            "to": to
        }
        
    except httpx.RequestError as e:
         # Errores de conexión, timeout, etc.
         logger.error(f"Error de red/conexión al enviar mensaje a {to}: {e}")
         return {"success": False, "error": f"Error de conexión: {str(e)}", "to": to}

    except Exception as e:
        logger.error(f"Excepción inesperada al enviar mensaje a {to}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Excepción inesperada: {str(e)}",
            "to": to
        }

def verify_meta_webhook_signature(request_body: bytes, signature: str) -> bool:
    """
    Verifica la firma de un webhook de Meta (usando el App Secret).

    Args:
        request_body: Cuerpo de la solicitud en bytes.
        signature: Valor de la cabecera X-Hub-Signature-256.

    Returns:
        True si la firma es válida, False en caso contrario.
    """
    logger.debug(f"Verificando firma de webhook: {signature[:15]}...")
    
    # Si no hay firma o está vacía, rechazar
    if not signature or not signature.startswith('sha256='):
        logger.warning("Firma de webhook inválida o ausente")
        return False
    
    # Obtener el App Secret de la configuración
    app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None)
    
    # Para entorno de desarrollo, podemos aceptar todas las solicitudes
    # ¡SOLO PARA DESARROLLO!
    if getattr(settings, "ENVIRONMENT", "development") == "development" and not app_secret:
        logger.warning("Aceptando firma sin verificar (modo desarrollo)")
        return True
    
    # En producción, verificar siempre la firma
    if not app_secret:
        logger.error("WHATSAPP_APP_SECRET no está configurado")
        return False
    
    # Calcular el hash HMAC-SHA256 del cuerpo de la solicitud
    try:
        expected_hash = hmac.new(
            app_secret.encode('utf-8'),
            msg=request_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Extraer el hash de la firma (quitar 'sha256=')
        received_hash = signature.split('=')[1]
        
        # Comparar los hashes (comparación segura)
        result = hmac.compare_digest(expected_hash, received_hash)
        
        if not result:
            logger.warning(f"Verificación de firma fallida. Esperado: {expected_hash[:10]}..., Recibido: {received_hash[:10]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Error al verificar la firma del webhook: {e}")
        return False

async def handle_meta_webhook(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maneja un webhook entrante de Meta para WhatsApp de forma asíncrona.

    Args:
        request_data: Datos JSON de la solicitud del webhook de Meta.

    Returns:
        Diccionario con la respuesta procesada o estado.
    """
    logger.info("Procesando webhook de Meta WhatsApp")
    
    try:
        # Estructura básica de un webhook de Meta:
        # {
        #   "object": "whatsapp_business_account",
        #   "entry": [{
        #     "id": "WHATSAPP_BUSINESS_ACCOUNT_ID", 
        #     "changes": [{
        #       "value": {
        #         "messaging_product": "whatsapp",
        #         "metadata": {...},
        #         "contacts": [...],
        #         "messages": [{...}]
        #       },
        #       "field": "messages"
        #     }]
        #   }]
        # }
        
        # Verificar estructura básica del webhook
        if request_data.get("object") != "whatsapp_business_account":
            logger.warning(f"Objeto de webhook inesperado: {request_data.get('object')}")
            return {"status": "ignored", "reason": "Tipo de objeto no es whatsapp_business_account"}
        
        if not request_data.get("entry") or not isinstance(request_data["entry"], list):
            logger.warning("Estructura 'entry' faltante o inválida en webhook")
            return {"status": "ignored", "reason": "Estructura 'entry' inválida"}
        
        # Procesar cada entrada (normalmente solo hay una)
        processing_results = [] # Almacenar resultados de procesamiento
        
        for entry in request_data["entry"]:
            entry_id = entry.get("id")
            
            # Verificar si hay cambios que procesar
            if not entry.get("changes") or not isinstance(entry["changes"], list):
                continue
            
            # Procesar cada cambio
            for change in entry["changes"]:
                # Solo nos interesan los cambios en 'messages'
                if change.get("field") != "messages":
                    continue
                
                value = change.get("value", {})
                
                # Verificar si hay mensajes para procesar
                if not value.get("messages") or not isinstance(value["messages"], list):
                    continue
                
                # Obtener contactos
                contacts = value.get("contacts", [])
                contact_info = contacts[0] if contacts else {}
                
                # Obtener metadatos
                metadata = value.get("metadata", {})
                display_phone_number = metadata.get("display_phone_number")
                phone_number_id = metadata.get("phone_number_id")
                
                # Procesar cada mensaje
                for message in value["messages"]:
                    message_id = message.get("id")
                    from_number = message.get("from")
                    timestamp = message.get("timestamp")
                    message_type = message.get("type")
                    
                    # Crear objeto de datos del mensaje
                    message_data = {
                        "success": True,
                        "id": message_id,
                        "from": from_number,
                        "timestamp": timestamp,
                        "type": message_type,
                        "contact_name": contact_info.get("profile", {}).get("name", "Usuario"),
                        "wa_id": contact_info.get("wa_id"),
                        "display_phone_number": display_phone_number,
                        "phone_number_id": phone_number_id
                    }
                    
                    # Extraer contenido según el tipo de mensaje
                    if message_type == "text":
                        text_body = message.get("text", {}).get("body")
                        if text_body:
                            logger.info(f"Mensaje de texto de {contact_info.get('profile', {}).get('name', 'Usuario')} ({from_number}): {text_body}")
                            messages = [{"role": "user", "content": text_body}]
                            ai_response = await generate_chat_response(messages)
                            if ai_response.get("success"):
                                respuesta_ia = ai_response["message"]["content"]
                                logger.info(f"Respuesta generada por la IA: {respuesta_ia}")
                                await send_whatsapp_message(from_number, respuesta_ia)
                                return {"success": True, "action": "ia_response_sent", "from": from_number}
                            else:
                                logger.error(f"Error al generar respuesta IA: {ai_response.get('error')}")
                                await send_whatsapp_message(from_number, "Lo siento, no pude procesar tu mensaje en este momento.")
                                return {"success": False, "error": "ia_generation_failed", "from": from_number}
                        else:
                            logger.error(f"No se pudo extraer el cuerpo del mensaje de texto de {from_number}")
                            await send_whatsapp_message(from_number, "No se pudo leer tu mensaje. Por favor, intenta de nuevo.")
                            return {"success": False, "error": "no_text_body", "from": from_number}
                    elif message_type == "image":
                        message_data["media_id"] = message.get("image", {}).get("id")
                        message_data["media_url"] = message.get("image", {}).get("url")
                        message_data["media_mime_type"] = message.get("image", {}).get("mime_type")
                        message_data["caption"] = message.get("image", {}).get("caption")
                    elif message_type == "audio":
                        message_data["media_id"] = message.get("audio", {}).get("id")
                        message_data["media_url"] = message.get("audio", {}).get("url")
                        message_data["media_mime_type"] = message.get("audio", {}).get("mime_type")
                    elif message_type == "document":
                        message_data["media_id"] = message.get("document", {}).get("id")
                        message_data["media_url"] = message.get("document", {}).get("url")
                        message_data["media_mime_type"] = message.get("document", {}).get("mime_type")
                        message_data["filename"] = message.get("document", {}).get("filename")
                    elif message_type == "button":
                        message_data["button_payload"] = message.get("button", {}).get("payload")
                        message_data["button_text"] = message.get("button", {}).get("text")
                    else:
                        message_data["unsupported_type"] = True
                    
                    # Marcar mensaje como leído (opcional)
                    # Esto debería implementarse como una función separada
                    
                    # Aquí se procesaría el mensaje y se generaría una respuesta
                    # Ejemplo simplificado:
                    if message_type == "text" and message_data.get("body"):
                        logger.info(f"Mensaje de texto recibido de {from_number}: {message_data.get('body')}")
                        # Llamar a la lógica principal de procesamiento y respuesta
                        await process_incoming_message(message_data, value)
                    
                    processing_results.append(message_data)
        
        if processing_results:
            logger.info(f"Procesados {len(processing_results)} mensajes del webhook")
            return {
                "status": "processed",
                "count": len(processing_results),
                "messages": processing_results
            }
        else:
            logger.info("No se encontraron mensajes para procesar en el webhook")
            return {"status": "no_messages"}
            
    except Exception as e:
        logger.error(f"Error al procesar webhook de Meta: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

async def send_auto_response(to: str, incoming_message: str):
    """
    Envía una respuesta automática simple (ej. "Mensaje recibido").
    Ahora es asíncrono porque llama a send_whatsapp_message.
    """
    response_text = f"Hemos recibido tu mensaje: '{incoming_message[:50]}...'\nPronto te contactaremos."
    logger.info(f"Enviando respuesta automática a {to}")
    # Usar el wrapper send_whatsapp_message que ahora es async
    await send_whatsapp_message(to, response_text)

async def download_media_meta(media_id: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Descarga un archivo multimedia desde la API de Meta usando su ID.

    Args:
        media_id: El ID del medio proporcionado por Meta.

    Returns:
        Una tupla: (contenido_en_bytes, content_type) o (None, None) si hay error.
    """
    logger.info(f"Intentando descargar media con ID: {media_id}")
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", None)
    if not access_token:
        logger.error("Falta WHATSAPP_ACCESS_TOKEN para descargar media")
        return None, None

    # 1. Obtener la URL del medio
    url_info_api = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    media_url = None
    mime_type = None
    
    try:
        async with httpx.AsyncClient(timeout=settings.HTTPX_TIMEOUT) as client:
            response_info = await client.get(url_info_api, headers=headers)
            response_info.raise_for_status()
            media_info = response_info.json()
            media_url = media_info.get("url")
            mime_type = media_info.get("mime_type") # Capturar mime_type
            sha256_hash = media_info.get("sha256") # Capturar hash si se quiere verificar
            file_size = media_info.get("file_size")
            
            if not media_url:
                logger.error(f"No se pudo obtener la URL para media ID {media_id}. Respuesta: {media_info}")
                return None, None
            logger.info(f"URL obtenida para media ID {media_id}: {media_url[:50]}... (Type: {mime_type}, Size: {file_size})")

    except httpx.HTTPStatusError as e:
         logger.error(f"Error HTTP {e.response.status_code} al obtener info de media {media_id}: {e.response.text}")
         return None, None
    except httpx.RequestError as e:
         logger.error(f"Error de conexión al obtener info de media {media_id}: {e}")
         return None, None
    except Exception as e:
         logger.exception(f"Excepción al obtener info de media {media_id}: {e}")
         return None, None

    # 2. Descargar el contenido del medio desde la URL obtenida
    if not media_url:
         return None, None
         
    try:
         # Nota: La URL devuelta por Meta requiere el mismo token de autorización
         async with httpx.AsyncClient(timeout=settings.HTTPX_TIMEOUT) as download_client:
             # Usar stream=True si el archivo es grande, pero para muchos casos .content es suficiente
             # response_download = await download_client.get(media_url, headers=headers, follow_redirects=True)
             # response_download.raise_for_status()
             # content = await response_download.aread() # Leer contenido asíncronamente
             
             # Forma más simple si los archivos no son enormes:
             response_download = await download_client.get(media_url, headers=headers, follow_redirects=True)
             response_download.raise_for_status()
             content = response_download.content # Leer contenido (bloqueante si es grande, pero httpx maneja bien) 

             logger.info(f"Media {media_id} descargada con éxito ({len(content)} bytes). Content-Type original: {mime_type}")
             # Podríamos verificar el hash sha256 aquí si es necesario
             return content, mime_type # Devolver también el content_type
             
    except httpx.HTTPStatusError as e:
         logger.error(f"Error HTTP {e.response.status_code} al descargar media desde {media_url[:50]}...: {e.response.text}")
         return None, None
    except httpx.RequestError as e:
         logger.error(f"Error de conexión al descargar media desde {media_url[:50]}...: {e}")
         return None, None
    except Exception as e:
         logger.exception(f"Excepción al descargar media {media_id}: {e}")
         return None, None

async def process_incoming_message(message_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un mensaje entrante individual recibido del webhook.
    Ahora es asíncrono para poder llamar a otras funciones async.
    """
    message_id = message_data.get("id")
    from_number = message_data.get("from")
    timestamp = message_data.get("timestamp")
    message_type = message_data.get("type")
    
    logger.info(f"Procesando mensaje entrante {message_id} de {from_number} (Tipo: {message_type})")
    
    # Extraer detalles del contacto si están presentes
    contact_info = next((c for c in metadata.get("contacts", []) if c.get("wa_id") == from_number), None)
    contact_name = contact_info.get("profile", {}).get("name", "Desconocido") if contact_info else "Desconocido"
    
    # Lógica de procesamiento según el tipo de mensaje
    
    # Mensaje de texto
    if message_type == "text":
        text_body = message_data.get("text", {}).get("body")
        if text_body:
            logger.info(f"Mensaje de texto de {contact_name} ({from_number}): {text_body}")
            messages = [{"role": "user", "content": text_body}]
            ai_response = await generate_chat_response(messages)
            if ai_response.get("success"):
                respuesta_ia = ai_response["message"]["content"]
                logger.info(f"Respuesta generada por la IA: {respuesta_ia}")
                await send_whatsapp_message(from_number, respuesta_ia)
                return {"success": True, "action": "ia_response_sent", "from": from_number}
            else:
                logger.error(f"Error al generar respuesta IA: {ai_response.get('error')}")
                await send_whatsapp_message(from_number, "Lo siento, no pude procesar tu mensaje en este momento.")
                return {"success": False, "error": "ia_generation_failed", "from": from_number}
        else:
            logger.error(f"No se pudo extraer el cuerpo del mensaje de texto de {from_number}")
            await send_whatsapp_message(from_number, "No se pudo leer tu mensaje. Por favor, intenta de nuevo.")
            return {"success": False, "error": "no_text_body", "from": from_number}

    # Mensaje de imagen
    elif message_type == "image":
        image_data = message_data.get("image", {})
        media_id = image_data.get("id")
        caption = image_data.get("caption", "")
        logger.info(f"Mensaje de imagen recibido de {from_number}. Media ID: {media_id}, Caption: {caption}")
        
        if media_id:
            # Descargar la imagen (llamada asíncrona)
            image_bytes, mime_type = await download_media_meta(media_id)
            if image_bytes:
                logger.info(f"Imagen {media_id} descargada ({len(image_bytes)} bytes, tipo: {mime_type}). Procesamiento adicional pendiente.")
                # Aquí podrías guardar la imagen, enviarla a otro servicio, etc.
                # Ejemplo: save_image_to_s3(image_bytes, f"{from_number}_{media_id}.jpg")
                await send_whatsapp_message(from_number, f"Recibí tu imagen (tipo: {mime_type}).")
                return {"success": True, "action": "image_downloaded", "media_id": media_id, "from": from_number}
            else:
                logger.error(f"No se pudo descargar la imagen con ID {media_id}")
                await send_whatsapp_message(from_number, "Hubo un problema al descargar tu imagen.")
                return {"success": False, "error": "image_download_failed", "media_id": media_id, "from": from_number}
        else:
             logger.warning(f"Mensaje de imagen sin media ID de {from_number}")
             return {"success": False, "error": "missing_media_id", "from": from_number}

    # Mensaje interactivo (respuesta a botón o lista)
    elif message_type == "interactive":
         interactive_data = message_data.get("interactive", {})
         interactive_type = interactive_data.get("type")
         logger.info(f"Mensaje interactivo recibido de {from_number} (Tipo: {interactive_type})")
         # Procesar button_reply, list_reply, etc.
         # response_text = f"Recibí tu selección interactiva: {interactive_data}"
         # await send_whatsapp_message(from_number, response_text)
         return {"success": True, "action": "interactive_processed", "interactive_type": interactive_type, "from": from_number}
         
    # Otros tipos (audio, video, documento, location, contacts, etc.)
    else:
        logger.info(f"Recibido mensaje de tipo '{message_type}' de {from_number}. Procesamiento no implementado.")
        # await send_whatsapp_message(from_number, f"Recibí tu mensaje de tipo {message_type}, aún no puedo procesarlo.")
        return {"success": True, "action": "type_unsupported", "message_type": message_type, "from": from_number}

# Wrapper simple para enviar mensajes (ahora asíncrono)
async def send_whatsapp_message(to: str, message: str) -> Dict[str, Any]:
    """Función wrapper asíncrona para enviar mensajes de texto simples vía Meta."""
    # Llama a la función principal de Meta (que ahora es async)
    return await send_whatsapp_message_meta(to=to, message=message, message_type="text")

