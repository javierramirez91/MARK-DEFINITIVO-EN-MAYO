# -*- coding: utf-8 -*-
"""
Cliente para interactuar con la base de datos Supabase.
Proporciona funciones asíncronas para gestionar pacientes, sesiones, etc.
"""
import json
from typing import Dict, List, Any, Optional # ASEGURAR QUE Dict, List, etc. están importados
from datetime import datetime, timezone, timedelta

from database.supabase_client import SupabaseClient 
from core.config import logger 

supabase = SupabaseClient()

# Constantes para nombres de tablas
TABLE_AUSENCIAS_TERAPEUTAS = "ausencias_terapeutas"
TABLE_APPOINTMENTS = "appointments"
TABLE_CONFIGURACIONES = "configuraciones"
TABLE_DIAGNOSTICOS_PACIENTES = "diagnosticos_pacientes"
TABLE_DOCUMENTOS = "documentos"
TABLE_FACTURAS = "facturas"
TABLE_HISTORIALES = "historiales"
TABLE_HORARIOS_TERAPEUTAS = "horarios_terapeutas"
TABLE_LOGS_ACTIVIDAD = "logs_actividad"
TABLE_NOTIFICATIONS = "notifications"
TABLE_PACIENTES = "pacientes"
TABLE_PAGOS = "pagos"
TABLE_RELACIONES_FAMILIARES = "relaciones_familiares"
TABLE_RESULTADOS_TESTS = "resultados_tests"
TABLE_TERAPEUTAS = "terapeutas"
TABLE_TESTS_PSICOLOGICOS = "tests_psicologicos"
TABLE_USUARIOS = "usuarios"
TABLE_SESSIONS_CONVERSATION = "sessions" # Para estado de conversación, si es diferente a citas

async def _handle_supabase_response(api_response, function_name: str, table_name: str, return_key_singular: str = "data", return_key_plural: str = "results") -> Dict[str, Any]:
    """Función helper para procesar APIResponse consistentemente."""
    if api_response.error:
        error_message = api_response.error.message if hasattr(api_response.error, 'message') else "Error desconocido de Supabase API"
        error_code = api_response.error.code if hasattr(api_response.error, 'code') else "N/A"
        logger.error(f"Error API Supabase en {function_name} (tabla '{table_name}'): Code={error_code}, Msg='{error_message}'")
        
        # Construir el payload de retorno para error
        # La clave principal para los datos (singular o plural) dependerá de la función
        # Por defecto, 'results' para listas, 'data' para objetos individuales.
        # Si la función espera una clave específica como 'user', 'patient', 'session', etc.,
        # el código llamante la extraerá de 'data' o 'results'.
        # Para simplificar, 'data' contendrá el primer elemento si es singular, 'results' la lista.
        
        payload_error = {
            "success": False, 
            "results": [],      # Siempre devolver lista para 'results'
            "data": None,       # 'data' será None en error
            "total": 0, 
            "error": error_message
        }
        # Añadir claves específicas si es necesario para la función que llama
        if return_key_singular not in payload_error: payload_error[return_key_singular] = None
        if return_key_plural not in payload_error: payload_error[return_key_plural] = []
        
        return payload_error

    data_results = api_response.data if api_response.data is not None else []
    total_count = api_response.count if api_response.count is not None else len(data_results)
    
    single_item = None
    if data_results and len(data_results) == 1 and return_key_singular != return_key_plural:
        single_item = data_results[0]
    elif data_results and return_key_singular != return_key_plural and len(data_results) > 1 : # Se esperaba uno, llegaron muchos
         logger.warning(f"Se esperaban datos únicos en {function_name} para '{table_name}', pero se obtuvieron {len(data_results)}. Devolviendo el primero.")
         single_item = data_results[0] # Devolver el primero por defecto

    logger.debug(f"Datos obtenidos/modificados en '{table_name}' por {function_name}: {len(data_results)} filas, Conteo total DB: {total_count}")
    
    payload_success = {
        "success": True, 
        "results": data_results, 
        "data": single_item, # Será None si no es aplicable o data_results está vacío
        "total": total_count, 
        "error": None
    }
    # Para funciones específicas de usuario, paciente, sesión, etc., que esperan una clave singular
    if return_key_singular not in payload_success: payload_success[return_key_singular] = single_item
    if return_key_plural not in payload_success: payload_success[return_key_plural] = data_results
    
    return payload_success


