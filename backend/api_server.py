"""
Servidor API principal que maneja la lógica del webhook de WhatsApp,
la interacción con el LLM y otras funcionalidades backend.
"""
# import logging # No usado
import os
# import time # No usado
import json
import uuid
from datetime import datetime #, timedelta # No usado
from typing import Dict, Any, Optional #, List, Annotated, Tuple # List, Annotated, Tuple no usadas

# from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Query, Depends, Form, Header, Body, APIRouter, status, Security, Response, WebSocket, WebSocketDisconnect, Middleware # FastAPI, Middleware no usadas directamente; APIRouter ya está importado
from fastapi import Request, HTTPException, BackgroundTasks, Query, Depends, Form, Header, Body, APIRouter, status, Security, Response, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware # No usado
# from dotenv import load_dotenv # No usado
from pydantic import BaseModel, Field, ValidationError
import httpx
import pytz

# Configuración y logging
from core.config import settings, logger

# Cliente LLM (asumiendo que está en ai/llm_client.py)
try:
    # from ai.llm_client import generate_chat_response
    # Mover esto a una importación explícita donde se usa si no se ha hecho ya
    pass
except ImportError:
    logger.error("No se pudo importar 'generate_chat_response' desde ai.llm_client.py")
    # generate_chat_response = None # O manejar de otra forma

# Detección de idioma
from ai.language_utils import detect_language, LANGDETECT_AVAILABLE

# Cliente de Base de Datos
from database.d1_client import (
    get_patient_by_phone, insert_patient, update_patient,
    # get_patient_by_id, # Eliminado
    get_patient_by_email,
    get_session_data, save_session_data, delete_expired_sessions,
    insert_notification, get_pending_notifications, update_notification_status,
    get_system_config,
    insert_appointment, get_appointment_by_calendly_uri, update_appointment_status
)

# Servicios
from services.whatsapp import send_whatsapp_message, send_whatsapp_message_meta, verify_meta_webhook_signature, handle_meta_webhook, download_media_meta
# from services.calendly import get_available_slots, schedule_appointment # Eliminado
from services.zoom import get_meeting_details, cancel_zoom_meeting, ZOOM_OAUTH_TOKEN_URL
# from services.stripe import generate_payment_link, check_payment_status # Eliminado

# Traducciones
from i18n import get_message

# --- Configuración del Router ---
apirouter = APIRouter(prefix="/api", tags=["API"])

# --- Estados de Sesión (Ahora en Base de Datos) ---
# SESSION_STORE = {}

# --- Definición de Modelos (si no están en otro lugar) ---
# ... (Modelos Pydantic para Requests/Responses) ...
class CalendlyPayload(BaseModel):
    event: str
    payload: Dict[str, Any]

