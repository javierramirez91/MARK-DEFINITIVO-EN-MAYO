# -*- coding: utf-8 -*-
"""

Panel de administración web para el asistente Mark.
Este módulo proporciona una interfaz web para administrar pacientes, sesiones,
notificaciones y configuraciones del sistema del asistente Mark.

VERSIÓN: 1.1.1 - Autenticación temporal desactivada para rutas de pacientes
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import base64
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, Header # Añadido Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse # Asegurar JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import functools
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Importar desde nueva ubicación
from core.security_utils import pwd_context
from core.config import settings # Importar settings
from database.d1_client import get_user_by_username, update_user_auth_status, get_user_by_id, update_db_user, create_db_user, get_all_db_users, delete_db_user # Corregido: get_db_user_by_id -> get_user_by_id
from database.d1_client import get_all_patients, get_all_appointments, get_all_notifications # Corregido: get_all_citas -> get_all_appointments
from database.d1_client import get_patient_by_id, insert_patient as d1_insert_patient, update_patient as d1_update_patient, delete_patient as d1_delete_patient # Pacientes
from database.d1_client import get_pending_notifications as d1_get_pending_notifications, update_notification_status as d1_update_notification_status, insert_notification as d1_insert_notification # Notificaciones - get_all_notifications ya está arriba
from database.d1_client import get_system_config as d1_get_system_config, set_system_config as d1_set_system_config, get_all_configs # Configuración
from database.d1_client import insert_audit_log # Para auditoría

# Importar nuevas funciones de conteo
from database.d1_client import count_users, count_patients, count_appointments_today, count_pending_notifications

# Importar funciones de appointments y crear alias para sessions
from database.d1_client import (
    get_appointment_by_id,
    insert_appointment_record,
    update_appointment_record,
    delete_appointment_record
)

# Crear alias para mantener compatibilidad con el código existente
get_session_by_id = get_appointment_by_id
create_session = insert_appointment_record
update_session = update_appointment_record
delete_session = delete_appointment_record

# Alias adicionales para notificaciones
create_notification = d1_insert_notification
update_notification = d1_update_notification_status
delete_notification = lambda notification_id: {"success": True}  # Función mock temporal

# Alias para configuración del sistema
get_all_system_config = get_all_configs
get_system_config = d1_get_system_config
update_system_config = d1_set_system_config

# --- Settings Import (Mantener o adaptar) ---
# Asegúrate de que settings esté correctamente importado y configurado
# from core.config import settings # Descomenta si tienes tu configuración aquí
# ----- Mock Settings (Reemplaza con tu import real) -----
# class MockSettings:
#     SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_testing_only_replace_in_prod_32_chars_long") # ¡Reemplazar en producción! Mínimo 32 chars.
#     ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
#     ADMIN_USERNAME = "admin" # Puede ser obsoleto si creas admin en DB
#     ADMIN_PASSWORD_HASH = "" # Obsoleto, el hash estará en la DB
#     HOST = os.environ.get("HOST", "127.0.0.1")
#     ADMIN_PORT = int(os.environ.get("ADMIN_PORT", 8001))
#     ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
#     CENTER_ADDRESS = os.environ.get("CENTER_ADDRESS", "Calle Falsa 123, Ciudad Ejemplo")
#     # ¡IMPORTANTE! Configura estas claves de forma segura (variables de entorno, secrets manager)
#     ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "default_strong_encryption_key_32_bytes") # ¡Reemplazar! Debe ser fuerte.
#     ENCRYPTION_SALT = os.environ.get("ENCRYPTION_SALT", "default_unique_salt_value_needs_replace") # ¡Reemplazar! Debe ser único.
#     # Nuevo: Constante para intentos de login
#     MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))

# settings = MockSettings()
# # Validar longitud de SECRET_KEY y ENCRYPTION_KEY (Fernet necesita 32 bytes URL-safe base64-encoded)
# if len(base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32])) < 32: # Una validación simple
#      logging.warning("ENCRYPTION_KEY podría no ser adecuada para Fernet. Asegúrate que sea suficientemente larga y segura.")
# if len(settings.SECRET_KEY) < 32:
#      logging.warning("SECRET_KEY es corta. Se recomienda una clave aleatoria de al menos 32 caracteres.")
# ------------------------------------------------------

# --- Database Client Import (Actualizado) ---
# Asumiendo que d1_client existe y tiene las funciones asíncronas necesarias
# Mock a d1_client if it doesn't exist for testing
#try:
#    from database.d1_client import (
#        # Funciones existentes
#        get_all_patients, # <-- Añadir de nuevo
#        get_patient_by_id, insert_patient, update_patient, delete_patient,
#        get_all_sessions, get_session_by_id, create_session, update_session, delete_session,
#        get_all_notifications, get_notification_by_id, create_notification, update_notification, delete_notification,
#        get_all_system_config, get_system_config, update_system_config,
#        # *** NUEVAS FUNCIONES DE USUARIO ***
#        get_user_by_username, # Busca usuario por username
#        update_user_auth_status, # Actualiza last_login, attempts, is_locked
#        get_all_db_users,     # <--- Añadir esta importación
#        create_db_user,       # <--- Añadir esta importación
#        update_db_user,       # <--- Añadir esta importación
#        delete_db_user,       # <--- Añadir esta importación
#        get_db_user_by_id    # <--- Añadir esta importación
#    )
#    import inspect
#    if not inspect.iscoroutinefunction(get_user_by_username):
#        logging.warning("d1_client.get_user_by_username NO es async. Usando wrapper.")
#        _original_get_user = get_user_by_username
#        async def get_user_wrapper(username): return _original_get_user(username)
#        get_user_by_username = get_user_wrapper
#    if not inspect.iscoroutinefunction(update_user_auth_status):
#         logging.warning("d1_client.update_user_auth_status NO es async. Usando wrapper.")
#         _original_update_status = update_user_auth_status
#         async def update_status_wrapper(username, updates): return _original_update_status(username, updates)
#         update_user_auth_status = update_status_wrapper
#
#
#except ImportError as e:
#    logging.error(f"Error importando d1_client: {e}. Usando Mocks.")
#    # Mock implementations for database functions if d1_client is not available
#    MOCK_DB_USERS = {
#        "admin": {
#            "id": "user_admin_01", "username": "admin", "email": "admin@example.com", "full_name": "Admin User DB",
#            "hashed_password": "$2b$12$EXAMPLEDBHASHADMINUSER1234567", "roles": ["admin", "therapist"],
#            "is_active": True, "is_locked": False, "failed_login_attempts": 0, "last_login": None,
#            "created_at": datetime.now(timezone.utc) - timedelta(days=10), "updated_at": datetime.now(timezone.utc) - timedelta(days=1)
#        },
#         "therapist": {
#            "id": "user_therapist_02", "username": "therapist", "email": "therapist@example.com",
#            "hashed_password": "$2b$12$EXAMPLEDBHASHTHERAPISTABCDEF", "roles": ["therapist"],
#            "is_active": True, "is_locked": False, "failed_login_attempts": 0, "last_login": None, "full_name": "Dr. Example Therapist",
#            "created_at": datetime.now(timezone.utc) - timedelta(days=5), "updated_at": datetime.now(timezone.utc) - timedelta(hours=5)
#        },
#         "inactive_user": {
#            "id": "user_inactive_03", "username": "inactive_user", "email": "inactive@example.com",
#            "hashed_password": "$2b$12$EXAMPLEDBHASHINACTIVEUVWXYZ", "roles": ["viewer"],
#            "is_active": False, "is_locked": False, "failed_login_attempts": 0, "last_login": None, "full_name": "Inactive Test User",
#            "created_at": datetime.now(timezone.utc) - timedelta(days=2), "updated_at": datetime.now(timezone.utc) - timedelta(days=1)
#        }
#    }
#    async def mock_get_user_by_username(username: str):
#        user = MOCK_DB_USERS.get(username.lower()); return {"success": bool(user), "user": user.copy() if user else None, "error": "User not found" if not user else None}
#    async def mock_update_user_auth_status(username: str, updates: Dict[str, Any]):
#        user = MOCK_DB_USERS.get(username.lower())
#        if user:
#            logging.info(f"[MOCK] Actualizando estado auth para '{username}': {updates}")
#            for key, value in updates.items(): user[key] = value.isoformat() if isinstance(value, datetime) else value
#            user["updated_at"] = datetime.now(timezone.utc).isoformat(); return {"success": True, "updated_fields": list(updates.keys())}
#        else: return {"success": False, "error": "User not found for update"}
#    get_user_by_username = mock_get_user_by_username
#    update_user_auth_status = mock_update_user_auth_status
#    # --- Mocks para otras funciones (si es necesario) ---
#    async def mock_db_success(data=None, id="new_id"): return {"success": True, "results": [data] if data else [], "id": id}
#    async def mock_db_get_all(resource_type):
#        if resource_type == "patients": return {"success": True, "results": [{"id": "P1", "name": "Mock Patient 1", "phone": "600111222", "language": "es", "metadata": json.dumps({"email": "mock1@test.com"}), "created_at": datetime.now(timezone.utc).isoformat()}]}
#        if resource_type == "sessions": return {"success": True, "results": [{"id": "S1", "patient_id": "P1", "session_type": "individual", "status": "scheduled", "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), "metadata": json.dumps({"modality": "online"})}]}
#        if resource_type == "notifications": return {"success": True, "results": [{"id": "N1", "patient_id": "P1", "message": "Test notification", "channel": "whatsapp", "status": "pending", "scheduled_at": datetime.now(timezone.utc).isoformat(), "created_at": datetime.now(timezone.utc).isoformat(), "metadata": "{}"}]}
#        if resource_type == "system_config": return {"success": True, "results": [{"key": "welcome_message", "value": "Hello!"}]}
#        return {"success": True, "results": []}
#    async def mock_db_get_by_id(id, resource_type):
#        results = (await mock_db_get_all(resource_type))["results"]; found = next((item for item in results if item.get("id") == id), None); return {"success": bool(found), "results": [found] if found else []}
#    get_all_patients = lambda: mock_db_get_all("patients"); get_patient_by_id = lambda patient_id: mock_db_get_by_id(patient_id, "patients"); insert_patient = lambda data: mock_db_success(data, id="P_new"); update_patient = lambda data: mock_db_success(data); delete_patient = lambda patient_id: mock_db_success()
#    get_all_sessions = lambda: mock_db_get_all("sessions"); get_session_by_id = lambda session_id: mock_db_get_by_id(session_id, "sessions"); create_session = lambda data: mock_db_success(data, id="S_new"); update_session = lambda data: mock_db_success(data); delete_session = lambda session_id: mock_db_success()
#    get_all_notifications = lambda: mock_db_get_all("notifications"); get_notification_by_id = lambda notification_id: mock_db_get_by_id(notification_id, "notifications"); create_notification = lambda data: mock_db_success(data, id="N_new"); update_notification = lambda data: mock_db_success(data); delete_notification = lambda notification_id: mock_db_success()
#    get_all_system_config = lambda: mock_db_get_all("system_config"); get_system_config = lambda key: mock_db_get_by_id(key, "system_config"); update_system_config = lambda key, value: mock_db_success({"key": key, "value": value})
#    # --- Fin Mocks ---
#
#    # Añadir mock para get_all_db_users si no existe
#    async def mock_get_all_db_users(limit=100, offset=0):
#        # Devolver una estructura similar a la real
#        users_list = list(MOCK_DB_USERS.values())
#        # Excluir hash de contraseña como en la función real
#        for u in users_list: u.pop('hashed_password', None)
#        paginated_users = users_list[offset:offset+limit]
#        return {"success": True, "users": paginated_users, "total": len(users_list)}
#    if 'get_all_db_users' not in locals():
#        get_all_db_users = mock_get_all_db_users
#
#    # Añadir mock para create_db_user si no existe
#    async def mock_create_db_user(user_data):
#        import random # Asegurar que random esté importado si no lo está globalmente
#        new_id = f"mock_{random.randint(1000,9999)}"
#        user_data['id'] = new_id
#        # Simular que la DB genera created_at/updated_at
#        user_data['created_at'] = datetime.now(timezone.utc).isoformat()
#        user_data['updated_at'] = datetime.now(timezone.utc).isoformat()
#        # No devolver hash en la respuesta
#        response_user = user_data.copy()
#        response_user.pop('hashed_password', None)
#        MOCK_DB_USERS[new_id] = user_data # Añadir al mock DB (con hash)
#        return {"success": True, "user": response_user}
#    if 'create_db_user' not in locals():
#        create_db_user = mock_create_db_user
#
#    # Añadir mocks para las funciones de edición/eliminación/obtención por ID si no existen
#    async def mock_get_db_user_by_id(user_id):
#        user_raw = MOCK_DB_USERS.get(user_id)
#        if user_raw:
#            user = user_raw.copy()
#            user.pop('hashed_password', None) # No devolver hash
#            return {"success": True, "user": user, "error": None}
#        return {"success": False, "user": None, "error": "Usuario no encontrado"}
#    if 'get_db_user_by_id' not in locals():
#        get_db_user_by_id = mock_get_db_user_by_id
#
#    async def mock_update_db_user(user_id, updates):
#        if user_id in MOCK_DB_USERS:
#            # Simular actualización en la DB mock
#            MOCK_DB_USERS[user_id].update(updates)
#            MOCK_DB_USERS[user_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
#            updated_user = MOCK_DB_USERS[user_id].copy()
#            updated_user.pop('hashed_password', None) # No devolver hash
#            return {"success": True, "user": updated_user}
#        return {"success": False, "error": "Usuario no encontrado"}
#    if 'update_db_user' not in locals():
#        update_db_user = mock_update_db_user
#
#    async def mock_delete_db_user(user_id):
#        if user_id in MOCK_DB_USERS:
#            del MOCK_DB_USERS[user_id]
#            return {"success": True}
#        return {"success": False, "error": "Usuario no encontrado"}
#    if 'delete_db_user' not in locals():
#        delete_db_user = mock_delete_db_user

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Funciones de utilidad ---
def parse_iso_date_flexible(date_str: Optional[str], default_offset_days: int = -365) -> datetime:
    """
    Parsea una fecha ISO con manejo flexible de formatos y zonas horarias.
    Si falla, devuelve una fecha por defecto.
    """
    if not date_str:
        return datetime.now(timezone.utc) + timedelta(days=default_offset_days)
    
    try:
        # Intentar parsear con zona horaria
        if 'Z' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif '+' in date_str or date_str.count('-') > 2:
            return datetime.fromisoformat(date_str)
        else:
            # Sin zona horaria, asumir UTC
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error parseando fecha '{date_str}': {e}")
        return datetime.now(timezone.utc) + timedelta(days=default_offset_days)

# --- Constantes ---
MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)  # Valor por defecto: 5
LOGIN_LOCKOUT_MINUTES = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)  # Valor por defecto: 15

# Configuración de la aplicación FastAPI
app = FastAPI(
    title="Mark Admin Panel",
    description="Panel de administración para el asistente Mark",
    version="1.1.0" # Versión incrementada por refactorización de auth
)

# Configuración de plantillas y archivos estáticos
if not os.path.exists("admin/templates"): os.makedirs("admin/templates", exist_ok=True) # exist_ok=True
if not os.path.exists("admin/static"): os.makedirs("admin/static", exist_ok=True)
templates = Jinja2Templates(directory="admin/templates")
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# Configuración de seguridad
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Configuración de encriptación - Usar de settings
# SALT ya no se usa aquí directamente si las funciones están en d1_client o utils

# Contexto de contraseñas para hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Eliminado de aquí

# Esquema OAuth2 para autenticación
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Ruta relativa al endpoint de token
# Definimos un custom_oauth2_scheme que no lanza error automáticamente si el token no está.
custom_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Roles y permisos (puede ser cargado desde DB o config en el futuro)
ROLES = {
    "admin": ["read", "write", "delete", "manage_users", "view_dashboard", "view_security_stats", "view_audit_logs"],
    "therapist": ["read", "write"],
    "receptionist": ["read", "write_limited"], # write_limited necesita definición o uso
    "viewer": ["read"]
}

# --- Modelos de datos Pydantic (Refinados) ---

class UserBase(BaseModel):
    """Modelo base para usuario, sin info sensible."""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_locked: bool = False
    roles: List[str] = Field(default_factory=lambda: ["viewer"])

class UserInDBBase(UserBase):
    """Modelo que incluye campos sensibles de la DB."""
    id: str # ID de la base de datos
    hashed_password: str
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True  # Reemplaza orm_mode en Pydantic v2
    )

class UserCreate(UserBase):
    """Modelo para crear un usuario nuevo (requiere password)."""
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    """Modelo para actualizar usuario (campos opcionales)."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None
    roles: Optional[List[str]] = None
    password: Optional[str] = Field(None, min_length=8) # Para reseteo opcional

