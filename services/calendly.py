"""
Servicio de integración con Calendly para gestión de citas.
Permite obtener horarios disponibles y programar citas.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx

from core.config import settings

logger = logging.getLogger("mark-assistant.calendly")

# Configurar cabeceras para API de Calendly
def get_headers() -> Dict[str, str]:
    """
    Obtiene las cabeceras para la API de Calendly
    
    Returns:
        Diccionario con cabeceras API
    """
    return {
        "Authorization": f"Bearer {settings.CALENDLY_API_KEY}",
        "Content-Type": "application/json"
    }

async def get_user_info() -> Dict[str, Any]:
    """
    Obtiene información del usuario de Calendly
    
    Returns:
        Información del usuario
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CALENDLY_API_URL}/users/me",
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
    
    except Exception as e:
        logger.error(f"Error al obtener información del usuario de Calendly: {e}")
        return {}

async def get_user_event_types(user_uri: str) -> List[Dict[str, Any]]:
    """
    Obtiene los tipos de eventos disponibles para un usuario
    
    Args:
        user_uri: URI del usuario en Calendly
    
    Returns:
        Lista de tipos de eventos
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CALENDLY_API_URL}/event_types",
                params={"user": user_uri},
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
    
    except Exception as e:
        logger.error(f"Error al obtener tipos de eventos: {e}")
        return []

async def _fetch_calendly_slots_for_event_type(
    event_type_uri: str,
    start_time: str,
    end_time: str,
    timezone: str = "Europe/Madrid"
) -> List[Dict[str, Any]]:
    """
    Obtiene los slots disponibles para un tipo de evento
    
    Args:
        event_type_uri: URI del tipo de evento
        start_time: Fecha y hora de inicio (ISO 8601)
        end_time: Fecha y hora de fin (ISO 8601)
        timezone: Zona horaria
    
    Returns:
        Lista de slots disponibles
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CALENDLY_API_URL}/event_type_available_times",
                params={
                    "event_type": event_type_uri,
                    "start_time": start_time,
                    "end_time": end_time,
                    "timezone": timezone
                },
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
    
    except Exception as e:
        logger.error(f"Error al obtener slots disponibles: {e}")
        return []

async def schedule_event(
    event_type_uri: str,
    start_time: str,
    name: str,
    email: str,
    phone: Optional[str] = None,
    timezone: str = "Europe/Madrid",
    questions_answers: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Programa un evento en Calendly
    
    Args:
        event_type_uri: URI del tipo de evento
        start_time: Fecha y hora de inicio (ISO 8601)
        name: Nombre del invitado
        email: Email del invitado
        phone: Teléfono del invitado (opcional)
        timezone: Zona horaria
        questions_answers: Respuestas a preguntas personalizadas (opcional)
    
    Returns:
        Información del evento programado
    """
    # Crear payload para la solicitud
    payload = {
        "event_type": event_type_uri,
        "start_time": start_time,
        "timezone": timezone,
        "invitee": {
            "name": name,
            "email": email
        }
    }
    
    # Añadir teléfono si está presente
    if phone:
        payload["invitee"]["phone_number"] = phone
    
    # Añadir respuestas a preguntas si están presentes
    if questions_answers:
        payload["questions_and_answers"] = questions_answers
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CALENDLY_API_URL}/scheduling_invitees",
                json=payload,
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
    
    except Exception as e:
        logger.error(f"Error al programar evento: {e}")
        return {"error": str(e)}

async def cancel_event(event_uri: str, reason: Optional[str] = None) -> bool:
    """
    Cancela un evento programado
    
    Args:
        event_uri: URI del evento
        reason: Motivo de la cancelación (opcional)
    
    Returns:
        True si se canceló correctamente, False en caso contrario
    """
    payload = {}
    if reason:
        payload["reason"] = reason
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CALENDLY_API_URL}/scheduling_cancellations",
                json={"event": event_uri, **payload},
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return True
    
    except Exception as e:
        logger.error(f"Error al cancelar evento: {e}")
        return False

async def get_event(event_uri: str) -> Dict[str, Any]:
    """
    Obtiene información de un evento
    
    Args:
        event_uri: URI del evento
    
    Returns:
        Información del evento
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CALENDLY_API_URL}/events/{event_uri}",
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
    
    except Exception as e:
        logger.error(f"Error al obtener información del evento: {e}")
        return {}