# --- Funciones de Usuarios ---
async def get_user_by_username(username: str) -> Dict[str, Any]:
    if not username: return {"success": False, "user": None, "error": "Username requerido"}
    try:
        await supabase._ensure_initialized(); search_username = username.lower()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.select("*").eq('username', search_username).limit(1), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_user_by_username", TABLE_USUARIOS, return_key_singular="user")
        return {"success": processed["success"], "user": processed["user"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en get_user_by_username: {e}", exc_info=True); return {"success": False, "user": None, "error": str(e)}

async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    if not user_id: return {"success": False, "user": None, "error": "User ID requerido"}
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.select("*").eq('id', user_id).limit(1), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_user_by_id", TABLE_USUARIOS, return_key_singular="user")
        if processed.get("user"): processed["user"].pop('hashed_password', None)
        return {"success": processed["success"], "user": processed["user"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en get_user_by_id: {e}", exc_info=True); return {"success": False, "user": None, "error": str(e)}

async def update_user_auth_status(username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    if not username or not updates: return {"success": False, "error": "Argumentos inválidos"}
    allowed_updates = {}
    if 'is_locked' in updates: allowed_updates['is_locked'] = bool(updates['is_locked'])
    if 'failed_login_attempts' in updates: allowed_updates['failed_login_attempts'] = int(updates['failed_login_attempts'])
    if 'last_login' in updates:
        if isinstance(updates['last_login'], datetime): allowed_updates['last_login'] = updates['last_login'].isoformat()
        elif isinstance(updates['last_login'], str): allowed_updates['last_login'] = updates['last_login']
    if not allowed_updates: return {"success": False, "error": "No hay campos válidos para actualizar"}
    try:
        await supabase._ensure_initialized(); search_username = username.lower()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.update(allowed_updates).eq('username', search_username), use_service_key=True, handle_error=False)
        # Update devuelve los datos actualizados si 'returning=representation' está activo o se especifica en la query
        return await _handle_supabase_response(api_response, "update_user_auth_status", TABLE_USUARIOS, return_key_plural="updated_users")
    except Exception as e: logger.error(f"Excepción en update_user_auth_status: {e}", exc_info=True); return {"success": False, "error": str(e)}

async def get_all_db_users(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    logger.info("Consultando todos los usuarios DB.")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.select("id, username, email, full_name, roles, is_active, is_locked, last_login, created_at, updated_at", count='exact').limit(limit).offset(offset).order("username"), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "get_all_db_users", TABLE_USUARIOS, return_key_plural="users")
    except Exception as e: logger.error(f"Excepción en get_all_db_users: {e}", exc_info=True); return {"success": False, "users": [], "total": 0, "error": str(e)}

async def create_db_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Creando usuario DB: {user_data.get('username')}")
    # ... (tu lógica de validación de required_fields y normalización) ...
    try:
        await supabase._ensure_initialized()
        user_data["username"] = user_data["username"].lower().strip()
        if "roles" not in user_data or not isinstance(user_data["roles"], list): user_data["roles"] = ["viewer"]

        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.insert(user_data), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "create_db_user", TABLE_USUARIOS, return_key_singular="user")
        if processed.get("user"): processed["user"].pop('hashed_password', None)
        return {"success": processed["success"], "user": processed["user"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en create_db_user: {e}", exc_info=True); return {"success": False, "user": None, "error": str(e)}

async def update_db_user(user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Actualizando usuario DB ID: {user_id}")
    # ... (tu lógica de limpieza de update_data) ...
    update_data.pop('id', None); update_data.pop('username', None)
    if "roles" in update_data and not isinstance(update_data["roles"], list): update_data["roles"] = [update_data["roles"]] if isinstance(update_data["roles"], str) else ["viewer"]
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.update(update_data).eq("id", user_id), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "update_db_user", TABLE_USUARIOS, return_key_singular="user")
        if processed.get("user"): processed["user"].pop('hashed_password', None)
        return {"success": processed["success"], "user": processed["user"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en update_db_user: {e}", exc_info=True); return {"success": False, "user": None, "error": str(e)}

async def delete_db_user(user_id: str) -> Dict[str, Any]:
    logger.info(f"Eliminando usuario DB ID: {user_id}")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_USUARIOS, lambda t: t.delete().eq('id', user_id), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "delete_db_user", TABLE_USUARIOS) # El helper ya devuelve success/error
    except Exception as e: logger.error(f"Excepción en delete_db_user: {e}", exc_info=True); return {"success": False, "error": str(e)}

# --- Funciones para Pacientes ---
async def get_all_patients(limit=1000, offset=0, sort_by="nombre", order="asc"):
    logger.info(f"Consultando tabla '{TABLE_PACIENTES}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_PACIENTES, lambda t: t.select("*", count='exact').order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "get_all_patients", TABLE_PACIENTES)
    except Exception as e: logger.exception(f"Excepción general en get_all_patients: {e}"); return {"success": False, "results": [], "total": 0, "error": str(e)}

async def get_patient_by_id(patient_id: str) -> Dict[str, Any]:
    if not patient_id: return {"success": False, "patient": None, "error": "Patient ID requerido"}
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(
            TABLE_PACIENTES,
            query_fn=lambda table: table.select("*").eq('id', patient_id).limit(1),
            use_service_key=True, handle_error=False
        )
        processed_response = await _handle_supabase_response(api_response, "get_patient_by_id", TABLE_PACIENTES)
        return {"success": processed_response["success"], "patient": processed_response["data"], "error": processed_response["error"]}
    except Exception as e:
        logger.error(f"Excepción en get_patient_by_id para '{patient_id}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error en base de datos: {str(e)}"}

async def get_patient_by_phone(phone: str) -> Dict[str, Any]:
    table_name = TABLE_PACIENTES
    logger.info(f"Buscando paciente por teléfono similar a '{phone}' en tabla '{table_name}'.")
    if not phone:
        return {"success": False, "patient": None, "error": "Número de teléfono requerido"}
    try:
        await supabase._ensure_initialized()
        normalized_phone = ''.join(filter(str.isdigit, phone))
        if not normalized_phone:
            return {"success": False, "patient": None, "error": "Número de teléfono normalizado inválido"}

        api_response = await supabase.query_table(
            table_name,
            query_fn=lambda t: t.select("*").like('telefono', f'%{normalized_phone}%').limit(1), # 'telefono' es el nombre de tu columna
            use_service_key=True, handle_error=False
        )
        processed = await _handle_supabase_response(api_response, "get_patient_by_phone", table_name)
        return {"success": processed["success"], "patient": processed["data"], "error": processed["error"]}
    except Exception as e:
        logger.error(f"Excepción en get_patient_by_phone para '{phone}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error en base de datos: {str(e)}"}

async def get_patient_by_email(email: str) -> Dict[str, Any]:
    if not email: return {"success": False, "patient": None, "error": "Email requerido"}
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_PACIENTES, lambda t: t.select("*").eq('email', email).limit(1), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_patient_by_email", TABLE_PACIENTES, return_key_singular="patient")
        return {"success": processed["success"], "patient": processed["patient"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en get_patient_by_email: {e}", exc_info=True); return {"success": False, "patient": None, "error": str(e)}

async def insert_patient(name: str, phone: str, email: Optional[str] = None, language: str = "es", metadata: Optional[Dict[str, Any]] = None, assigned_therapist_id: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"Insertando paciente: {name}")
    try:
        await supabase._ensure_initialized()
        normalized_phone = ''.join(filter(str.isdigit, phone))
        patient_data = {"name": name, "phone": normalized_phone, "language": language, "metadata": metadata or {}, "email": email, "assigned_therapist_id": assigned_therapist_id}
        api_response = await supabase.query_table(TABLE_PACIENTES, lambda t: t.insert(patient_data), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "insert_patient", TABLE_PACIENTES, return_key_singular="patient")
        return {"success": processed["success"], "id": processed.get("patient", {}).get("id") if processed.get("patient") else None, "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en insert_patient: {e}", exc_info=True); return {"success": False, "id": None, "error": str(e)}

async def update_patient(patient_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Actualizando paciente ID: {patient_id}")
    update_data.pop('id', None)
    if 'phone' in update_data: update_data['phone'] = ''.join(filter(str.isdigit, update_data['phone']))
    if 'email' in update_data and update_data['email']: update_data['email'] = update_data['email'].lower()
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_PACIENTES, lambda t: t.update(update_data).eq('id', patient_id), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "update_patient", TABLE_PACIENTES, return_key_singular="patient")
        return {"success": processed["success"], "patient": processed["patient"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en update_patient: {e}", exc_info=True); return {"success": False, "patient": None, "error": str(e)}

async def delete_patient(patient_id: str) -> Dict[str, Any]:
    logger.info(f"Eliminando paciente ID: {patient_id}")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_PACIENTES, lambda t: t.delete().eq('id', patient_id), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "delete_patient", TABLE_PACIENTES)
    except Exception as e: logger.error(f"Excepción en delete_patient: {e}", exc_info=True); return {"success": False, "error": str(e)}


# --- Funciones para Citas (Appointments) ---
async def get_all_appointments(limit=1000, offset=0, sort_by="scheduled_date", order="desc"):
    logger.info(f"Consultando tabla '{TABLE_APPOINTMENTS}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.select("*", count='exact').order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "get_all_appointments", TABLE_APPOINTMENTS, return_key_plural="appointments")
    except Exception as e: logger.exception(f"Excepción general en get_all_appointments: {e}"); return {"success": False, "results": [], "total": 0, "error": str(e)}

async def insert_appointment_record(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Insertando cita (appointment): {appointment_data.get('client_id') if appointment_data else 'N/A'}") 
    try:
        await supabase._ensure_initialized()
        # Asegurar que scheduled_at es string ISO si existe y es datetime
        if isinstance(appointment_data.get("scheduled_date"), datetime):
            appointment_data["scheduled_date"] = appointment_data["scheduled_date"].date().isoformat()
        if isinstance(appointment_data.get("start_time"), datetime.time):
            appointment_data["start_time"] = appointment_data["start_time"].isoformat()
        if isinstance(appointment_data.get("end_time"), datetime.time):
            appointment_data["end_time"] = appointment_data["end_time"].isoformat()
        
        # Para upsert basado en calendly_event_uri si existe, o simple insert si no
        if "calendly_event_uri" in appointment_data and appointment_data["calendly_event_uri"]:
            if "email" in appointment_data and appointment_data["email"]: 
                 appointment_data["invitee_email"] = appointment_data["invitee_email"].lower() # Asumiendo que esta clave existe
            query_fn = lambda t: t.upsert(appointment_data, on_conflict="calendly_event_uri")
        else:
            query_fn = lambda t: t.insert(appointment_data)

        api_response = await supabase.query_table(TABLE_APPOINTMENTS, query_fn, use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "insert_appointment_record", TABLE_APPOINTMENTS, return_key_singular="appointment")
        return {"success": processed["success"], "id": processed.get("appointment", {}).get("id") if processed.get("appointment") else None, "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en insert_appointment_record: {e}", exc_info=True); return {"success": False, "id": None, "error": str(e)}

async def get_appointment_by_id(appointment_id: str) -> Dict[str, Any]:
    logger.info(f"Obteniendo cita (appointment) ID: {appointment_id}") 
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.select("*").eq('id', appointment_id).limit(1), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_appointment_by_id", TABLE_APPOINTMENTS, return_key_singular="appointment")
        return {"success": processed["success"], "appointment": processed["appointment"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en get_appointment_by_id: {e}", exc_info=True); return {"success": False, "appointment": None, "error": str(e)}

async def update_appointment_record(appointment_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]: 
    logger.info(f"Actualizando cita (appointment) ID: {appointment_id}") 
    update_data.pop('id', None)
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.update(update_data).eq('id', appointment_id), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "update_appointment_record", TABLE_APPOINTMENTS, return_key_singular="appointment")
        return {"success": processed["success"], "appointment": processed["appointment"], "error": processed["error"]}
    except Exception as e: logger.error(f"Excepción en update_appointment_record: {e}", exc_info=True); return {"success": False, "appointment": None, "error": str(e)}

async def delete_appointment_record(appointment_id: str) -> Dict[str, Any]: 
    logger.info(f"Eliminando cita (appointment) ID: {appointment_id}") 
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.delete().eq('id', appointment_id), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "delete_appointment_record", TABLE_APPOINTMENTS)
    except Exception as e: logger.error(f"Excepción en delete_appointment_record: {e}", exc_info=True); return {"success": False, "error": str(e)}


# --- Funciones para Notifications ---
async def get_all_notifications(limit: int = 1000, offset: int = 0, sort_by="created_at", order="desc") -> Dict[str, Any]:
    logger.info(f"Consultando tabla '{TABLE_NOTIFICATIONS}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_NOTIFICATIONS, lambda t: t.select("*", count='exact').order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "get_all_notifications", TABLE_NOTIFICATIONS)
    except Exception as e: logger.exception(f"Excepción general en get_all_notifications: {e}"); return {"success": False, "results": [], "total": 0, "error": str(e)}

async def get_pending_notifications(limit: int = 10) -> Dict[str, Any]:
    table_name = TABLE_NOTIFICATIONS
    logger.info(f"Consultando notificaciones pendientes (tabla '{table_name}'). Limite: {limit}")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(
            table_name,
            query_fn=lambda t: t.select("*", count='exact').eq('status', 'pendiente').order("created_at", desc=False).limit(limit),
            use_service_key=True, handle_error=False
        )
        return await _handle_supabase_response(api_response, "get_pending_notifications", table_name, return_key_plural="notifications")
    except Exception as e: logger.error(f"Excepción en get_pending_notifications: {e}", exc_info=True); return {"success": False, "notifications": [], "total": 0, "error": str(e)}

async def update_notification_status(notification_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.info(f"Actualizando estado de notificación ID {notification_id} a '{status}'")
    try:
        await supabase._ensure_initialized()
        update_data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
        if metadata is not None: update_data["metadata"] = metadata
        api_response = await supabase.query_table(TABLE_NOTIFICATIONS, lambda t: t.update(update_data).eq("id", notification_id), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "update_notification_status", TABLE_NOTIFICATIONS, return_key_singular="notification")
    except Exception as e: logger.error(f"Excepción en update_notification_status: {e}", exc_info=True); return {"success": False, "data": None, "error": str(e)} # data era 'notification'

async def insert_notification(patient_id: str, message: str, channel: str = "whatsapp", status: str = "pending", scheduled_at: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.info(f"Insertando notificación para paciente {patient_id}")
    try:
        await supabase._ensure_initialized()
        notification_data = {"patient_id": patient_id, "message": message, "channel": channel, "status": status, "scheduled_at": scheduled_at, "metadata": metadata or {}}
        api_response = await supabase.query_table(TABLE_NOTIFICATIONS, lambda t: t.insert(notification_data), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "insert_notification", TABLE_NOTIFICATIONS, return_key_singular="notification")
        return {"success": processed["success"], "id": processed.get("notification", {}).get("id") if processed.get("notification") else None, "error": processed["error"]} # id era notification_id
    except Exception as e: logger.error(f"Excepción en insert_notification: {e}", exc_info=True); return {"success": False, "id": None, "error": str(e)}


# --- Funciones para Configuraciones ---
async def get_system_config(key: str) -> Dict[str, Any]:
    logger.info(f"Obteniendo config: {key}")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_CONFIGURACIONES, lambda t: t.select("key, value").eq('key', key).limit(1), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_system_config", TABLE_CONFIGURACIONES, return_key_singular="config")
        # Procesar value si es JSON string
        if processed.get("config") and isinstance(processed["config"].get("value"), str):
            try: processed["config"]["value"] = json.loads(processed["config"]["value"])
            except json.JSONDecodeError: pass
        return {"success": processed["success"], "value": processed.get("config", {}).get("value") if processed.get("config") else None, "error": processed["error"]}
    except Exception as e: logger.exception(f"Excepción en get_system_config: {e}"); return {"success": False, "value": None, "error": str(e)}

async def set_system_config(key: str, value: Any) -> Dict[str, Any]:
    logger.info(f"Estableciendo config: {key} = {value}")
    try:
        await supabase._ensure_initialized()
        # La columna 'value' en 'configuraciones' es JSONB, FastAPI/Pydantic debería manejar la serialización
        # o Supabase la aceptará si es un dict/list. Si es un string simple, también está bien.
        config_data = {"key": key, "value": value, "updated_at": datetime.now(timezone.utc).isoformat()}
        api_response = await supabase.query_table(TABLE_CONFIGURACIONES, lambda t: t.upsert(config_data), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "set_system_config", TABLE_CONFIGURACIONES)
    except Exception as e: logger.exception(f"Excepción en set_system_config: {e}"); return {"success": False, "error": str(e)}

async def get_all_configs(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    logger.info(f"Consultando tabla '{TABLE_CONFIGURACIONES}'.")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_CONFIGURACIONES, lambda t: t.select("*", count='exact').order("key").limit(limit).offset(offset).execute(), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_all_configs", TABLE_CONFIGURACIONES, return_key_plural="configs")
        # Procesar 'value' para cada config
        if processed.get("configs"):
            for item in processed["configs"]:
                if isinstance(item.get("value"), str):
                    try: item["value"] = json.loads(item["value"])
                    except json.JSONDecodeError: pass
        return processed
    except Exception as e: logger.exception(f"Excepción general en get_all_configs: {e}"); return {"success": False, "configs": [], "total":0, "error": str(e)} #Devolver clave configs

# --- Funciones para Audit Log ---
async def insert_audit_log(user_id: str, action: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
    logger.debug(f"Insertando log de auditoría: User={user_id}, Action={action}")
    try:
        await supabase._ensure_initialized()
        log_data = {"user_id": user_id, "user_email": None, "action": action, "resource_type": resource_type, "resource_id": resource_id, "details": details or {}, "ip_address": ip_address, "status": "success"}
        # Obtener email del usuario si user_id es UUID válido
        if user_id and len(user_id) == 36: # Asumiendo que es un UUID
            user_info = await get_user_by_id(user_id)
            if user_info.get("success") and user_info.get("user"):
                log_data["user_email"] = user_info["user"].get("email")
        
        api_response = await supabase.query_table(TABLE_LOGS_ACTIVIDAD, lambda t: t.insert(log_data), use_service_key=True, handle_error=False) # Service key para auditoría
        processed = await _handle_supabase_response(api_response, "insert_audit_log", TABLE_LOGS_ACTIVIDAD, return_key_singular="log_entry")
        return {"success": processed["success"], "log_id": processed.get("log_entry", {}).get("id") if processed.get("log_entry") else None, "error": processed["error"]}
    except Exception as e: logger.critical(f"Excepción CRÍTICA al insertar log de auditoría: {e}", exc_info=True); return {"success": False, "log_id": None, "error": str(e)}


# --- Funciones para Sesiones de Conversación (si TABLE_SESSIONS_CONVERSATION es diferente de TABLE_CITAS) ---
# Estas funciones asumen una tabla 'sessions' simple con 'session_id' (PK, text) y 'data' (JSONB), 'updated_at'
# Si no tienes esta tabla separada o su estructura es diferente, ajusta o elimina estas funciones.
async def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    logger.debug(f"Obteniendo datos de sesión de conversación: {session_id}")
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_SESSIONS_CONVERSATION, lambda t: t.select("data").eq('session_id', session_id).limit(1).maybe_single(), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "get_session_data", TABLE_SESSIONS_CONVERSATION, return_key_singular="session_conv_data")
        if processed["success"] and processed.get("session_conv_data"):
            return processed["session_conv_data"].get("data") # Devuelve solo el contenido de la columna 'data'
        return None
    except Exception as e: logger.error(f"Excepción en get_session_data: {e}", exc_info=True); return None

async def save_session_data(session_id: str, data: Dict[str, Any]) -> bool:
    logger.debug(f"Guardando datos de sesión de conversación: {session_id}")
    try:
        await supabase._ensure_initialized()
        session_record = {"session_id": session_id, "data": data, "updated_at": datetime.now(timezone.utc).isoformat()}
        api_response = await supabase.query_table(TABLE_SESSIONS_CONVERSATION, lambda t: t.upsert(session_record), use_service_key=True, handle_error=False)
        processed = await _handle_supabase_response(api_response, "save_session_data", TABLE_SESSIONS_CONVERSATION)
        return processed["success"]
    except Exception as e: logger.error(f"Excepción en save_session_data: {e}", exc_info=True); return False

async def delete_expired_sessions(ttl_seconds: int) -> int:
    logger.info(f"Eliminando sesiones de conversación expiradas (TTL: {ttl_seconds}s)")
    try:
        await supabase._ensure_initialized()
        # Usaremos RPC para esto, asumiendo que la función delete_old_sessions existe en la DB
        # CREATE OR REPLACE FUNCTION delete_old_sessions(ttl_interval text) RETURNS integer AS $$ ... $$
        rpc_params = {'ttl_interval': f'{ttl_seconds} seconds'}
        api_response = await supabase.execute_rpc('delete_old_sessions', params=rpc_params, handle_error=False) # supabase_client.execute_rpc no devuelve APIResponse, sino directamente el resultado o un error
        
        # El wrapper execute_rpc en SupabaseClientWrapper ya debería devolver un dict con 'data' o 'error'
        if api_response and isinstance(api_response, dict) and api_response.get('data') is not None: # Cambio aquí
            deleted_count = api_response.get('data')
            logger.info(f"RPC delete_old_sessions devolvió: {deleted_count} sesiones eliminadas.")
            return int(deleted_count) if isinstance(deleted_count, (int, str)) and str(deleted_count).isdigit() else 0
        elif api_response and isinstance(api_response, dict) and api_response.get('error'):
             logger.error(f"Error de Supabase al ejecutar RPC delete_old_sessions: {api_response.get('error')}")
             return -1
        else: # No error explícito, pero no hay datos
             logger.warning(f"Respuesta inesperada o sin datos de RPC delete_old_sessions: {api_response}")
             return 0 # Asumir 0 eliminadas si no hay error ni datos claros
             
    except Exception as e:
        logger.exception(f"Excepción inesperada al eliminar sesiones expiradas: {e}")
        return -1


# --- Funciones para Appointments (Calendly/Zoom - tabla 'appointments') ---
# Asumo que TABLE_APPOINTMENTS = "appointments" está definida
# TABLE_APPOINTMENTS = "appointments" # ELIMINAR ESTA REDEFINICIÓN

async def insert_appointment(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Insertando/Actualizando cita (appointment) vía Calendly/Zoom: {appointment_data.get('calendly_event_uri')}")
    if not appointment_data.get("calendly_event_uri"):
        return {"success": False, "id": None, "error": "Calendly event URI es requerido"}
    try:
        await supabase._ensure_initialized()
        # Asegurar que scheduled_at es string ISO
        if isinstance(appointment_data.get("scheduled_at"), datetime):
            appointment_data["scheduled_at"] = appointment_data["scheduled_at"].isoformat()
        if "email" in appointment_data and appointment_data["email"]: # Si existe invitee_email
             appointment_data["invitee_email"] = appointment_data["invitee_email"].lower()

        api_response = await supabase.query_table(
            TABLE_APPOINTMENTS,
            query_fn=lambda t: t.upsert(appointment_data, on_conflict="calendly_event_uri"),
            use_service_key=True, handle_error=False
        )
        processed = await _handle_supabase_response(api_response, "insert_appointment", TABLE_APPOINTMENTS, return_key_singular="appointment")
        return {"success": processed["success"], "id": processed.get("appointment", {}).get("id") if processed.get("appointment") else None, "error": processed["error"]}
    except Exception as e:
        logger.error(f"Excepción en insert_appointment: {e}", exc_info=True)
        return {"success": False, "id": None, "error": str(e)}

async def get_appointment_by_calendly_uri(calendly_event_uri: str) -> Dict[str, Any]:
    logger.info(f"Obteniendo cita (appointment) por Calendly URI: {calendly_event_uri}")
    if not calendly_event_uri: return {"success": False, "appointment": None, "error": "Calendly event URI requerido"}
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.select("*").eq('calendly_event_uri', calendly_event_uri).limit(1), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "get_appointment_by_calendly_uri", TABLE_APPOINTMENTS, return_key_singular="appointment")
    except Exception as e:
        logger.error(f"Excepción en get_appointment_by_calendly_uri: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": str(e)}

async def update_appointment_zoom_details(calendly_event_uri: str, zoom_meeting_id: str, zoom_join_url: str) -> Dict[str, Any]:
    logger.info(f"Actualizando Zoom para cita Calendly URI: {calendly_event_uri}")
    if not all([calendly_event_uri, zoom_meeting_id, zoom_join_url]): return {"success": False, "error": "Datos incompletos para actualizar Zoom"}
    try:
        await supabase._ensure_initialized()
        update_data = {"zoom_meeting_id": zoom_meeting_id, "zoom_join_url": zoom_join_url}
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.update(update_data).eq('calendly_event_uri', calendly_event_uri), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "update_appointment_zoom_details", TABLE_APPOINTMENTS)
    except Exception as e: logger.error(f"Excepción en update_appointment_zoom_details: {e}", exc_info=True); return {"success": False, "error": str(e)}

async def update_appointment_status(calendly_event_uri: str, status: str) -> Dict[str, Any]:
    logger.info(f"Actualizando estado de cita Calendly URI {calendly_event_uri} a: {status}")
    if not all([calendly_event_uri, status]): return {"success": False, "error": "Datos incompletos para actualizar estado de cita"}
    try:
        await supabase._ensure_initialized()
        api_response = await supabase.query_table(TABLE_APPOINTMENTS, lambda t: t.update({"status": status}).eq('calendly_event_uri', calendly_event_uri), use_service_key=True, handle_error=False)
        return await _handle_supabase_response(api_response, "update_appointment_status", TABLE_APPOINTMENTS)
    except Exception as e: logger.error(f"Excepción en update_appointment_status: {e}", exc_info=True); return {"success": False, "error": str(e)}