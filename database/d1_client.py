# -*- coding: utf-8 -*-
"""
Cliente para interactuar con la base de datos Supabase.
Proporciona funciones asíncronas para gestionar pacientes, sesiones, etc.
"""
import json
from typing import Dict, List, Any, Optional # ASEGURAR QUE Dict, List, etc. están importados
from datetime import datetime, timezone, timedelta

# Importaciones necesarias para el manejo de errores
from supabase import PostgrestAPIError  # Para errores de PostgREST
from gotrue.errors import AuthApiError  # Para errores de autenticación
import httpx # Para errores de red

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

async def _handle_supabase_response(
    data_payload: Any,
    operation_name: str,
    table_name: Optional[str] = None,
    return_key_plural: Optional[str] = None,
    return_key_singular: Optional[str] = None,
    error_obj: Optional[Dict[str, Any]] = None # Nuevo parámetro para errores lógicos de la API
) -> Dict[str, Any]:
    # El status OK (200) ya fue verificado antes de llegar aquí (o se lanzó excepción).
    # Si hay un error_obj, significa que la API de Supabase devolvió un error JSON
    if error_obj: # Si Supabase devolvió { "code": ..., "message": ... }
        error_message = error_obj.get('message', 'Error desconocido de Supabase')
        error_details = str(error_obj)
        logger.error(f"Supabase API devolvió un error en {operation_name} para la tabla {table_name or 'N/A'}: {error_message} | Detalles: {error_details}")
        return {"success": False, "error": error_message, "details": error_details}

    # Si no hay error_obj, el éxito es que data_payload tiene los datos.
    # data_payload puede ser None si la operación fue exitosa pero no devuelve datos (ej. delete sin returning).
    # O puede ser una lista vacía si una consulta select no encontró resultados.

    result = {"success": True}
    
    if data_payload is None:
        # Algunas operaciones como delete pueden no devolver datos.
        # O RPCs que no tienen un 'return'.
        result["message"] = f"{operation_name} en {table_name or 'N/A'} completado, sin datos de retorno específicos."
        result["data"] = None
        result["results"] = [] # Mantener consistencia
        if return_key_singular: result[return_key_singular] = None
        if return_key_plural: result[return_key_plural] = []
        return result

    if isinstance(data_payload, list):
        result[return_key_plural if return_key_plural else "results"] = data_payload
        if return_key_singular:
            result[return_key_singular] = data_payload[0] if data_payload else None
        # Asegurar que 'data' y 'results' existan para consistencia general, aunque no sean las claves primarias
        if "data" not in result: result["data"] = data_payload[0] if data_payload else None
        if "results" not in result: result["results"] = data_payload

    else: # Si es un solo objeto (por ejemplo, de un .limit(1).maybe_single() o un insert/update con returning=representation y single)
        result[return_key_singular if return_key_singular else "data"] = data_payload
        # Asegurar que 'data' y 'results' existan
        if "data" not in result: result["data"] = data_payload
        # Si se esperaba un singular pero se obtuvo una lista, esto ya se manejó antes de llamar a _handle_supabase_response
        # o la lógica de la función que llama debería adaptarse. Para 'results', si es singular, se puede poner en una lista.
        if "results" not in result: result["results"] = [data_payload] 
            
    logger.debug(f"Datos obtenidos/modificados en '{table_name or 'N/A'}' por {operation_name}. Payload: {data_payload}")
    return result