async def get_invitee(invitee_uri: str) -> Dict[str, Any]:
    """
    Obtiene información de un invitado
    
    Args:
        invitee_uri: URI del invitado
    
    Returns:
        Información del invitado
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CALENDLY_API_URL}/invitees/{invitee_uri}",
                headers=get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
    
    except Exception as e:
        logger.error(f"Error al obtener información del invitado: {e}")
        return {}

# Funciones de utilidad para la interfaz del asistente Mark
async def get_available_slots(
    start_date: str,
    end_date: str,
    therapist_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene los slots disponibles en un rango de fechas
    
    Args:
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
        therapist_id: ID del terapeuta (opcional)
    
    Returns:
        Lista de slots disponibles formateados
    """
    # Convertir fechas a objetos datetime
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Verificar que el rango sea válido
    if start > end:
        logger.error(f"Rango de fechas inválido: {start_date} - {end_date}")
        return []
    
    # Limitar el rango a 30 días
    if (end - start).days > 30:
        end = start + timedelta(days=30)
        logger.warning(f"Rango de fechas limitado a 30 días: {start.isoformat()} - {end.isoformat()}")
    
    # Convertir a formato ISO 8601
    start_time = start.isoformat() + "Z"  # UTC
    end_time = end.isoformat() + "Z"      # UTC
    
    try:
        # Obtener información del usuario
        user_info = await get_user_info()
        user_uri = user_info.get("resource", {}).get("uri", "")
        
        if not user_uri:
            logger.error("No se pudo obtener URI del usuario de Calendly")
            return []
        
        # Obtener tipos de eventos
        event_types = await get_user_event_types(user_uri)
        
        if not event_types:
            logger.error("No se encontraron tipos de eventos")
            return []
        
        # Filtrar por terapeuta si está especificado
        if therapist_id:
            event_types = [et for et in event_types if therapist_id in et.get("name", "")]
        
        # Obtener slots disponibles para cada tipo de evento
        all_slots = []
        for event_type in event_types:
            if not event_type.get("active"):
                continue
            
            event_type_uri = event_type["uri"]
            slots = await _fetch_calendly_slots_for_event_type(event_type_uri, start_time, end_time)
            
            # Formatear y añadir slots
            for slot in slots:
                all_slots.append({
                    "start_time": slot.get("start_time"),
                    "end_time": slot.get("end_time"),
                    "therapist_name": event_type.get("name"),
                    "event_type_uri": event_type_uri
                })
        
        return all_slots
    
    except Exception as e:
        logger.error(f"Error al obtener slots disponibles (Mark): {e}")
        return []

async def schedule_appointment(
    slot_id: str,
    event_type_uri: str,
    patient_name: str,
    patient_email: str,
    patient_phone: Optional[str] = None,
    appointment_type: str = "initial",
    meeting_format: str = "online",
    questions_answers: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Programa una cita usando la API de Calendly.
    
    Args:
        slot_id: Hora de inicio del slot seleccionado (ISO 8601).
        event_type_uri: URI del tipo de evento de Calendly.
        patient_name: Nombre del paciente.
        patient_email: Email del paciente.
        patient_phone: Teléfono del paciente (opcional).
        appointment_type: Tipo de cita (ej: 'initial', 'follow-up') - no usado por Calendly directamente.
        meeting_format: Formato de la cita (ej: 'online', 'in-person') - no usado por Calendly directamente.
        questions_answers: Respuestas a preguntas personalizadas.
        
    Returns:
        Respuesta de la API de Calendly o diccionario de error.
    """
    try:
        # El 'slot_id' aquí es el 'start_time' que necesita 'schedule_event'
        # 'name' y 'email' son 'patient_name' y 'patient_email'
        # 'event_type_uri' se pasa directamente
        response = await schedule_event(
            event_type_uri=event_type_uri,
            start_time=slot_id,
            name=patient_name,
            email=patient_email,
            phone=patient_phone,
            questions_answers=questions_answers
        )
        
        if "error" in response:
            logger.error(f"Error devuelto por Calendly al programar: {response['error']}")
        elif response.get("resource", {}).get("uri"):
            logger.info(f"Cita programada exitosamente: {response['resource']['uri']}")
        else:
            logger.warning(f"Respuesta inesperada de Calendly al programar: {response}")
            
        return response
        
    except Exception as e:
        logger.error(f"Error al programar cita (Mark): {e}")
        return {"error": str(e), "details": "Error interno del asistente"}

# TODO: Revisar si hay más funciones que necesiten ser async o si 'json' se usa.
# TODO: Considerar si 'get_available_slots_for_day' y otras son necesarias o redundantes.

# (El resto del archivo, si existe, no fue modificado) 