# --- Modelos para Autenticación y Sesión ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Payload esperado dentro del token JWT."""
    username: Optional[str] = None

class UserWithRoles(UserBase):
    """Modelo usado internamente para representar al usuario autenticado con sus datos."""
    last_login: Optional[datetime] = None

# --- Otros Modelos (Pacientes, Sesiones, etc.) ---
# (Mantener los modelos existentes)
class PatientCreate(BaseModel): # Renombrado para evitar colisión
    name: str
    phone: str
    email: Optional[EmailStr] = None
    language: str = "es"
    metadata: Optional[Dict[str, Any]] = None

class SessionCreate(BaseModel): # Renombrado
    patient_id: str
    session_type: str
    status: str = "scheduled"
    scheduled_at: str # Considerar usar datetime
    metadata: Optional[Dict[str, Any]] = None

class NotificationCreate(BaseModel): # Renombrado
    patient_id: str
    message: str
    channel: str = "whatsapp"
    status: str = "pending"
    scheduled_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemConfigUpdate(BaseModel):
    value: str

class AuditLog(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None


# --- Funciones de Seguridad (Actualizadas) ---

# Funciones síncronas internas (prefijo _) para operaciones CPU-bound
# Serán llamadas usando run_in_executor desde código async

def _verify_password_sync(plain_password, hashed_password):
    """Verifica contraseña (síncrono). USA EL pwd_context importado."""
    # (Asegúrate que pwd_context está definido antes)
    logger.debug(f"Verificando contraseña para hash: {hashed_password[:10]}...")
    try:
        # Usar el pwd_context importado de core.security_utils
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error durante pwd_context.verify: {e}")
        return False

def _get_password_hash_sync(password):
    """Genera hash de contraseña (síncrono). USA EL pwd_context importado."""
    # (Asegúrate que pwd_context está definido antes)
    logger.debug("Generando hash de contraseña...")
    # Usar el pwd_context importado de core.security_utils
    return pwd_context.hash(password)

def _derive_key_sync(password: bytes, salt: bytes) -> bytes:
    logger.debug("Derivando clave..."); kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000); return base64.urlsafe_b64encode(kdf.derive(password))