class PatientUpdatePayload(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None
    # Añade otros campos actualizables de tu tabla 'patients' aquí
    # No incluyas 'phone' directamente si requiere lógica especial (normalización)
    # o maneja la normalización en el endpoint.
    # Ejemplo:
    # metadata: Optional[Dict[str, Any]] = None 

# --- Funciones Auxiliares ---

async def get_translation(language: str, key: str, **kwargs) -> str:
    # ... (código existente)
    ...

async def get_or_create_session(phone_number: str) -> Dict[str, Any]:
    # ... (código existente)
    ...

async def process_message(phone_number: str, message_text: str, session_data: Dict[str, Any]):
    # ... (código existente)
    ...

async def handle_audio_message(phone_number: str, media_id: str, session_data: Dict[str, Any]):
    # ... (código existente)
    ...

# --- Endpoints API ---

@apirouter.get("/health")
async def health_check():
    # ... (código existente)
    ...

@apirouter.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(request: Request):
    # ... (código existente)
    ...

@apirouter.post("/whatsapp/webhook")
async def receive_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    # ... (código existente)
    ...

# --- Endpoints eliminados (Calendly / Stripe / etc.) ---
# @apirouter.post("/calendly/webhook")
# async def calendly_webhook(payload: CalendlyPayload, background_tasks: BackgroundTasks):
#     ...

# --- Endpoints Admin (si no están en admin_panel.py) ---
# @apirouter.get("/admin/sessions") -> para depuración, quizá quitar
# async def get_all_sessions():
#     ...

@apirouter.post("/admin/cleanup_sessions", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_expired_sessions():
    # ... (código existente)
    ...

# @apirouter.post("/payment/create-link")
# async def create_payment_link_endpoint(category: str = Query("standard")):
#     ...

# @apirouter.get("/payment/status/{session_id}")
# async def check_payment_status_endpoint(session_id: str):
#     ...

@apirouter.post("/notify/emergency")
async def notify_emergency(
    patient_id: Optional[str] = None,
    phone: Optional[str] = None,
    message: str = "Solicitud de atención urgente",
    background_tasks: BackgroundTasks = None
):
    """Envía una notificación de emergencia (ej. a Dina)."""
    if not settings.EMERGENCY_CONTACT:
        logger.error("EMERGENCY_CONTACT no está configurado, no se puede notificar.")
        raise HTTPException(status_code=500, detail="Contacto de emergencia no configurado")
        
    notification_text = f"¡URGENTE! {message}\n"
    if patient_id:
        notification_text += f"Paciente ID: {patient_id}\n"
    if phone:
        notification_text += f"Teléfono: {phone}\n"
    
    logger.info(f"Enviando notificación de emergencia a {settings.EMERGENCY_CONTACT}")
    
    async def send_notification_task():
         await send_whatsapp_message(settings.EMERGENCY_CONTACT, notification_text)
         
    if background_tasks:
         background_tasks.add_task(send_notification_task)
         return {"status": "Notification task added to background"}
    else:
         await send_notification_task()
         return {"status": "Notification sent directly"}

@apirouter.get("/appointments/available")
async def get_available_appointments(
    start_date: str,
    end_date: str,
    therapist_id: Optional[str] = None
):
    """Obtiene slots disponibles de Calendly (requiere refactorizar service a async)."""
    raise HTTPException(status_code=501, detail="Funcionalidad de Calendly pendiente de refactorización async")

@apirouter.post("/appointments/schedule")
async def schedule_appointment_endpoint(
    patient_id: str,
    slot_id: str,
    appointment_type: str = "initial",
    format: str = "online"
):
    """Programa una cita en Calendly (requiere refactorizar service a async)."""
    raise HTTPException(status_code=501, detail="Funcionalidad de Calendly pendiente de refactorización async")

@apirouter.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Endpoint para recibir webhooks de Stripe."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Falta cabecera Stripe-Signature")
        
    from services.stripe import handle_stripe_webhook 
    result = await handle_stripe_webhook(payload, sig_header)
    
    if result.get("success"):
        return JSONResponse(content={"status": "received", "result": result}, status_code=200)
    else:
        status_code = 400 if "Firma inválida" in result.get("error","") or "Payload inválido" in result.get("error","") else 500
        logger.error(f"Error procesando webhook de Stripe: {result.get('error')}")
        response_status = 200 if status_code == 500 else status_code 
        return JSONResponse(content={"status": "error", "detail": result.get("error")}, status_code=response_status)

@apirouter.post("/api/calendly/webhook")
async def calendly_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook para eventos de Calendly (ej: cita creada, cancelada).
    Crea una reunión de Zoom para nuevas citas y la cancela si la cita se cancela.
    """
    webhook_payload = {} 
    try:
        webhook_payload = await request.json()
        event_type = webhook_payload.get("event")
        payload_data = webhook_payload.get("payload", {})

        logger.info(f"Webhook de Calendly recibido: Evento '{event_type}'")
        # logger.debug(f"Payload Calendly: {json.dumps(webhook_payload, indent=2)}")

        # --- Procesar creación de cita ---
        if event_type == "invitee.created":
            logger.info("Procesando evento 'invitee.created' de Calendly.")
            
            scheduled_event = payload_data.get("scheduled_event", {})
            invitee = payload_data.get("invitee", {})
            
            start_time_str = scheduled_event.get("start_time")
            calendly_event_uri = scheduled_event.get("uri") # URI del evento agendado
            calendly_invitee_uri = invitee.get("uri")      # URI del invitado específico
            invitee_name = invitee.get("name")
            invitee_email = invitee.get("email")
            
            if not all([start_time_str, invitee_name, invitee_email, calendly_event_uri, calendly_invitee_uri]):
                logger.warning("Payload 'invitee.created' incompleto. Faltan datos clave.")
                return Response(status_code=status.HTTP_200_OK)

            try:
                meeting_start_time_naive = datetime.fromisoformat(start_time_str.replace("Z", ""))
                meeting_start_time_utc = pytz.utc.localize(meeting_start_time_naive)

                # 1. Buscar paciente asociado por email
                patient_id = None
                patient_phone = None
                patient_lang = settings.DEFAULT_LANGUAGE
                patient_result = await get_patient_by_email(invitee_email)
                if patient_result.get("success"):
                    patient_data = patient_result.get("patient", {})
                    patient_id = patient_data.get("id")
                    patient_phone = patient_data.get("phone")
                    patient_lang = patient_data.get("language", settings.DEFAULT_LANGUAGE)
                    logger.info(f"Paciente encontrado (ID: {patient_id}) para email {invitee_email}")
                else:
                    logger.warning(f"No se encontró paciente con email {invitee_email}. La cita se guardará sin asociación directa.")

                # 2. Insertar/Actualizar registro de la cita en la BD
                appointment_insert_res = await insert_appointment(
                    calendly_event_uri=calendly_event_uri,
                    calendly_invitee_uri=calendly_invitee_uri,
                    scheduled_at=meeting_start_time_utc,
                    invitee_name=invitee_name,
                    invitee_email=invitee_email,
                    patient_id=patient_id
                )
                if not appointment_insert_res.get("success"):
                    logger.error("No se pudo guardar la información de la cita en la base de datos.")
                
                # 3. Crear reunión de Zoom
                topic = f"Consulta Psicológica - {invitee_name}"
                duration = 60 
                logger.info(f"Intentando crear reunión Zoom para '{invitee_name}' ({invitee_email})")
                zoom_result = await create_zoom_meeting(
                    topic=topic,
                    start_time=meeting_start_time_utc,
                    duration_minutes=duration,
                    timezone="UTC"
                )

                if zoom_result.get("success"):
                    meeting_data = zoom_result.get("meeting", {})
                    join_url = meeting_data.get("join_url")
                    meeting_id = meeting_data.get("id")
                    logger.info(f"Reunión Zoom creada: ID {meeting_id}. URL: {join_url}")
                    
                    # 4. Actualizar la cita en la BD con los detalles de Zoom
                    update_success = await update_appointment_zoom_details(
                        calendly_event_uri=calendly_event_uri,
                        zoom_meeting_id=str(meeting_id), 
                        zoom_join_url=join_url
                    )
                    if not update_success:
                        logger.error(f"Fallo al guardar detalles de Zoom en BD para cita {calendly_event_uri}")
                    
                    # 5. Enviar notificación WhatsApp si se encontró el teléfono
                    if patient_phone:
                        message_text = get_message("zoom_link_notification", patient_lang).format(
                            name=invitee_name, 
                            date=meeting_start_time_utc.strftime("%d/%m/%Y"), 
                            time=meeting_start_time_utc.strftime("%H:%M UTC"), 
                            link=join_url
                        )
                        background_tasks.add_task(send_whatsapp_message, patient_phone, message_text)
                        logger.info(f"Tarea de notificación WhatsApp añadida para {patient_phone}.")
                    else:
                        logger.info("No se envió notificación WhatsApp (paciente o teléfono no encontrado).")

                else:
                    logger.error(f"Fallo al crear reunión Zoom para {invitee_name}: {zoom_result.get('error')}")

            except Exception as e_inner:
                 logger.error(f"Error procesando evento 'invitee.created': {e_inner}", exc_info=True)

        # --- Procesar cancelación de cita ---
        elif event_type == "invitee.canceled":
            logger.info("Procesando evento 'invitee.canceled' de Calendly.")
            
            # Extraer el URI del *invitee* que se cancela, ya que el evento principal puede tener múltiples invitados
            # OJO: Confirma que esta es la clave correcta en el payload de cancelación de Calendly
            invitee_uri_to_cancel = payload_data.get("invitee", {}).get("uri")
            # Alternativamente, si la cancelación afecta a todo el evento:
            # calendly_event_uri_to_cancel = payload_data.get("scheduled_event", {}).get("uri") 

            # Usaremos el URI del evento si el del invitee no está claro en el payload de cancelación
            # (La lógica de búsqueda debería adaptarse según qué URI se use consistentemente)
            calendly_event_uri = payload_data.get("scheduled_event", {}).get("uri")

            if not calendly_event_uri: # Necesitamos al menos el URI del evento para buscar
                logger.warning("Payload 'invitee.canceled' incompleto. No se puede identificar la cita a cancelar.")
                return Response(status_code=status.HTTP_200_OK)
                
            try:
                # 1. Buscar la cita en la BD usando el URI del evento
                appointment_result = await get_appointment_by_calendly_uri(calendly_event_uri)
                
                if appointment_result.get("success"):
                    appointment_data = appointment_result.get("appointment", {})
                    zoom_meeting_id = appointment_data.get("zoom_meeting_id")
                    current_status = appointment_data.get("status")
                    db_appointment_id = appointment_data.get("id") # ID interno de la cita
                    
                    if current_status == 'canceled':
                         logger.info(f"La cita {calendly_event_uri} (ID: {db_appointment_id}) ya estaba marcada como cancelada.")
                    else:
                        # 2. Cancelar reunión de Zoom si existe
                        if zoom_meeting_id:
                            logger.info(f"Intentando cancelar reunión Zoom ID: {zoom_meeting_id} asociada a cita {db_appointment_id}")
                            cancel_result = await cancel_zoom_meeting(zoom_meeting_id)
                            if cancel_result.get("success"):
                                logger.info(f"Reunión Zoom {zoom_meeting_id} cancelada exitosamente.")
                            elif cancel_result.get("error") == "Meeting not found":
                                logger.warning(f"Reunión Zoom {zoom_meeting_id} no encontrada en Zoom (ya cancelada/expirada?), continuando.")
                            else:
                                logger.error(f"Fallo al cancelar reunión Zoom {zoom_meeting_id}: {cancel_result.get('error')}")
                        else:
                            logger.info(f"Cita {calendly_event_uri} (ID: {db_appointment_id}) cancelada, pero no tenía reunión Zoom asociada.")
                    
                        # 3. Actualizar estado de la cita en la BD a 'canceled'
                        update_status_success = await update_appointment_status(calendly_event_uri, "canceled")
                        if not update_status_success:
                             logger.error(f"Fallo al actualizar estado a 'canceled' para cita {calendly_event_uri}")
                             
                else:
                    logger.warning(f"No se encontró la cita con URI {calendly_event_uri} en la base de datos para cancelar.")
                    
            except Exception as e_cancel:
                logger.error(f"Error procesando evento 'invitee.canceled': {e_cancel}", exc_info=True)

        else:
            logger.debug(f"Evento Calendly '{event_type}' recibido pero no manejado.")

        return Response(status_code=status.HTTP_200_OK)

    except json.JSONDecodeError:
        logger.error("Error decodificando JSON del webhook de Calendly.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo inválido.")
    except Exception as e:
        logger.error(f"Error inesperado procesando webhook de Calendly: {e}", exc_info=True)
        return Response(status_code=status.HTTP_200_OK)

@apirouter.on_event("startup")
async def startup_event():
    """Acciones a realizar al iniciar el servidor."""
    logger.info("Iniciando servidor API Mark Assistant...")
    logger.info("Servidor API listo.")

@apirouter.on_event("shutdown")
async def shutdown_event():
    """Acciones a realizar al detener el servidor."""
    logger.info("Deteniendo servidor API Mark Assistant...")
    logger.info("Servidor API detenido.")

# --- Endpoint para actualizar paciente ---
@apirouter.patch("/patients/{patient_id}", tags=["Patients"])
async def api_update_patient(
    patient_id: str,
    update_payload: PatientUpdatePayload
):
    """Actualiza la información de un paciente existente."""
    # Convertir el payload Pydantic a un dict, excluyendo los valores None
    update_data = update_payload.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No se proporcionaron datos para actualizar."
        )
        
    # Llamar a la función de la base de datos
    result = await update_patient(patient_id=patient_id, update_data=update_data)
    
    if result.get("success"):
        return {"status": "success", "patient": result.get("updated_patient", {})} # Devolver datos actualizados si están
    elif result.get("not_found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=result.get("error", "Paciente no encontrado")
        )
    else:
        # Otro error de base de datos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Error interno al actualizar el paciente")
        )
# --- Fin Endpoint para actualizar paciente ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG) 