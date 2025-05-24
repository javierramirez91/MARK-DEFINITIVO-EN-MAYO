import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from core.config import settings, logger

# Constantes de la API de Zoom
ZOOM_API_BASE_URL = "https://api.zoom.us/v2"
ZOOM_OAUTH_TOKEN_URL = "https://zoom.us/oauth/token"

# --- Cliente HTTP Asíncrono ---
async def get_zoom_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=ZOOM_API_BASE_URL, timeout=15.0)

# --- Autenticación (Ejemplo con Server-to-Server OAuth) ---
_zoom_access_token: Optional[str] = None
_zoom_token_expiry: Optional[datetime] = None
_token_lock = asyncio.Lock()

async def get_zoom_s2s_token() -> Optional[str]:
    """
    Obtiene un token de acceso Server-to-Server OAuth para Zoom.
    Maneja el refresco si el token está caducado o no existe.
    """
    global _zoom_access_token, _zoom_token_expiry

    async with _token_lock:
        now = datetime.now(timezone.utc)
        if not _zoom_access_token or not _zoom_token_expiry or _zoom_token_expiry <= (now + timedelta(seconds=60)):
            logger.info("Obteniendo/Refrescando token S2S de Zoom...")
            if not all([
                settings.ZOOM_ACCOUNT_ID, 
                settings.ZOOM_S2S_CLIENT_ID, 
                settings.ZOOM_S2S_CLIENT_SECRET
            ]):
                logger.error("Credenciales Server-to-Server OAuth de Zoom no configuradas.")
                return None

            auth_header = httpx.BasicAuth(settings.ZOOM_S2S_CLIENT_ID, settings.ZOOM_S2S_CLIENT_SECRET)
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        ZOOM_OAUTH_TOKEN_URL,
                        headers={"Authorization": f"Basic {auth_header.encode()}"},
                        params={"grant_type": "account_credentials", "account_id": settings.ZOOM_ACCOUNT_ID}
                    )
                    response.raise_for_status()
                    token_data = response.json()
                    _zoom_access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    _zoom_token_expiry = now + timedelta(seconds=expires_in)
                    logger.info(f"Token S2S de Zoom obtenido, expira en {expires_in} segundos.")

                except httpx.RequestError as e:
                    logger.error(f"Error de red al obtener token S2S de Zoom: {e}")
                    _zoom_access_token = None
                    _zoom_token_expiry = None
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error HTTP al obtener token S2S de Zoom: {e.response.status_code} - {e.response.text}")
                    _zoom_access_token = None
                    _zoom_token_expiry = None
                except Exception as e:
                    logger.error(f"Error inesperado al obtener token S2S de Zoom: {e}")
                    _zoom_access_token = None
                    _zoom_token_expiry = None

        return _zoom_access_token

# --- Funciones Principales del Servicio ---

async def create_zoom_meeting(topic: str, start_time: datetime, duration_minutes: int, timezone: str = "UTC", user_id: str = "me") -> Dict[str, Any]:
    """
    Crea una nueva reunión de Zoom usando autenticación S2S OAuth.
    """
    logger.info(f"Intentando crear reunión de Zoom: '{topic}'")
    token = await get_zoom_s2s_token()
    if not token:
        return {"success": False, "error": "Authentication failed"}

    meeting_details = {
        "topic": topic,
        "type": 2, # Scheduled meeting
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration": duration_minutes,
        "timezone": timezone,
        "settings": {
            "join_before_host": False,
            "mute_upon_entry": True,
            "participant_video": False,
            "host_video": False,
            "waiting_room": True
        }
    }

    async with await get_zoom_http_client() as client:
        try:
            response = await client.post(
                f"/users/{user_id}/meetings",
                headers={"Authorization": f"Bearer {token}"},
                json=meeting_details
            )
            response.raise_for_status()
            meeting_data = response.json()
            logger.info(f"Reunión de Zoom creada exitosamente: ID {meeting_data.get('id')}")
            return {"success": True, "meeting": meeting_data}

        except httpx.RequestError as e:
            logger.error(f"Error de red al crear reunión de Zoom: {e}")
            return {"success": False, "error": "Network error", "details": str(e)}
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP al crear reunión de Zoom: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP Error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            logger.error(f"Error inesperado al crear reunión de Zoom: {e}")
            return {"success": False, "error": "Unexpected error", "details": str(e)}