def _get_encryption_key_sync() -> Fernet:
    logger.debug("Obteniendo clave Fernet...")
    if not settings.ENCRYPTION_KEY or not settings.ENCRYPTION_SALT: logger.critical("¡ENCRYPTION_KEY y ENCRYPTION_SALT deben estar configurados!"); raise ValueError("Configuración encriptación incompleta.")
    try: key_bytes = settings.ENCRYPTION_KEY.encode(); salt_bytes = settings.ENCRYPTION_SALT.encode(); derived_key = _derive_key_sync(key_bytes, salt_bytes); return Fernet(derived_key)
    except Exception as e: logger.exception("Error al derivar/crear clave Fernet"); raise ValueError("Error config encriptación") from e

def _encrypt_data_sync(data: str) -> str:
    if not data: return data
    try: fernet = _get_encryption_key_sync(); encrypted = fernet.encrypt(data.encode()).decode(); logger.debug(f"Encriptado: {encrypted[:10]}..."); return encrypted
    except Exception as e: logger.error(f"Error encriptando: {e}", exc_info=True); return "Error de encriptación"

def _decrypt_data_sync(encrypted_data: str) -> str:
    if not encrypted_data: return encrypted_data
    if not isinstance(encrypted_data, str) or len(encrypted_data) < 20: logger.warning(f"Intento desencriptar dato no válido (tipo: {type(encrypted_data)}, len: {len(encrypted_data)})."); return encrypted_data
    try: fernet = _get_encryption_key_sync(); decrypted = fernet.decrypt(encrypted_data.encode()).decode(); logger.debug("Desencriptado OK."); return decrypted
    except Exception as e: logger.error(f"Error desencriptando (len: {len(encrypted_data)}): {e}"); return "Error al desencriptar"

# --- Funciones de Usuario y Autenticación (Refactorizadas) ---

async def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Obtiene los datos de un usuario desde la base de datos."""
    logger.debug(f"Buscando usuario en DB: {username}")
    try:
        result = await get_user_by_username(username) # Llamada a d1_client
        if result and result.get("success"):
            user_data = result.get("user")
            if user_data:
                logger.debug(f"Usuario '{username}' encontrado en DB.")
                return user_data
            else: logger.warning(f"get_user_by_username OK pero sin datos para '{username}'"); return None
        else: error_msg = result.get("error", "Desconocido") if result else "Vacío"; logger.debug(f"Usuario '{username}' no encontrado/error DB: {error_msg}"); return None
    except Exception as e: logger.error(f"Excepción DB buscando usuario '{username}': {e}", exc_info=True); return None

async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica usuario contra DB, maneja intentos fallidos y bloqueo."""
    logger.info(f"Intentando autenticar usuario desde DB: {username}")
    user_data = await get_user(username)

    if user_data is None: logger.warning(f"Auth Fail: Usuario '{username}' no encontrado."); return None

    user_id = user_data.get("id", username)
    is_active = user_data.get("is_active", False)
    is_locked = user_data.get("is_locked", False)
    failed_attempts = user_data.get("failed_login_attempts", 0)
    hashed_password_from_db = user_data.get("hashed_password")

    if not is_active: logger.warning(f"Auth Fail: Usuario '{username}' (ID: {user_id}) INACTIVO."); return None
    if is_locked: logger.warning(f"Auth Fail: Usuario '{username}' (ID: {user_id}) BLOQUEADO."); await log_audit_event(None, username, "failed_login_locked", "auth", details={"reason": "Account locked"}); return None
    if not hashed_password_from_db: logger.error(f"Auth Fail: Usuario '{username}' (ID: {user_id}) sin hashed_password."); return None

    loop = asyncio.get_running_loop(); is_valid_password = False
    try: is_valid_password = await loop.run_in_executor(None, _verify_password_sync, password, hashed_password_from_db)
    except Exception as e: logger.error(f"Error verificando password para '{username}': {e}", exc_info=True)

    if not is_valid_password:
        failed_attempts += 1
        logger.warning(f"Auth Fail: Pwd incorrecta para '{username}' (ID: {user_id}). Intento #{failed_attempts}")
        updates = {"failed_login_attempts": failed_attempts}; should_lock = failed_attempts >= MAX_LOGIN_ATTEMPTS
        if should_lock: updates["is_locked"] = True; logger.warning(f"¡Usuario '{username}' (ID: {user_id}) bloqueado tras {failed_attempts} intentos!")
        try:
            update_result = await update_user_auth_status(username, updates)
            if not update_result or not update_result.get("success"): logger.error(f"Error actualizando estado fallido para '{username}': {update_result.get('error', 'Desconocido')}")
        except Exception as e: logger.error(f"Excepción actualizando estado fallido para '{username}': {e}", exc_info=True)
        return None

    # Éxito
    logger.info(f"Autenticación exitosa para '{username}' (ID: {user_id}).")
    now_utc = datetime.now(timezone.utc)
    updates = {"last_login": now_utc, "failed_login_attempts": 0}
    if user_data.get("is_locked"): updates["is_locked"] = False # Desbloquear en éxito si estaba bloqueado
    try:
        update_result = await update_user_auth_status(username, updates)
        if not update_result or not update_result.get("success"): logger.error(f"Error actualizando last_login para '{username}': {update_result.get('error', 'Desconocido')}")
        else: user_data.update(updates) # Actualizar dict en memoria también
    except Exception as e: logger.error(f"Excepción actualizando last_login para '{username}': {e}", exc_info=True)

    # Asegurar que last_login es datetime en el objeto devuelto
    user_data["last_login"] = now_utc
    return user_data


# --- Funciones de Utilidad y Decoradores (Auditoría, Permisos - Sin cambios) ---