# --- Funciones de Usuarios ---
async def get_user_by_username(username: str) -> Dict[str, Any]:
    if not username: return {"success": False, "user": None, "error": "Username requerido"}
    operation_name = "get_user_by_username"
    table_name = TABLE_USUARIOS
    try:
        await supabase._ensure_initialized()
        search_username = username.lower()
        # Usar admin_client para operaciones de usuario que pueden requerir permisos elevados
        api_response = supabase.admin_client.from_(table_name).select("*").eq('username', search_username).limit(1).execute()
        
        # Verificar errores lógicos en la respuesta JSON
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        # Procesar datos exitosos
        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="user")
        return {"success": processed["success"], "user": processed.get("user"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción inesperada en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    if not user_id: return {"success": False, "user": None, "error": "User ID requerido"}
    operation_name = "get_user_by_id"
    table_name = TABLE_USUARIOS
    try:
        await supabase._ensure_initialized()
        api_response = supabase.admin_client.from_(table_name).select("*").eq('id', user_id).limit(1).execute()

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="user")
        if processed.get("user") and isinstance(processed["user"], dict): # Asegurarse que user es un dict
            processed["user"].pop('hashed_password', None)
        return {"success": processed["success"], "user": processed.get("user"), "error": processed.get("error")}
        
    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción inesperada en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_user_auth_status(username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    if not username or not updates: return {"success": False, "error": "Argumentos inválidos"}
    operation_name = "update_user_auth_status"
    table_name = TABLE_USUARIOS
    
    allowed_updates = {}
    if 'is_locked' in updates: allowed_updates['is_locked'] = bool(updates['is_locked'])
    if 'failed_login_attempts' in updates: allowed_updates['failed_login_attempts'] = int(updates['failed_login_attempts'])
    if 'last_login' in updates:
        if isinstance(updates['last_login'], datetime): allowed_updates['last_login'] = updates['last_login'].isoformat()
        elif isinstance(updates['last_login'], str): allowed_updates['last_login'] = updates['last_login']
    if not allowed_updates: return {"success": False, "error": "No hay campos válidos para actualizar"}

    try:
        await supabase._ensure_initialized()
        search_username = username.lower()
        api_response = supabase.admin_client.from_(table_name).update(allowed_updates).eq('username', search_username).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="updated_users")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción inesperada en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_all_db_users(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    operation_name = "get_all_db_users"
    table_name = TABLE_USUARIOS
    logger.info(f"Consultando todos los usuarios DB ({operation_name}).")
    try:
        await supabase._ensure_initialized()
        # Usar el cliente de servicio para listar usuarios (puede requerir permisos elevados)
        # Nota: count='exact' no es un parámetro directo de select en supabase-py v2, 
        # se maneja con .execute(count=CountMethod.exact) o se obtiene de api_response.count
        api_response = supabase.admin_client.from_(table_name).select(
            "id, username, email, full_name, roles, is_active, is_locked, last_login, created_at, updated_at"
        ).limit(limit).offset(offset).order("username").execute() # Removido count='exact' de select

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
        
        # El conteo total (si se pidió con execute(count=...)) estaría en api_response.count
        # _handle_supabase_response no maneja 'count' directamente, sino que se infiere del payload.
        # Para obtener el conteo total exacto, la llamada a execute necesitaría el parámetro `count`.
        # Aquí, asumiremos que el conteo es la longitud de los datos si no se especifica `count` en execute.
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="users")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "users": [], "total": 0, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "users": [], "total": 0, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción inesperada en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "users": [], "total": 0, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def create_db_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    operation_name = "create_db_user"
    table_name = TABLE_USUARIOS
    logger.info(f"Creando usuario DB ({operation_name}): {user_data.get('username')}")
    
    # Validación básica (mantener o mejorar según necesidad)
    if not user_data.get("username") or not user_data.get("hashed_password"):
        return {"success": False, "user": None, "error": "Username y hashed_password son requeridos"}
    
    user_data["username"] = user_data["username"].lower().strip()
    if "roles" not in user_data or not isinstance(user_data["roles"], list): 
        user_data["roles"] = ["viewer"]

    try:
        await supabase._ensure_initialized()
        # Usar el cliente de servicio para operaciones de usuario que requieren permisos elevados
        api_response = supabase.admin_client.from_(table_name).insert(user_data).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            # Este caso es menos común para insert si hay un error a nivel de DB, usualmente PostgrestAPIError se lanzaría.
            # Pero podría ser un error lógico si la API lo permite.
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="user")
        new_user = processed.get("user")
        if new_user and isinstance(new_user, dict): # Asegurarse que user es un dict
             new_user.pop('hashed_password', None) # No devolver el hash

        return {"success": processed["success"], "user": new_user, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción inesperada en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_db_user(user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    operation_name = "update_db_user"
    table_name = TABLE_USUARIOS
    logger.info(f"Actualizando usuario DB ID ({operation_name}): {user_id}")

    update_data.pop('id', None) # No se puede actualizar el ID
    update_data.pop('username', None) # No permitir cambio de username aquí para simplificar
    if "roles" in update_data and not isinstance(update_data["roles"], list): 
        update_data["roles"] = [update_data["roles"]] if isinstance(update_data["roles"], str) else ["viewer"]
    if not update_data:
        return {"success": False, "user": None, "error": "No hay datos para actualizar."}

    try:
        await supabase._ensure_initialized()
        # Usar el cliente de servicio para operaciones de usuario que requieren permisos elevados
        api_response = supabase.admin_client.from_(table_name).update(update_data).eq("id", user_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="user")
        updated_user = processed.get("user")
        if updated_user and isinstance(updated_user, dict): # Asegurarse que user es un dict
            updated_user.pop('hashed_password', None)

        return {"success": processed["success"], "user": updated_user, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {user_id}: {e.message}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {user_id}: {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {user_id}: {e}", exc_info=True)
        return {"success": False, "user": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def delete_db_user(user_id: str) -> Dict[str, Any]:
    operation_name = "delete_db_user"
    table_name = TABLE_USUARIOS
    logger.info(f"Eliminando usuario DB ID ({operation_name}): {user_id}")
    try:
        await supabase._ensure_initialized()
        # Usar el cliente de servicio para operaciones de usuario que requieren permisos elevados
        api_response = supabase.admin_client.from_(table_name).delete().eq('id', user_id).execute()
        
        # Delete puede devolver datos si se usa `returning` o si la PK no existe (devuelve lista vacía).
        # Si hay un error de DB (ej. foreign key constraint), PostgrestAPIError se lanzaría.
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
             return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        # Si data es una lista vacía y no hubo error, significa que el delete fue "exitoso" (no encontró el ID o lo borró).
        # _handle_supabase_response lo tratará como "sin datos de retorno específicos"
        return await _handle_supabase_response(api_response.data, operation_name, table_name)

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {user_id}: {e.message}", exc_info=True)
        return {"success": False, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {user_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {user_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

# --- Funciones para Pacientes ---
async def get_all_patients(limit=1000, offset=0, sort_by="name", order="asc") -> Dict[str, Any]: # Corregido default sort_by
    operation_name = "get_all_patients"
    table_name = TABLE_PACIENTES
    logger.info(f"Consultando tabla '{table_name}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="results") # Debería ser "patients" o "results" consistentemente

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "results": [], "total": 0, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "results": [], "total": 0, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.exception(f"Excepción general en {operation_name}: {e}")
        return {"success": False, "results": [], "total": 0, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_patient_by_id(patient_id: str) -> Dict[str, Any]:
    if not patient_id: return {"success": False, "patient": None, "error": "Patient ID requerido"}
    operation_name = "get_patient_by_id"
    table_name = TABLE_PACIENTES
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").eq('id', patient_id).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed_response = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="patient")
        return {"success": processed_response["success"], "patient": processed_response.get("patient"), "error": processed_response.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para '{patient_id}': {e.message}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para '{patient_id}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para '{patient_id}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_patient_by_phone(phone: str) -> Dict[str, Any]:
    operation_name = "get_patient_by_phone"
    table_name = TABLE_PACIENTES
    logger.info(f"Buscando paciente por teléfono similar a '{phone}' en tabla '{table_name}'.")
    if not phone:
        return {"success": False, "patient": None, "error": "Número de teléfono requerido"}
    
    try:
        await supabase._ensure_initialized()
        normalized_phone = ''.join(filter(str.isdigit, phone))
        if not normalized_phone:
            return {"success": False, "patient": None, "error": "Número de teléfono normalizado inválido"}

        api_response = supabase.client.from_(table_name).select("*").like('telefono', f'%{normalized_phone}%').limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="patient")
        return {"success": processed["success"], "patient": processed.get("patient"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para '{phone}': {e.message}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para '{phone}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para '{phone}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_patient_by_email(email: str) -> Dict[str, Any]:
    if not email: return {"success": False, "patient": None, "error": "Email requerido"}
    operation_name = "get_patient_by_email"
    table_name = TABLE_PACIENTES
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").eq('email', email.lower()).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="patient")
        return {"success": processed["success"], "patient": processed.get("patient"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para '{email}': {e.message}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para '{email}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para '{email}': {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def insert_patient(name: str, phone: str, email: Optional[str] = None, language: str = "es", metadata: Optional[Dict[str, Any]] = None, assigned_therapist_id: Optional[str] = None) -> Dict[str, Any]:
    operation_name = "insert_patient"
    table_name = TABLE_PACIENTES
    logger.info(f"Insertando paciente ({operation_name}): {name}")
    try:
        await supabase._ensure_initialized()
        normalized_phone = ''.join(filter(str.isdigit, phone))
        patient_data = {"name": name, "phone": normalized_phone, "language": language, "metadata": metadata or {}, "email": email.lower() if email else None, "assigned_therapist_id": assigned_therapist_id}
        
        api_response = supabase.client.from_(table_name).insert(patient_data).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="patient")
        patient_obj = processed.get("patient")
        patient_id = patient_obj.get("id") if isinstance(patient_obj, dict) else None
        
        return {"success": processed["success"], "id": patient_id, "patient": patient_obj, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "id": None, "patient":None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "patient":None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "patient":None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_patient(patient_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    operation_name = "update_patient"
    table_name = TABLE_PACIENTES
    logger.info(f"Actualizando paciente ID ({operation_name}): {patient_id}")
    update_data.pop('id', None)
    if 'phone' in update_data and update_data['phone']: update_data['phone'] = ''.join(filter(str.isdigit, update_data['phone']))
    if 'email' in update_data and update_data['email']: update_data['email'] = update_data['email'].lower()
    if not update_data:
        return {"success": False, "patient": None, "error": "No hay datos para actualizar."}

    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).update(update_data).eq('id', patient_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="patient")
        return {"success": processed["success"], "patient": processed.get("patient"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {patient_id}: {e.message}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {patient_id}: {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {patient_id}: {e}", exc_info=True)
        return {"success": False, "patient": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def delete_patient(patient_id: str) -> Dict[str, Any]:
    operation_name = "delete_patient"
    table_name = TABLE_PACIENTES
    logger.info(f"Eliminando paciente ID ({operation_name}): {patient_id}")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).delete().eq('id', patient_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name)

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {patient_id}: {e.message}", exc_info=True)
        return {"success": False, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {patient_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {patient_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

# --- Funciones para Citas (Appointments) ---
async def get_all_appointments(limit=1000, offset=0, sort_by="scheduled_date", order="desc") -> Dict[str, Any]: # Cambiado nombre scheduled_at a scheduled_date si aplica
    operation_name = "get_all_appointments"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Consultando tabla '{table_name}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1).execute()

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="appointments")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "appointments": [], "total": 0, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "appointments": [], "total": 0, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.exception(f"Excepción general en {operation_name}: {e}")
        return {"success": False, "appointments": [], "total": 0, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def insert_appointment_record(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    operation_name = "insert_appointment_record"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Insertando cita ({operation_name}) para paciente ID: {appointment_data.get('patient_id')}")

    # Validación básica (ejemplo)
    required_fields = ['patient_id', 'therapist_id', 'scheduled_date', 'duration_minutes', 'status']
    for field in required_fields:
        if field not in appointment_data:
            return {"success": False, "appointment": None, "error": f"Campo requerido '{field}' ausente."}

    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).insert(appointment_data).execute()

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
        appointment_obj = processed.get("appointment")
        appointment_id = appointment_obj.get("id") if isinstance(appointment_obj, dict) else None

        return {"success": processed["success"], "id": appointment_id, "appointment": appointment_obj, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}
        
async def get_appointment_by_id(appointment_id: str) -> Dict[str, Any]:
    if not appointment_id: return {"success": False, "appointment": None, "error": "Appointment ID requerido"}
    operation_name = "get_appointment_by_id"
    table_name = TABLE_APPOINTMENTS
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").eq('id', appointment_id).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
        return {"success": processed["success"], "appointment": processed.get("appointment"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {appointment_id}: {e.message}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_appointment_record(appointment_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]: 
    operation_name = "update_appointment_record"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Actualizando cita ID ({operation_name}): {appointment_id}")
    update_data.pop('id', None)
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).update(update_data).eq('id', appointment_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
        return {"success": processed["success"], "appointment": processed.get("appointment"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {appointment_id}: {e.message}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def delete_appointment_record(appointment_id: str) -> Dict[str, Any]: 
    operation_name = "delete_appointment_record"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Eliminando cita ID ({operation_name}): {appointment_id}")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).delete().eq('id', appointment_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name)

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {appointment_id}: {e.message}", exc_info=True)
        return {"success": False, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {appointment_id}: {e}", exc_info=True)
        return {"success": False, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

# --- Funciones para Notificaciones ---
async def get_all_notifications(limit: int = 1000, offset: int = 0, sort_by="created_at", order="desc") -> Dict[str, Any]:
    operation_name = "get_all_notifications"
    table_name = TABLE_NOTIFICATIONS
    logger.info(f"Consultando tabla '{table_name}', sort_by={sort_by}, order={order}.")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").order(sort_by, desc=(order.lower() == "desc")).range(offset, offset + limit - 1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="notifications")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "notifications": [], "total": 0, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "notifications": [], "total": 0, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.exception(f"Excepción general en {operation_name}: {e}")
        return {"success": False, "notifications": [], "total": 0, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_pending_notifications(limit: int = 10, table_name: str = TABLE_NOTIFICATIONS) -> Dict[str, Any]: # Añadido table_name como parámetro
    operation_name = "get_pending_notifications"
    # table_name es ahora un parámetro, pero default a TABLE_NOTIFICATIONS
    logger.info(f"Consultando notificaciones pendientes en tabla '{table_name}'.") # Revertido el log
    try:
        await supabase._ensure_initialized()
        
        # ----- REVERTIDO A CONSULTA ORIGINAL -----
        api_response = supabase.client.from_(table_name).select("*").eq("status", "pendiente").order("created_at", desc=False).limit(limit).execute()
        # ----- FIN DE REVERSIÓN -----

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="notifications")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error específico de Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "notifications": [], "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e: 
        logger.error(f"Error de red/conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "notifications": [], "error": f"Error de red: {type(e).__name__}", "details": str(e)}
    except Exception as e: 
        logger.error(f"Excepción inesperada en {operation_name}: {e}", exc_info=True)
        return {"success": False, "notifications": [], "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_notification_status(notification_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    operation_name = "update_notification_status"
    table_name = TABLE_NOTIFICATIONS
    logger.info(f"Actualizando estado de notificación ID {notification_id} a '{status}'.")
    update_payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if metadata is not None:
        update_payload["metadata"] = metadata
        
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).update(update_payload).eq("id", notification_id).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="notification")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {notification_id}: {e.message}", exc_info=True)
        return {"success": False, "notification": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {notification_id}: {e}", exc_info=True)
        return {"success": False, "notification": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {notification_id}: {e}", exc_info=True)
        return {"success": False, "notification": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def insert_notification(patient_id: str, message: str, channel: str = "whatsapp", status: str = "pending", scheduled_at: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    operation_name = "insert_notification"
    table_name = TABLE_NOTIFICATIONS
    logger.info(f"Insertando notificación para paciente ID {patient_id}")
    
    notification_data = {"patient_id": patient_id, "message": message, "channel": channel, "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    if scheduled_at:
        notification_data["scheduled_at"] = scheduled_at
        
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).insert(notification_data).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="notification")
        notification_obj = processed.get("notification")
        notification_id = notification_obj.get("id") if isinstance(notification_obj, dict) else None
        
        return {"success": processed["success"], "id": notification_id, "notification": notification_obj, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "id": None, "notification": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "notification": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "notification": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

# --- Funciones para Configuración del Sistema ---
async def get_system_config(key: str) -> Dict[str, Any]:
    operation_name = "get_system_config"
    table_name = TABLE_CONFIGURACIONES # Asegúrate que esta constante esté definida
    logger.info(f"Consultando configuración del sistema para la clave '{key}'.")
    if not key:
        return {"success": False, "config_value": None, "error": "Clave de configuración requerida."}
        
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("value").eq('key', key).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        # Si api_response.data es una lista y tiene elementos, extrae 'value'
        config_value = None
        if api_response.data and isinstance(api_response.data, list) and len(api_response.data) > 0:
            config_value = api_response.data[0].get('value')
            # Pasar solo el valor a _handle_supabase_response si es lo que se espera
            processed = await _handle_supabase_response(config_value, operation_name, table_name, return_key_singular="config_value")
        else: # No data or not a list
            processed = await _handle_supabase_response(None, operation_name, table_name, return_key_singular="config_value")

        return {"success": processed["success"], "config_value": processed.get("config_value"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para clave '{key}': {e.message}", exc_info=True)
        return {"success": False, "config_value": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para clave '{key}': {e}", exc_info=True)
        return {"success": False, "config_value": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para clave '{key}': {e}", exc_info=True)
        return {"success": False, "config_value": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def set_system_config(key: str, value: Any) -> Dict[str, Any]:
    operation_name = "set_system_config"
    table_name = TABLE_CONFIGURACIONES # Asegúrate que esta constante esté definida
    logger.info(f"Estableciendo configuración del sistema para la clave '{key}'.")
    if not key:
        return {"success": False, "error": "Clave de configuración requerida."}
        
    config_data = {"key": key, "value": value, "updated_at": datetime.now(timezone.utc).isoformat()}
    
    try:
        await supabase._ensure_initialized()
        # Upsert para crear o actualizar la configuración
        api_response = supabase.client.from_(table_name).upsert(config_data).execute()
        
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="config_entry")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para clave '{key}': {e.message}", exc_info=True)
        return {"success": False, "config_entry": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para clave '{key}': {e}", exc_info=True)
        return {"success": False, "config_entry": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para clave '{key}': {e}", exc_info=True)
        return {"success": False, "config_entry": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def get_all_configs(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    operation_name = "get_all_configs"
    table_name = TABLE_CONFIGURACIONES # Asegúrate que esta constante esté definida
    logger.info(f"Consultando todas las configuraciones del sistema ({operation_name}).")
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").limit(limit).offset(offset).order("key").execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)
            
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_plural="configs")

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} ({table_name}): {e.message}", exc_info=True)
        return {"success": False, "configs": [], "total": 0, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} ({table_name}): {e}", exc_info=True)
        return {"success": False, "configs": [], "total": 0, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.exception(f"Excepción general en {operation_name}: {e}")
        return {"success": False, "configs": [], "total": 0, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}
        
# --- Funciones para Logs de Auditoría ---
async def insert_audit_log(user_id: str, action: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
    operation_name = "insert_audit_log"
    table_name = TABLE_LOGS_ACTIVIDAD # Asegúrate que esta constante esté definida
    logger.info(f"Insertando log de auditoría: User {user_id}, Action {action}")
    
    log_data = {
        "user_id": user_id, "action": action, "resource_type": resource_type,
        "resource_id": resource_id, "details": details or {}, "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await supabase._ensure_initialized()
        # Usar service_role para insertar logs, ya que puede ser llamado por el sistema o usuarios autenticados.
        api_response = supabase.client.from_(table_name).insert(log_data).execute() 
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="log_entry")
        return {"success": processed["success"], "id": processed.get("log_entry", {}).get("id") if processed.get("log_entry") else None, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "id": None, "log_entry": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e: # Manejar errores de red
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "log_entry": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e: # Manejar cualquier otra excepción
        logger.error(f"Excepción inesperada en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "log_entry": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

# --- Funciones de Estado de Conversación (Ejemplo, adaptar a tu tabla 'sessions') ---
# Si 'sessions' es para estado de conversación (no citas)
async def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    operation_name = "get_session_data"
    table_name = TABLE_SESSIONS_CONVERSATION # Usar la constante correcta
    logger.info(f"Obteniendo datos de sesión ({operation_name}): {session_id}")
    if not session_id: return None # o un diccionario de error
        
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("data").eq('session_id', session_id).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data) # Loguea el error
            return None

        if api_response.data and isinstance(api_response.data, list) and len(api_response.data) > 0:
            return api_response.data[0].get('data') # Asume que 'data' es la columna con el JSON
        return None

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {session_id}: {e.message}", exc_info=True)
        return None
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {session_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {session_id}: {e}", exc_info=True)
        return None

async def save_session_data(session_id: str, data: Dict[str, Any]) -> bool:
    operation_name = "save_session_data"
    table_name = TABLE_SESSIONS_CONVERSATION # Usar la constante correcta
    logger.info(f"Guardando datos de sesión ({operation_name}): {session_id}")
    
    session_payload = {
        "session_id": session_id, 
        "data": data, # Asume que 'data' es la columna para el JSON
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await supabase._ensure_initialized()
        # Upsert para crear o actualizar la sesión de conversación
        api_response = supabase.client.from_(table_name).upsert(session_payload, on_conflict="session_id").execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data) # Loguea el error
            return False
            
        # Si no hay error, se asume que fue exitoso. Upsert devuelve los datos.
        # Aquí simplemente devolvemos True si no hubo excepción y no error lógico.
        return True

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para ID {session_id}: {e.message}", exc_info=True)
        return False
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para ID {session_id}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para ID {session_id}: {e}", exc_info=True)
        return False

async def delete_expired_sessions(ttl_seconds: int) -> int:
    operation_name = "delete_expired_sessions"
    table_name = TABLE_SESSIONS_CONVERSATION # Usar la constante correcta
    logger.info(f"Eliminando sesiones expiradas ({operation_name}) más antiguas que {ttl_seconds} segundos.")
    
    try:
        await supabase._ensure_initialized()
        expiration_time = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        
        # Importante: Supabase-py v2 no soporta .count() directamente en delete.
        # Se debe hacer un select con count y luego un delete, o el delete devuelve los datos borrados si se usa `returning`.
        # Para simplemente borrar y obtener el número de filas afectadas, es más complejo.
        # Alternativa 1: Seleccionar IDs y luego borrar por IDs.
        # Alternativa 2: Usar una función RPC en Supabase que devuelva el conteo.
        # Alternativa 3: Borrar y asumir que tuvo éxito si no hay error. El conteo de filas borradas no es directamente accesible.
        
        # Aquí optamos por borrar y no obtener el conteo de filas borradas directamente de la respuesta de delete.
        # Si necesitas el conteo, tendrás que hacer un SELECT count(*) antes y después si es crítico.
        api_response = supabase.client.from_(table_name).delete().lt('updated_at', expiration_time.isoformat()).execute()

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data) # Loguea el error
            return 0 # O manejar como un error
        
        # `api_response.data` para delete contendrá los registros eliminados si `returning` está habilitado.
        # Si no, podría ser una lista vacía. El número de filas afectadas no está en `api_response.count` para delete.
        # Por simplicidad, aquí no intentamos obtener el número de filas borradas.
        # Podrías hacer un SELECT count(*) antes y después si es crítico.
        logger.info(f"{operation_name} completado. No se puede determinar el número de filas borradas directamente desde la respuesta de delete sin 'returning'.")
        return -1 # Indicador de que no se contó.

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return 0
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return 0
    except Exception as e:
        logger.error(f"Excepción en {operation_name}: {e}", exc_info=True)
        return 0


# --- Funciones relacionadas con Calendly/Zoom (Adaptar si es necesario) ---
# Estas funciones pueden necesitar ser revisadas de manera similar si hacen llamadas directas a Supabase
# que no fueron cubiertas por las funciones genéricas de citas.

async def insert_appointment(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    # Esta función parece un alias o una versión específica de insert_appointment_record.
    # Asegúrate de que llama a la versión refactorizada o aplica el mismo patrón aquí.
    operation_name = "insert_appointment (específica)" # Distinguir de insert_appointment_record
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Insertando cita ({operation_name}) vía función específica: {appointment_data.get('calendly_event_uri')}")
    
    # Aquí deberías tener la lógica para mapear appointment_data a los campos de tu tabla.
    # Por ejemplo:
    # db_payload = {
    #    "patient_id": ..., "therapist_id": ..., "scheduled_date": ..., 
    #    "duration_minutes": ..., "status": ..., "calendly_event_uri": ..., 
    #    "zoom_meeting_id": ..., "zoom_join_url": ..., "metadata": ...
    # }
    # Asegúrate que `appointment_data` tenga los campos correctos o transfórmalos.

    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).insert(appointment_data).execute() # Asume que appointment_data está listo para la DB

        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
        appointment_obj = processed.get("appointment")
        appointment_id = appointment_obj.get("id") if isinstance(appointment_obj, dict) else None
        
        return {"success": processed["success"], "id": appointment_id, "appointment": appointment_obj, "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name}: {e.message}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name}: {e}", exc_info=True)
        return {"success": False, "id": None, "appointment": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}


async def get_appointment_by_calendly_uri(calendly_event_uri: str) -> Dict[str, Any]:
    if not calendly_event_uri: return {"success": False, "appointment": None, "error": "Calendly Event URI requerido"}
    operation_name = "get_appointment_by_calendly_uri"
    table_name = TABLE_APPOINTMENTS
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).select("*").eq('calendly_event_uri', calendly_event_uri).limit(1).execute()
        
        if isinstance(api_response.data, dict) and 'message' in api_response.data and 'code' in api_response.data:
            return await _handle_supabase_response(None, operation_name, table_name, error_obj=api_response.data)

        processed = await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
        return {"success": processed["success"], "appointment": processed.get("appointment"), "error": processed.get("error")}

    except (PostgrestAPIError, AuthApiError) as e: # Cambiado GotrueAPIError a AuthApiError
        logger.error(f"Error Supabase API en {operation_name} para URI {calendly_event_uri}: {e.message}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Supabase API: {e.message}", "details": str(e)}
    except httpx.RequestError as e:
        logger.error(f"Error de Red/Conexión en {operation_name} para URI {calendly_event_uri}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error de Red: {type(e).__name__}", "details": str(e)}
    except Exception as e:
        logger.error(f"Excepción en {operation_name} para URI {calendly_event_uri}: {e}", exc_info=True)
        return {"success": False, "appointment": None, "error": f"Error inesperado: {type(e).__name__}", "details": str(e)}

async def update_appointment_zoom_details(calendly_event_uri: str, zoom_meeting_id: str, zoom_join_url: str) -> Dict[str, Any]:
    operation_name = "update_appointment_zoom_details"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Actualizando detalles de Zoom para cita Calendly URI ({operation_name}): {calendly_event_uri}")
    if not all([calendly_event_uri, zoom_meeting_id, zoom_join_url]): return {"success": False, "error": "Datos incompletos para actualizar Zoom"}
    try:
        await supabase._ensure_initialized()
        update_data = {"zoom_meeting_id": zoom_meeting_id, "zoom_join_url": zoom_join_url}
        api_response = supabase.client.from_(table_name).update(update_data).eq('calendly_event_uri', calendly_event_uri).execute()
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
    except Exception as e: logger.error(f"Excepción en {operation_name}: {e}", exc_info=True); return {"success": False, "error": str(e)}

async def update_appointment_status(calendly_event_uri: str, status: str) -> Dict[str, Any]:
    operation_name = "update_appointment_status"
    table_name = TABLE_APPOINTMENTS
    logger.info(f"Actualizando estado de cita Calendly URI {calendly_event_uri} a: {status}")
    if not all([calendly_event_uri, status]): return {"success": False, "error": "Datos incompletos para actualizar estado de cita"}
    try:
        await supabase._ensure_initialized()
        api_response = supabase.client.from_(table_name).update({"status": status}).eq('calendly_event_uri', calendly_event_uri).execute()
        return await _handle_supabase_response(api_response.data, operation_name, table_name, return_key_singular="appointment")
    except Exception as e: logger.error(f"Excepción en {operation_name}: {e}", exc_info=True); return {"success": False, "error": str(e)}