async def get_meeting_details(meeting_id: str) -> Dict[str, Any]:
    """Obtiene detalles de una reunión existente usando S2S OAuth."""
    logger.info(f"Obteniendo detalles para reunión Zoom ID: {meeting_id}")
    token = await get_zoom_s2s_token()
    if not token:
        return {"success": False, "error": "Authentication failed"}

    async with await get_zoom_http_client() as client:
        try:
            response = await client.get(
                f"/meetings/{meeting_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            meeting_data = response.json()
            logger.info(f"Detalles de reunión Zoom {meeting_id} obtenidos.")
            return {"success": True, "meeting": meeting_data}
        
        except httpx.RequestError as e:
            logger.error(f"Error de red al obtener detalles de reunión Zoom {meeting_id}: {e}")
            return {"success": False, "error": "Network error", "details": str(e)}
        except httpx.HTTPStatusError as e:
            # Zoom devuelve 404 si la reunión no existe o ya pasó y fue eliminada
            if e.response.status_code == 404:
                logger.warning(f"Reunión Zoom {meeting_id} no encontrada (404). Puede que no exista o haya expirado.")
                return {"success": False, "error": "Meeting not found", "status_code": 404}
            logger.error(f"Error HTTP al obtener detalles de reunión Zoom {meeting_id}: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP Error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            logger.error(f"Error inesperado al obtener detalles de reunión Zoom {meeting_id}: {e}")
            return {"success": False, "error": "Unexpected error", "details": str(e)}

async def cancel_zoom_meeting(meeting_id: str, occurrence_id: Optional[str] = None) -> Dict[str, Any]:
    """Cancela una reunión de Zoom usando S2S OAuth."""
    logger.info(f"Intentando cancelar reunión Zoom ID: {meeting_id}")
    token = await get_zoom_s2s_token()
    if not token:
        return {"success": False, "error": "Authentication failed"}

    params = {}
    if occurrence_id:
        params['occurrence_id'] = occurrence_id

    async with await get_zoom_http_client() as client:
        try:
            response = await client.delete(
                f"/meetings/{meeting_id}",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            # Zoom devuelve 204 No Content en caso de éxito
            if response.status_code == 204:
                 logger.info(f"Reunión Zoom {meeting_id} cancelada exitosamente.")
                 return {"success": True}
            else:
                # Si no es 204, intentar levantar error para capturar detalles
                response.raise_for_status() 
                # Si raise_for_status no lanza error (poco probable si no es 2xx), loguear
                logger.warning(f"Respuesta inesperada al cancelar reunión Zoom {meeting_id}: {response.status_code}")
                return {"success": False, "error": "Unexpected status code", "status_code": response.status_code, "details": response.text}

        except httpx.RequestError as e:
            logger.error(f"Error de red al cancelar reunión Zoom {meeting_id}: {e}")
            return {"success": False, "error": "Network error", "details": str(e)}
        except httpx.HTTPStatusError as e:
             # Zoom devuelve 404 si la reunión no existe
            if e.response.status_code == 404:
                logger.warning(f"No se pudo cancelar reunión Zoom {meeting_id} porque no fue encontrada (404). Puede que ya estuviera cancelada/expirada.")
                return {"success": False, "error": "Meeting not found", "status_code": 404}
            logger.error(f"Error HTTP al cancelar reunión Zoom {meeting_id}: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP Error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            logger.error(f"Error inesperado al cancelar reunión Zoom {meeting_id}: {e}")
            return {"success": False, "error": "Unexpected error", "details": str(e)}

# --- Funciones Adicionales (Añadir según sea necesario) --- 