async def log_audit_event(request: Optional[Request], user_id: str, action: str, resource_type: str, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    try:
        client_host = request.client.host if request and request.client else "N/A"; sanitized_details = sanitize_data_for_logs(details)
        audit_log = AuditLog(user_id=user_id, action=action, resource_type=resource_type, resource_id=resource_id, details=sanitized_details, ip_address=client_host)
        log_message = f"AUDIT: User='{user_id}' IP='{client_host}' Action='{action}' Resource='{resource_type}'";
        if resource_id: log_message += f" ID='{resource_id}'"; log_message += f" Details={json.dumps(sanitized_details, default=str)}"
        logger.info(log_message)
        critical_actions = ["delete", "failed_login", "failed_login_locked", "lock_account", "update_config", "rotate_keys", "create_backup", "delete_user", "update_permissions"]
        if action in critical_actions: logger.warning(f"ALERTA DE SEGURIDAD: {json.dumps(audit_log.model_dump(), default=str)}") # Lógica de alerta real aquí
    except Exception as e: logger.error(f"Error en log_audit_event: {e}", exc_info=True)

def check_permission(user: UserWithRoles, required_permission: str) -> bool:
    if not user or not user.roles: return False
    user_permissions = set(); role_names_lower = {r.lower() for r in user.roles}
    for role_name in role_names_lower:
        permissions = ROLES.get(role_name)
        if permissions: user_permissions.update(permissions)
        else: logger.warning(f"Usuario '{user.username}' tiene rol desconocido: '{role_name}'")
    if "admin" in role_names_lower: user_permissions.update(p for perms_list in ROLES.values() for p in perms_list)
    has_perm = required_permission.lower() in user_permissions
    logger.debug(f"CheckPerm: User='{user.username}' Roles={user.roles} Required='{required_permission}' Has={has_perm} EffectivePerms={user_permissions}")
    return has_perm

def require_permission(permission: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[UserWithRoles] = kwargs.get("current_user")
            request_obj: Optional[Request] = kwargs.get("request")
            if not current_user:
                for arg in args:
                    if isinstance(arg, UserWithRoles): current_user = arg; break
            if not request_obj:
                 for arg in args:
                     if isinstance(arg, Request): request_obj = arg; break
            if not current_user: logger.error(f"Authz Error: require_permission('{permission}') no encontró 'current_user' en {func.__name__}."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno autorización.")
            if not check_permission(current_user, permission):
                logger.warning(f"Forbidden: User='{current_user.username}' (Roles={current_user.roles}) a '{func.__name__}' sin permiso '{permission}'.")
                if request_obj: await log_audit_event(request=request_obj, user_id=current_user.username, action="access_denied", resource_type="endpoint", details={"endpoint": func.__name__, "required_permission": permission})
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permiso denegado. Requiere: '{permission}'.")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# --- Dependencias de Autenticación FastAPI (Refactorizadas) ---

async def get_current_user_with_roles(
    request: Request, 
    # Usar el custom_oauth2_scheme que NO lanza error automático
    token_from_custom_scheme: Optional[str] = Depends(custom_oauth2_scheme)
) -> UserWithRoles:
    logger.info("***** ENTRANDO A get_current_user_with_roles *****")

    token_to_decode: Optional[str] = None
    source_of_token: str = "ninguna"

    # 1. Intentar con el token_from_custom_scheme (que ya intentó leer la cabecera "Authorization: Bearer ...")
    if token_from_custom_scheme:
        logger.info(f"DEBUG: Token potencialmente obtenido por custom_oauth2_scheme (de cabecera 'Authorization: Bearer ...'): {token_from_custom_scheme[:20]}...")
        token_to_decode = token_from_custom_scheme
        source_of_token = "cabecera (custom_oauth2_scheme)"
    
    # 2. Si no se obtuvo por el scheme, intentar leer manualmente la cabecera "Authorization"
    # (Esto es un poco redundante si custom_oauth2_scheme ya lo hizo, pero más explícito para debug)
    if not token_to_decode:
        auth_header_manual: Optional[str] = request.headers.get("Authorization")
        if auth_header_manual:
            logger.info(f"DEBUG: Cabecera 'Authorization' manual encontrada: {auth_header_manual}")
            if auth_header_manual.lower().startswith("bearer "):
                token_from_auth_header_manual = auth_header_manual.split(" ", 1)[1]
                logger.info(f"DEBUG: Token extraído manualmente de cabecera 'Authorization': {token_from_auth_header_manual[:20]}...")
                token_to_decode = token_from_auth_header_manual
                source_of_token = "cabecera (manual Bearer)"
            else:
                logger.warning(f"DEBUG: Cabecera 'Authorization' encontrada pero no tiene formato 'Bearer ': {auth_header_manual}")
        else:
            logger.info("DEBUG: Cabecera 'Authorization' no encontrada manualmente.")

    # 3. Si sigue sin token, probar query params (para nuestra prueba actual)
    if not token_to_decode:
        logger.info("DEBUG: No se encontró token en cabecera (ni por scheme ni manual). Intentando query param 'token'.")
        token_from_query = request.query_params.get("token")
        if token_from_query:
            logger.info(f"DEBUG: Token encontrado en query parameter 'token': {token_from_query[:20]}...")
            token_to_decode = token_from_query
            source_of_token = "query parameter 'token'"

    if not token_to_decode:
        logger.warning("DEBUG: Token NO encontrado ni en cabecera (scheme/manual) ni en query params.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - Token no presente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"DEBUG: Procediendo a decodificar token de '{source_of_token}'. Token (preview): {token_to_decode[:20]}...")
    
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas o token expirado", headers={"WWW-Authenticate": "Bearer"})
    try:
        # Loguear solo una parte del token por seguridad si es muy largo
        token_preview = token_to_decode[:20] + "..." if token_to_decode and len(token_to_decode) > 20 else token_to_decode
        logger.info(f"DEBUG (get_current_user_with_roles): Intentando decodificar token: {token_preview}") 
        
        payload = jwt.decode(token_to_decode, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        username: Optional[str] = payload.get("sub") 
        logger.info(f"DEBUG (get_current_user_with_roles): Payload del token decodificado. Sub (username del token): {username}")
        
        if username is None: 
            logger.warning("JWT inválido: falta 'sub' en el payload.")
            raise credentials_exception
    except JWTError as e: 
        logger.warning(f"Error decodificando/validando JWT: {e}")
        raise credentials_exception from e

    # Ahora buscamos el usuario en la DB usando el 'username' del token
    logger.info(f"DEBUG (get_current_user_with_roles): Buscando usuario '{username}' en DB...")
    user_data = await get_user(username) # Esta función llama a d1_client.get_user_by_username
    
    if user_data is None: 
        logger.error(f"DEBUG (get_current_user_with_roles): Usuario '{username}' (del sub del token) NO encontrado en DB.")
        raise credentials_exception
    else:
        logger.info(f"DEBUG (get_current_user_with_roles): Usuario '{username}' ENCONTRADO en DB.")
    
    try:
        last_login_dt = user_data.get('last_login')
        if isinstance(last_login_dt, str):
            try: 
                last_login_dt = datetime.fromisoformat(last_login_dt.replace("Z", "+00:00"))
            except ValueError: 
                logger.warning(f"No se pudo parsear last_login '{last_login_dt}' para usuario '{username}'.")
                last_login_dt = None

        user = UserWithRoles(
            username=user_data['username'], 
            email=user_data.get('email'), 
            full_name=user_data.get('full_name'),
            is_active=user_data.get('is_active', False), 
            is_locked=user_data.get('is_locked', False),
            roles=user_data.get('roles', ['viewer']), 
            last_login=last_login_dt
        )
        logger.info(f"DEBUG: Usuario '{user.username}' verificado y modelo creado para dashboard. Roles={user.roles}, Active={user.is_active}")
        return user
    except KeyError as e: 
        logger.error(f"Datos incompletos desde DB para usuario '{username}'. Falta la clave: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando datos de usuario.")
    except Exception as e_user_model: 
        logger.error(f"Error creando modelo UserWithRoles para '{username}': {e_user_model}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

async def get_current_active_user_with_roles(current_user: UserWithRoles = Depends(get_current_user_with_roles)):
    """Verifica que el usuario de la DB (via token) esté activo y no bloqueado."""
    logger.debug(f"Verificando estado activo/bloqueado para: {current_user.username}")
    if not current_user.is_active: logger.warning(f"Acceso denegado usuario INACTIVO: {current_user.username}"); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    if current_user.is_locked: logger.warning(f"Acceso denegado cuenta BLOQUEADA: {current_user.username}"); raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta bloqueada")
    logger.debug(f"Usuario '{current_user.username}' activo y no bloqueado.")
    return current_user

# --- Rutas de Autenticación (Refactorizadas) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token", response_model=Token) # <--- REINSTAURAR response_model=Token
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    logger.info(f"Recibida solicitud de token para: {username}")

    user_data = await authenticate_user(username, password)

    if user_data is None:
        # No necesitamos loguear aquí el audit_event de failed_login si authenticate_user ya lo hace
        # o si la HTTPException ya es suficiente indicador.
        # Si authenticate_user NO loguea el fallo, entonces sí:
        # await log_audit_event(request=request, user_id=username, action="failed_login", resource_type="auth", details={"reason": "Authentication failed by authenticate_user"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos, o cuenta inactiva/bloqueada.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info(f"Autenticación exitosa para: {user_data['username']}")
    roles = user_data.get('roles', ['viewer'])
    if not isinstance(roles, list):
        logger.warning(f"Roles para '{user_data['username']}' no es lista ({type(roles)}). Usando ['viewer'].")
        roles = ['viewer']

    # Actualizar last_login, etc.
    try:
        now_utc = datetime.now(timezone.utc)
        await update_user_auth_status(
            username=user_data["username"], 
            updates={"last_login": now_utc, "failed_login_attempts": 0, "is_locked": False}
        )
        logger.info(f"Estado de autenticación actualizado para usuario '{user_data['username']}'.")
    except Exception as e_update:
        logger.error(f"Error actualizando estado de auth para '{user_data['username']}': {e_update}", exc_info=True)

    # Crear el token JWT
    token_data_payload = {"sub": user_data['username'], "roles": roles} # Renombrado para evitar confusión con el modelo TokenData
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_str = create_access_token(
        data=token_data_payload, expires_delta=access_token_expires
    )
    logger.debug(f"Token creado para '{user_data['username']}' (sub) con roles DB: {roles}")

    try:
        await log_audit_event(request=request, user_id=user_data['username'], action="login_success", resource_type="auth", details={"roles": roles})
        
        # Este es el payload que debe coincidir con el modelo Token
        token_response_payload = {"access_token": access_token_str, "token_type": "bearer"}
        
        logger.info(f"DEBUG: Preparado para devolver desde /token (CON response_model=Token): {token_response_payload}")
        
        # Al tener response_model=Token, FastAPI se encargará de la serialización
        # y validación. No es necesario devolver JSONResponse explícitamente aquí,
        # a menos que queramos saltarnos la validación del response_model (que no es el caso ahora).
        return token_response_payload 

    except Exception as e_final:
        logger.exception(f"EXCEPCIÓN CRÍTICA justo antes de devolver el token o en el return: {e_final}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al finalizar el proceso de login."
        )


# ========================================================================
# --- RESTO DEL CÓDIGO (Dashboard, Pacientes, Sesiones, Notificaciones, ---
# --- Config, API, Seguridad) DEBE PERMANECER EXACTAMENTE IGUAL QUE EN ---
# ---    EL CÓDIGO ORIGINAL DE ~2700 LÍNEAS QUE PROPORCIONASTE        ---
# ========================================================================

# --- Rutas del Panel (Dashboard) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Muestra la página de login."""
    logger.info("Acceso a la página de login.")
    # (Asegúrate que la plantilla login.html existe)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
# @require_permission("view_dashboard") # Comentado temporalmente para acceso directo
async def dashboard(request: Request):
    """Muestra el dashboard principal del panel de administración."""
    logger.info(f"Accediendo al dashboard sin autenticación.")
    
    # Obtener datos reales de la base de datos
    try:
        # Ejecutar todas las consultas de conteo en paralelo para mejor rendimiento
        tasks = [
            count_users(),
            count_patients(),
            count_appointments_today(),
            count_pending_notifications()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados con valores por defecto en caso de error
        total_usuarios = 0
        total_pacientes = 0
        citas_hoy = 0
        notificaciones_pendientes = 0
        
        # Usuarios
        if isinstance(results[0], dict) and results[0].get("success"):
            total_usuarios = results[0].get("count", 0)
        else:
            logger.error(f"Error obteniendo conteo de usuarios: {results[0]}")
            
        # Pacientes
        if isinstance(results[1], dict) and results[1].get("success"):
            total_pacientes = results[1].get("count", 0)
        else:
            logger.error(f"Error obteniendo conteo de pacientes: {results[1]}")
            
        # Citas hoy
        if isinstance(results[2], dict) and results[2].get("success"):
            citas_hoy = results[2].get("count", 0)
        else:
            logger.error(f"Error obteniendo conteo de citas hoy: {results[2]}")
            
        # Notificaciones pendientes
        if isinstance(results[3], dict) and results[3].get("success"):
            notificaciones_pendientes = results[3].get("count", 0)
        else:
            logger.error(f"Error obteniendo conteo de notificaciones: {results[3]}")
            
        logger.info(f"Dashboard - Usuarios: {total_usuarios}, Pacientes: {total_pacientes}, "
                   f"Citas hoy: {citas_hoy}, Notificaciones: {notificaciones_pendientes}")
        
    except Exception as e:
        logger.error(f"Error obteniendo datos para el dashboard: {e}", exc_info=True)
        # Usar valores por defecto si hay un error general
        total_usuarios = 0
        total_pacientes = 0
        citas_hoy = 0
        notificaciones_pendientes = 0
    
    # Devolver la plantilla HTML del dashboard con los datos reales
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_usuarios": total_usuarios,
        "total_pacientes": total_pacientes,
        "citas_hoy": citas_hoy,
        "notificaciones_pendientes": notificaciones_pendientes,
        # "current_user": current_user # Comentado
    })


# --- Rutas de gestión de pacientes ---
# (Esta sección debe ser idéntica a la original, solo depende de la nueva auth)
def process_patient_data_for_display(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa datos de paciente para mostrar (Ej: desencripta, enmascara). VERSIÓN SÍNCRONA."""
    if not patient_data: return {}
    logger.debug(f"Procesando datos para mostrar del paciente ID: {patient_data.get('id')}")
    processed = patient_data.copy()
    processed["phone_masked"] = mask_sensitive_data(processed.get("phone", "N/A"))
    metadata_dict = {}
    metadata_raw = processed.get("metadata")
    if isinstance(metadata_raw, str) and metadata_raw.strip():
        try: metadata_dict = json.loads(metadata_raw)
        except json.JSONDecodeError as e: logger.error(f"Error parseando metadata JSON paciente {patient_data.get('id')}: {e}"); metadata_dict = {"error": "Metadata inválida"}
    elif isinstance(metadata_raw, dict): metadata_dict = metadata_raw
    metadata_dict["email_masked"] = mask_sensitive_data(metadata_dict.get("email", "N/A"))
    processed["metadata_processed"] = metadata_dict
    return processed

@app.get("/patients", response_class=HTMLResponse)
# @require_permission("read")  # Comentado temporalmente para acceso directo
async def list_patients(request: Request):  # Removido current_user parameter
    """Lista todos los pacientes."""
    logger.info("Listando pacientes (sin autenticación temporal).")
    # (Asegúrate que la plantilla patients/list.html existe)
    try:
        patients_data = await get_all_patients()
        patients_raw = patients_data.get("results", [])
        processed_patients = [process_patient_data_for_display(p) for p in patients_raw]
        # await log_audit_event(request=request, user_id="anonymous", action="view_list", resource_type="patient", details={"count": len(processed_patients)})
        user_permissions_set = {"read", "write", "delete"}  # Permisos temporales
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        return templates.TemplateResponse("patients/list.html", {"request": request, "patients": processed_patients, "user": mock_user, "user_permissions": list(user_permissions_set)})
    except Exception as e:
        logger.error(f"Error al listar pacientes: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": f"Error al listar pacientes: {e}"}, status_code=500)

@app.get("/patients/new", response_class=HTMLResponse)
# @require_permission("write")  # Comentado temporalmente para acceso directo
async def new_patient_form(request: Request):  # Removido current_user parameter
    """Muestra el formulario para crear un nuevo paciente."""
    logger.info("Accediendo al formulario de nuevo paciente (sin autenticación temporal).")
    # (Asegúrate que la plantilla patients/new.html existe)
    mock_user = {"username": "admin_temp", "roles": ["admin"]}
    return templates.TemplateResponse("patients/new.html", {"request": request, "user": mock_user, "form_data": {}})

@app.post("/patients/new")
# @require_permission("write")  # Comentado temporalmente para acceso directo
async def create_new_patient(
    request: Request, name: str = Form(...), phone: str = Form(...), email: Optional[EmailStr] = Form(None), language: str = Form("es")
    # current_user: UserWithRoles = Depends(get_current_active_user_with_roles)  # Comentado temporalmente
):
    """Crea un nuevo paciente."""
    logger.info(f"Creando paciente: {name} (sin autenticación temporal)")
    try:
        loop = asyncio.get_running_loop()
        encrypted_phone, encrypted_email = phone, email
        tasks, phone_idx, email_idx = [], -1, -1
        if phone: tasks.append(loop.run_in_executor(None, _encrypt_data_sync, phone)); phone_idx = len(tasks) - 1
        if email: tasks.append(loop.run_in_executor(None, _encrypt_data_sync, email)); email_idx = len(tasks) - 1
        if tasks:
            try:
                results = await asyncio.gather(*tasks)
                if phone_idx != -1: encrypted_phone = results[phone_idx]
                if email_idx != -1: encrypted_email = results[email_idx]
                if "Error de encriptación" in results: raise ValueError("Fallo encriptación al crear paciente.")
            except Exception as enc_error: logger.error(f"Error encriptando nuevo paciente {name}: {enc_error}", exc_info=True); raise HTTPException(status_code=500, detail="Error procesando datos paciente.")

        metadata = {}
        if encrypted_email: metadata["email"] = encrypted_email
        patient_data_to_create = {"name": name, "phone": encrypted_phone, "language": language, "metadata": json.dumps(metadata) if metadata else "{}"}
        logger.debug(f"Datos a crear paciente: (Nombre: {name}, Lang: {language}, MetaKeys: {list(metadata.keys())})") # Log Sanitizado

        result = await d1_insert_patient(patient_data_to_create); new_patient_id = result.get("id")
        if result.get("success") and new_patient_id:
            logger.info(f"Paciente '{name}' (ID: {new_patient_id}) creado exitosamente.")
            # await log_audit_event(request=request, user_id="admin_temp", action="create", resource_type="patient", resource_id=new_patient_id, details={"name": name, "language": language, "metadata_keys": list(metadata.keys())})
            return RedirectResponse(url="/patients", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido al crear paciente.")
            logger.error(f"Error creando paciente '{name}': {error_msg}")
            mock_user = {"username": "admin_temp", "roles": ["admin"]}
            return templates.TemplateResponse("patients/new.html", {"request": request, "user": mock_user, "error": error_msg, "form_data": {"name": name, "phone": phone, "email": email, "language": language}}, status_code=400)
    except HTTPException: raise
    except ValueError as ve: logger.error(f"Error valor/encriptación creando paciente {name}: {ve}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error interno procesando datos: {ve}"}, status_code=500)
    except Exception as e: logger.exception(f"Excepción no controlada creando paciente '{name}': {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado creando paciente: {e}"}, status_code=500)

@app.get("/patients/{patient_id}", response_class=HTMLResponse)
@require_permission("read")
async def view_patient(request: Request, patient_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra los detalles de un paciente específico."""
    logger.info(f"Usuario '{current_user.username}' viendo paciente ID: {patient_id}")
    # (Asegúrate que la plantilla patients/view.html existe)
    try:
        patient_data_task = get_patient_by_id(patient_id)
        sessions_data_task = get_all_appointments()
        notifications_data_task = get_all_notifications()
        patient_data, sessions_data, notifications_data = await asyncio.gather(patient_data_task, sessions_data_task, notifications_data_task)
        patient_raw = patient_data.get("results", [{}])[0] if patient_data.get("results") else None
        if not patient_raw: logger.warning(f"Intento ver paciente no encontrado (ID: {patient_id}) por '{current_user.username}'."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")

        processed_patient = process_patient_data_for_display(patient_raw)
        all_sessions = sessions_data.get("results", [])
        patient_sessions = sorted([s for s in all_sessions if s.get("patient_id") == patient_id], key=lambda s: parse_iso_date_flexible(s.get("scheduled_at")), reverse=True)
        all_notifications = notifications_data.get("results", [])
        patient_notifications = sorted([n for n in all_notifications if n.get("patient_id") == patient_id], key=lambda n: parse_iso_date_flexible(n.get("created_at")), reverse=True)

        await log_audit_event(request=request, user_id=current_user.username, action="view_details", resource_type="patient", resource_id=patient_id)
        return templates.TemplateResponse("patients/view.html", {"request": request, "patient": processed_patient, "sessions": patient_sessions, "notifications": patient_notifications, "user": current_user})
    except HTTPException: raise
    except Exception as e: logger.error(f"Error viendo paciente ID {patient_id}: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error cargando detalles paciente: {e}"}, status_code=500)

@app.get("/patients/{patient_id}/edit", response_class=HTMLResponse)
@require_permission("write")
async def edit_patient_form(request: Request, patient_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra el formulario para editar un paciente."""
    logger.info(f"Usuario '{current_user.username}' editando paciente ID: {patient_id}")
    # (Asegúrate que la plantilla patients/edit.html existe)
    try:
        patient_data = await get_patient_by_id(patient_id)
        patient_raw = patient_data.get("results", [{}])[0] if patient_data.get("results") else None
        if not patient_raw: logger.warning(f"Intento editar paciente no encontrado (ID: {patient_id}) por '{current_user.username}'."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")

        patient_for_form = process_patient_data_for_display(patient_raw)
        loop = asyncio.get_running_loop()
        phone_to_decrypt = patient_raw.get("phone")
        email_to_decrypt = patient_for_form.get("metadata_processed", {}).get("email")
        tasks, phone_idx, email_idx = [], -1, -1
        if phone_to_decrypt: tasks.append(loop.run_in_executor(None, _decrypt_data_sync, phone_to_decrypt)); phone_idx = len(tasks) - 1
        if email_to_decrypt: tasks.append(loop.run_in_executor(None, _decrypt_data_sync, email_to_decrypt)); email_idx = len(tasks) - 1

        decrypted_phone, decrypted_email = "", ""
        if tasks:
            try:
                results = await asyncio.gather(*tasks)
                if phone_idx != -1: decrypted_phone = results[phone_idx]
                if email_idx != -1: decrypted_email = results[email_idx]
                if decrypted_phone == "Error al desencriptar": logger.warning(f"Fallo desencriptar teléfono form paciente {patient_id}"); decrypted_phone = ""
                if decrypted_email == "Error al desencriptar": logger.warning(f"Fallo desencriptar email form paciente {patient_id}"); decrypted_email = ""
            except Exception as dec_error: logger.error(f"Error desencriptando form paciente {patient_id}: {dec_error}", exc_info=True)

        patient_for_form["phone_decrypted"] = decrypted_phone
        patient_for_form["email_decrypted"] = decrypted_email
        patient_for_form["phone"] = patient_raw.get("phone", "") # Original por si falla decrypt
        patient_for_form["email_from_metadata"] = patient_for_form.get("metadata_processed", {}).get("email", "")

        return templates.TemplateResponse("patients/edit.html", {"request": request, "patient": patient_for_form, "user": current_user})
    except HTTPException: raise
    except Exception as e: logger.error(f"Error preparando form edición paciente {patient_id}: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error cargando datos edición: {e}"}, status_code=500)

@app.post("/patients/{patient_id}/edit")
@require_permission("write")
async def update_patient_data(
    request: Request, patient_id: str, name: str = Form(...), phone: str = Form(...), email: Optional[EmailStr] = Form(None), language: str = Form("es"),
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    """Actualiza los datos de un paciente."""
    logger.info(f"Usuario '{current_user.username}' actualizando paciente ID: {patient_id}")
    try:
        # OBTENER datos actuales para merge de metadata (más robusto)
        current_patient_data = await get_patient_by_id(patient_id)
        if not current_patient_data.get("results"): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado para actualizar")
        current_metadata = {}
        try: current_metadata = json.loads(current_patient_data["results"][0].get("metadata", "{}"))
        except: pass

        loop = asyncio.get_running_loop()
        encrypted_phone, encrypted_email = phone, email
        tasks, phone_idx, email_idx = [], -1, -1
        if phone: tasks.append(loop.run_in_executor(None, _encrypt_data_sync, phone)); phone_idx = len(tasks) - 1
        # Solo encriptar email si se proporcionó un valor
        if email is not None: tasks.append(loop.run_in_executor(None, _encrypt_data_sync, email)); email_idx = len(tasks) - 1
        else: encrypted_email = current_metadata.get("email") # Mantener email antiguo si no se envió nuevo

        if tasks:
            try:
                results = await asyncio.gather(*tasks)
                if phone_idx != -1: encrypted_phone = results[phone_idx]
                if email_idx != -1: encrypted_email = results[email_idx] # Solo si se encriptó
                if "Error de encriptación" in results: raise ValueError("Fallo encriptación al actualizar paciente.")
            except Exception as enc_error: logger.error(f"Error encriptando actualización paciente {patient_id}: {enc_error}", exc_info=True); raise HTTPException(status_code=500, detail="Error procesando datos actualización.")

        # Actualizar metadata combinada
        updated_metadata = current_metadata.copy()
        if email is not None: updated_metadata["email"] = encrypted_email # Actualizar solo si se proporcionó

        patient_data_to_update = {"id": patient_id, "name": name, "phone": encrypted_phone, "language": language, "metadata": json.dumps(updated_metadata)}
        logger.debug(f"Datos a actualizar paciente {patient_id}: (Nombre: {name}, Lang: {language}, MetaKeys: {list(updated_metadata.keys())})") # Log Sanitizado

        result = await d1_update_patient(patient_data_to_update)
        if result.get("success"):
            logger.info(f"Paciente ID: {patient_id} actualizado por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="update", resource_type="patient", resource_id=patient_id, details={"updated_fields": ["name", "phone", "language", "metadata"]})
            return RedirectResponse(url=f"/patients/{patient_id}", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido al actualizar paciente.")
            logger.error(f"Error actualizando paciente ID {patient_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": f"No se pudo actualizar el paciente: {error_msg}"}, status_code=400)
    except HTTPException: raise
    except ValueError as ve: logger.error(f"Error valor/encriptación actualizando paciente {patient_id}: {ve}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error interno procesando datos: {ve}"}, status_code=500)
    except Exception as e: logger.exception(f"Excepción no controlada actualizando paciente {patient_id}: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado actualizando paciente: {e}"}, status_code=500)

@app.post("/patients/{patient_id}/delete")
@require_permission("delete")
async def delete_patient_data(request: Request, patient_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Elimina un paciente."""
    logger.warning(f"Usuario '{current_user.username}' intentando ELIMINAR paciente ID: {patient_id}")
    try:
        patient_data = await get_patient_by_id(patient_id); patient_details = patient_data.get("results", [None])[0]
        if not patient_details: logger.warning(f"Intento eliminar paciente no encontrado (ID: {patient_id}) por '{current_user.username}'."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado para eliminar")
        patient_name = patient_details.get("name", "Desconocido")
        result = await d1_delete_patient(patient_id)
        if result.get("success"):
            logger.info(f"Paciente ID: {patient_id} (Nombre: {patient_name}) eliminado por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="delete", resource_type="patient", resource_id=patient_id, details={"deleted_patient_name": sanitize_data_for_logs({"name": patient_name}).get("name")})
            return RedirectResponse(url="/patients", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido al eliminar paciente.")
            logger.error(f"Error eliminando paciente ID {patient_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": f"No se pudo eliminar el paciente: {error_msg}"}, status_code=400)
    except HTTPException: raise
    except Exception as e: logger.exception(f"Excepción no controlada eliminando paciente {patient_id}: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado eliminando paciente: {e}"}, status_code=500)


# --- Rutas de gestión de sesiones ---
# (Esta sección debe ser idéntica a la original)
@app.get("/sessions", response_class=HTMLResponse)
# @require_permission("read")  # Comentado temporalmente para acceso directo
async def list_sessions(
    request: Request,
    status_filter: Optional[str] = None, session_type_filter: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    search: Optional[str] = None, modality_filter: Optional[str] = None,
    sort_by: str = "scheduled_at", sort_order: str = "desc", page: int = 1,
    # current_user: UserWithRoles = Depends(get_current_active_user_with_roles)  # Comentado temporalmente
):
    logger.info(f"Listando sesiones con filtros: status={status_filter}, type={session_type_filter}, search={search}, page={page}")
    # (Asegúrate que la plantilla sessions/list.html existe)
    try:
        sessions_data_task = get_all_appointments()
        patients_data_task = get_all_patients()
        sessions_data, patients_data = await asyncio.gather(sessions_data_task, patients_data_task)
        all_sessions = sessions_data.get("results", [])
        patients_dict = {p.get("id"): p for p in patients_data.get("results", [])}
        filtered_sessions = []; now_utc = datetime.now(timezone.utc)
        for session in all_sessions:
            patient_id = session.get("patient_id"); patient_info = patients_dict.get(patient_id)
            session["patient_name"] = patient_info.get("name", "Paciente Desconocido") if patient_info else "Paciente Desconocido"
            session["scheduled_at_dt"] = parse_iso_date_flexible(session.get("scheduled_at"))
            try: session["metadata_parsed"] = json.loads(session.get("metadata", "{}"))
            except json.JSONDecodeError: session["metadata_parsed"] = {"error": "Invalid JSON"}
            keep = True
            if status_filter and session.get("status", "").lower() != status_filter.lower(): keep = False
            if session_type_filter and session.get("session_type", "").lower() != session_type_filter.lower(): keep = False
            if modality_filter and session["metadata_parsed"].get("modality", "").lower() != modality_filter.lower(): keep = False
            if date_from:
                 date_from_dt = parse_iso_date_flexible(date_from + "T00:00:00", 0)
                 if session["scheduled_at_dt"] < date_from_dt: keep = False
            if date_to:
                 date_to_dt = parse_iso_date_flexible(date_to + "T23:59:59", 0)
                 if session["scheduled_at_dt"] > date_to_dt: keep = False
            if search:
                search_lower = search.lower()
                if not (search_lower in session["patient_name"].lower() or search_lower in session.get("session_type", "").lower() or search_lower in session.get("status", "").lower()): keep = False
            if keep: filtered_sessions.append(session)

        reverse_sort = (sort_order.lower() == "desc")
        def sort_key_func(s):
            if sort_by == "patient_name": return s.get("patient_name", "")
            elif sort_by == "status": return s.get("status", "")
            else: return s.get("scheduled_at_dt", now_utc - timedelta(days=365*10))
        filtered_sessions.sort(key=sort_key_func, reverse=reverse_sort)

        items_per_page = 15; total_items = len(filtered_sessions); total_pages = (total_items + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages or 1))
        start_idx = (page - 1) * items_per_page; end_idx = start_idx + items_per_page
        paginated_sessions = filtered_sessions[start_idx:end_idx]

        # await log_audit_event(request=request, user_id=current_user.username, action="view_list", resource_type="session", details={"filters": {"status": status_filter, "type": session_type_filter, "search": search, "page": page}, "count": len(paginated_sessions), "total_found": total_items})
        
        # Mock user temporal
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        
        return templates.TemplateResponse("sessions/list.html", {
            "request": request, "sessions": paginated_sessions, "current_page": page, "total_pages": total_pages, "total_items": total_items,
            "filters": {"status_filter": status_filter, "session_type_filter": session_type_filter, "date_from": date_from, "date_to": date_to, "search": search, "modality_filter": modality_filter, "sort_by": sort_by, "sort_order": sort_order},
            "user": mock_user  # Cambiado de current_user a mock_user
        })
    except Exception as e: logger.error(f"Error listando sesiones: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error listando sesiones: {e}"}, status_code=500)

@app.get("/sessions/new", response_class=HTMLResponse)
# @require_permission("write")  # Comentado temporalmente para acceso directo
async def new_session_form(request: Request):  # Removido current_user parameter
    # (Asegúrate que la plantilla sessions/new.html existe)
    try:
        patients_data = await get_all_patients()
        patients = patients_data.get("results", [])
        # Obtener lista de terapeutas (real o mock)
        therapists = [{"id": 1, "name": "Terapeuta 1"}, {"id": 2, "name": "Terapeuta 2"}] # Mock
        # Mock user temporal
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        return templates.TemplateResponse("sessions/new.html", {"request": request, "patients": patients, "therapists": therapists, "center_address": settings.CENTER_ADDRESS, "user": mock_user})
    except Exception as e: logger.error(f"Error form nueva sesión: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)

@app.post("/sessions/create") # Debería ser /sessions/new o /sessions
# @require_permission("write")  # Comentado temporalmente para acceso directo
async def create_new_session(
    request: Request, patient_id: str = Form(...), session_type: str = Form(...), modality: str = Form(...),
    session_date: str = Form(...), session_time: str = Form(...), duration: int = Form(60), therapist_name: str = Form(None),
    video_link: str = Form(None), notes: str = Form(None), send_notification: bool = Form(False), send_reminder: bool = Form(False),
    # current_user: UserWithRoles = Depends(get_current_active_user_with_roles)  # Comentado temporalmente
):
    logger.info(f"Creando nueva sesión para paciente ID: {patient_id}")
    try:
        scheduled_at = f"{session_date}T{session_time}:00" # Considerar validación y zona horaria
        # Encriptar notas si es necesario
        encrypted_notes = notes
        if notes: encrypted_notes = await asyncio.get_running_loop().run_in_executor(None, _encrypt_data_sync, notes)
        if encrypted_notes == "Error de encriptación": raise ValueError("Fallo encriptando notas de sesión.")

        metadata = {"modality": modality, "duration": duration, "therapist_name": therapist_name}
        if modality == "online" and video_link: metadata["video_link"] = video_link
        if encrypted_notes: metadata["notes"] = encrypted_notes # Guardar notas encriptadas

        session_data = {"patient_id": patient_id, "session_type": session_type, "status": "scheduled", "scheduled_at": scheduled_at, "metadata": json.dumps(metadata)}
        result = await create_session(session_data); new_session_id = result.get("id")

        if result.get("success") and new_session_id:
            logger.info(f"Sesión ID {new_session_id} creada.")
            # await log_audit_event(request=request, user_id="admin_temp", action="create", resource_type="session", resource_id=new_session_id, details=sanitize_data_for_logs({"patient_id":patient_id, "type": session_type, "modality": modality}))

            # Lógica para crear notificaciones (confirmación, recordatorio)
            if send_notification or send_reminder:
                 patient_data = await get_patient_by_id(patient_id)
                 patient = patient_data.get("results", [{}])[0]
                 if patient:
                      scheduled_dt = datetime.fromisoformat(scheduled_at)
                      formatted_date = scheduled_dt.strftime("%d/%m/%Y")
                      formatted_time = scheduled_dt.strftime("%H:%M")
                      if send_notification:
                          # ... (construir mensaje de confirmación) ...
                          message = f"Sesión programada para {formatted_date} a las {formatted_time}."
                          notif_data = {"patient_id": patient_id, "message": message, "channel": "whatsapp", "status": "pending", "scheduled_at": datetime.now(timezone.utc).isoformat(), "metadata": json.dumps({"session_id": new_session_id})}
                          await create_notification(notif_data)
                      if send_reminder:
                          reminder_dt = scheduled_dt - timedelta(hours=24)
                          if reminder_dt > datetime.now(timezone.utc): # Solo programar si es en el futuro
                              # ... (construir mensaje de recordatorio) ...
                              message = f"Recordatorio: Sesión mañana a las {formatted_time}."
                              notif_data = {"patient_id": patient_id, "message": message, "channel": "whatsapp", "status": "pending", "scheduled_at": reminder_dt.isoformat(), "metadata": json.dumps({"session_id": new_session_id, "type": "reminder"})}
                              await create_notification(notif_data)

            return RedirectResponse(url="/sessions", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido creando sesión.")
            logger.error(f"Error creando sesión para paciente {patient_id}: {error_msg}")
            # Volver a mostrar form con error
            return templates.TemplateResponse("error.html", {"request": request, "error": error_msg}, status_code=400) # Simplificado
    except HTTPException: raise
    except ValueError as ve: logger.error(f"Error valor/encriptación creando sesión: {ve}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error interno procesando datos: {ve}"}, status_code=500)
    except Exception as e: logger.exception(f"Excepción no controlada creando sesión: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado creando sesión: {e}"}, status_code=500)

# --- Funciones de utilidad para procesar datos sensibles ---
def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """Enmascara datos sensibles para mostrar en la interfaz."""
    if not data or not isinstance(data, str) or len(data) <= visible_chars: return data if isinstance(data, str) else str(data)
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]

def sanitize_data_for_logs(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Sanitiza datos para registros de auditoría (definida arriba)."""
    if not data: return None
    sanitized_data = {}
    sensitive_keys_redact = ["password", "passwd", "secret", "token", "apikey", "credentials", "creditcard", "cvv", "ssn", "taxid", "dob", "medicalhistory", "diagnosis"]
    sensitive_keys_mask = ["phone", "email", "address", "name", "username", "accountnumber", "iban"]
    MAX_DEPTH = 3
    def sanitize_recursive(item, depth):
        if depth > MAX_DEPTH: return "[DEPTH LIMIT]"
        if isinstance(item, dict):
            nd = {}
            for k, v in item.items():
                kl = str(k).lower()
                if any(sk in kl for sk in sensitive_keys_redact): nd[k] = "[REDACTADO]"
                elif any(sk in kl for sk in sensitive_keys_mask): nd[k] = mask_sensitive_data(str(v))
                else: nd[k] = sanitize_recursive(v, depth + 1)
            return nd
        elif isinstance(item, list): return [sanitize_recursive(e, depth + 1) for e in item][:20]
        elif isinstance(item, str) and len(item) > 250: return item[:250] + "...[TRUNCADO]"
        else: return item
    sanitized_data = sanitize_recursive(data, 0)
    return sanitized_data


# --- Rutas de gestión de usuarios ---
@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    """Lista todos los usuarios del sistema."""
    logger.info("Listando usuarios del sistema")
    try:
        users_data = await get_all_db_users(limit=100)
        users = users_data.get("users", [])
        
        # Mock user temporal
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        
        return templates.TemplateResponse("users/list.html", {
            "request": request,
            "users": users,
            "user": mock_user,
            "user_permissions": ["read", "write", "delete", "manage_users"]
        })
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)


# --- Rutas de notificaciones ---
@app.get("/notifications", response_class=HTMLResponse)
async def list_notifications(request: Request):
    """Lista todas las notificaciones."""
    logger.info("Listando notificaciones")
    try:
        notifications_data = await get_all_notifications()
        notifications = notifications_data.get("notifications", [])
        
        # Mock user temporal
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        
        return templates.TemplateResponse("notifications/list.html", {
            "request": request,
            "notifications": notifications,
            "user": mock_user
        })
    except Exception as e:
        logger.error(f"Error listando notificaciones: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)


# --- Rutas de configuración ---
@app.get("/config", response_class=HTMLResponse)
async def system_config(request: Request):
    """Muestra la configuración del sistema."""
    logger.info("Accediendo a configuración del sistema")
    try:
        configs = await get_all_configs()
        config_list = configs.get("configs", [])
        
        # Mock user temporal
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        
        return templates.TemplateResponse("config/index.html", {
            "request": request,
            "configs": config_list,
            "user": mock_user
        })
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)


# --- Rutas de logs ---
@app.get("/logs", response_class=HTMLResponse)
async def audit_logs(request: Request):
    """Muestra los logs de auditoría."""
    logger.info("Accediendo a logs de auditoría")
    try:
        # Por ahora, devolver una página simple indicando que está en construcción
        mock_user = {"username": "admin_temp", "roles": ["admin"]}
        
        return templates.TemplateResponse("logs/index.html", {
            "request": request,
            "logs": [],  # Lista vacía por ahora
            "user": mock_user
        })
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)


# --- Función principal para ejecutar la aplicación ---
def run_admin_panel():
    """Ejecuta el panel de administración."""
    logger.info(f"Iniciando Mark Admin Panel v1.1.1 en {settings.HOST}:{settings.ADMIN_PORT}")
    logger.info(f"ENVIRONMENT={settings.ENVIRONMENT}, MAX_LOGIN_ATTEMPTS={MAX_LOGIN_ATTEMPTS}")
    uvicorn.run(
        "admin.admin_panel:app", # Ruta de importación correcta desde la raíz del proyecto
        host=settings.HOST, port=settings.ADMIN_PORT,
        reload=(settings.ENVIRONMENT == "development"),
        log_level="info"
    )

if __name__ == "__main__":
    run_admin_panel()
