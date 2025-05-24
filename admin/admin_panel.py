# -*- coding: utf-8 -*-
"""

Panel de administración web para el asistente Mark.
Este módulo proporciona una interfaz web para administrar pacientes, sesiones,
notificaciones y configuraciones del sistema del asistente Mark.
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
from pydantic import BaseModel, Field, EmailStr
import functools
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Importar desde nueva ubicación
from core.security_utils import pwd_context
from core.config import settings # Importar settings
from database.d1_client import get_user_by_username, update_user_auth_status, get_user_by_id, update_db_user, create_db_user, get_all_db_users, delete_db_user # Corregido: get_db_user_by_id -> get_user_by_id
from database.d1_client import get_all_patients, get_all_citas, get_all_notifications # Específicas para el dashboard
from database.d1_client import get_patient_by_id, insert_patient as d1_insert_patient, update_patient as d1_update_patient, delete_patient as d1_delete_patient # Pacientes
from database.d1_client import insert_session as d1_insert_session, get_session_by_id as d1_get_session_by_id, update_session as d1_update_session, delete_session as d1_delete_session # Sesiones - get_all_sessions se reemplaza por get_all_citas
from database.d1_client import get_pending_notifications as d1_get_pending_notifications, update_notification_status as d1_update_notification_status, insert_notification as d1_insert_notification # Notificaciones - get_all_notifications ya está arriba
from database.d1_client import get_system_config as d1_get_system_config, set_system_config as d1_set_system_config, get_all_configs # Configuración
from database.d1_client import insert_audit_log # Para auditoría

# --- Settings Import (Mantener o adaptar) ---
# Asegúrate de que settings esté correctamente importado y configurado
# from core.config import settings # Descomenta si tienes tu configuración aquí
# ----- Mock Settings (Reemplaza con tu import real) -----
class MockSettings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_testing_only_replace_in_prod_32_chars_long") # ¡Reemplazar en producción! Mínimo 32 chars.
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    ADMIN_USERNAME = "admin" # Puede ser obsoleto si creas admin en DB
    ADMIN_PASSWORD_HASH = "" # Obsoleto, el hash estará en la DB
    HOST = os.environ.get("HOST", "127.0.0.1")
    ADMIN_PORT = int(os.environ.get("ADMIN_PORT", 8001))
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
    CENTER_ADDRESS = os.environ.get("CENTER_ADDRESS", "Calle Falsa 123, Ciudad Ejemplo")
    # ¡IMPORTANTE! Configura estas claves de forma segura (variables de entorno, secrets manager)
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "default_strong_encryption_key_32_bytes") # ¡Reemplazar! Debe ser fuerte.
    ENCRYPTION_SALT = os.environ.get("ENCRYPTION_SALT", "default_unique_salt_value_needs_replace") # ¡Reemplazar! Debe ser único.
    # Nuevo: Constante para intentos de login
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))

settings = MockSettings()
# Validar longitud de SECRET_KEY y ENCRYPTION_KEY (Fernet necesita 32 bytes URL-safe base64-encoded)
if len(base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32])) < 32: # Una validación simple
     logging.warning("ENCRYPTION_KEY podría no ser adecuada para Fernet. Asegúrate que sea suficientemente larga y segura.")
if len(settings.SECRET_KEY) < 32:
     logging.warning("SECRET_KEY es corta. Se recomienda una clave aleatoria de al menos 32 caracteres.")
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

# --- Constantes ---
MAX_LOGIN_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS

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

    class Config:
        from_attributes = True # Compatible con ORMs si se usa, actualizado de orm_mode
        # Permitir conversión de string ISO a datetime
        json_encoders = { datetime: lambda dt: dt.isoformat() }

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
        if action in critical_actions: logger.warning(f"ALERTA DE SEGURIDAD: {json.dumps(audit_log.dict(), default=str)}") # Lógica de alerta real aquí
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
@require_permission("view_dashboard") # Requiere permiso para ver el dashboard
async def dashboard(
    request: Request,
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles) # Inyecta usuario y verifica
):
    logger.info(f"Usuario '{current_user.username}' accediendo al dashboard.")
    
    if 'format_datetime' not in templates.env.filters:
        def format_datetime_filter(value, fmt='%Y-%m-%d %H:%M'):
            if not value: return ""
            try:
                dt_obj = value
                if not isinstance(value, datetime):
                    dt_obj = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return dt_obj.strftime(fmt)
            except Exception as e_filter:
                logger.warning(f"Error formateando fecha en filtro Jinja: {value}, error: {e_filter}")
                return str(value) 
        templates.env.filters['format_datetime'] = format_datetime_filter

    try:
        patients_response_task = get_all_patients() 
        citas_response_task = get_all_citas() # Llamar a la función renombrada
        notifications_response_task = get_all_notifications()

        patients_response, citas_response, notifications_response = await asyncio.gather(
            patients_response_task, citas_response_task, notifications_response_task
        )

        patients_list = []
        total_patients = 0
        if patients_response and patients_response.get("success"):
            patients_list = patients_response.get("results", [])
            total_patients = patients_response.get("total", len(patients_list)) # Usar el conteo de la DB
            logger.info(f"Dashboard: {len(patients_list)} pacientes obtenidos (Total DB: {total_patients}).")
        else:
            logger.error(f"Dashboard: Error obteniendo pacientes - {patients_response.get('error', 'Error desconocido') if patients_response else 'patients_response es None'}")

        citas_list = [] 
        total_citas = 0
        if citas_response and citas_response.get("success"):
            citas_list = citas_response.get("results", [])
            total_citas = citas_response.get("total", len(citas_list)) # Usar el conteo de la DB
            logger.info(f"Dashboard: {len(citas_list)} citas obtenidas (Total DB: {total_citas}).")
        else:
            logger.error(f"Dashboard: Error obteniendo citas - {citas_response.get('error', 'Error desconocido') if citas_response else 'citas_response es None'}")

        notifications_list = []
        if notifications_response and notifications_response.get("success"):
            notifications_list = notifications_response.get("results", [])
            logger.info(f"Dashboard: {len(notifications_list)} notificaciones obtenidas.")
        else:
            logger.error(f"Dashboard: Error obteniendo notificaciones - {notifications_response.get('error', 'Error desconocido') if notifications_response else 'notifications_response es None'}")

        pending_notifications = sum(1 for n in notifications_list if n.get("status", "").lower() == "pending")
        failed_notifications = sum(1 for n in notifications_list if n.get("status", "").lower() == "failed")

        recent_citas = citas_list[:5] # Ya vienen ordenadas por fecha_inicio desc
        recent_notifications = notifications_list[:5] # Ya vienen ordenadas por created_at desc

        stats_for_template = {
            "total_patients": total_patients,
            "total_citas": total_citas, 
            "pending_notifications": pending_notifications,
            "failed_notifications": failed_notifications,
            "recent_citas": recent_citas, 
            "recent_notifications": recent_notifications
        }
        
        logger.info(f"Dashboard: Datos para plantilla preparados. Stats (resumen): { {k:v for k,v in stats_for_template.items() if not isinstance(v, list)} }")
        await log_audit_event(request=request, user_id=current_user.username, action="view", resource_type="dashboard")

        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "user": current_user,
            "stats": stats_for_template
        })
    except Exception as e:
        logger.error(f"Error crítico al cargar datos del dashboard: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"No se pudieron cargar los datos del dashboard: {e}"}, status_code=500)


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
@require_permission("read")
async def list_patients(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Lista todos los pacientes."""
    logger.info(f"Usuario '{current_user.username}' listando pacientes.")
    # (Asegúrate que la plantilla patients/list.html existe)
    try:
        patients_data = await get_all_patients()
        patients_raw = patients_data.get("results", [])
        processed_patients = [process_patient_data_for_display(p) for p in patients_raw]
        await log_audit_event(request=request, user_id=current_user.username, action="view_list", resource_type="patient", details={"count": len(processed_patients)})
        user_permissions_set = set()
        for role_name in current_user.roles: user_permissions_set.update(ROLES.get(role_name.lower(), []))
        return templates.TemplateResponse("patients/list.html", {"request": request, "patients": processed_patients, "user": current_user, "user_permissions": list(user_permissions_set)})
    except Exception as e:
        logger.error(f"Error al listar pacientes: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": f"Error al listar pacientes: {e}"}, status_code=500)

@app.get("/patients/new", response_class=HTMLResponse)
@require_permission("write")
async def new_patient_form(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra el formulario para crear un nuevo paciente."""
    logger.info(f"Usuario '{current_user.username}' accediendo al formulario de nuevo paciente.")
    # (Asegúrate que la plantilla patients/new.html existe)
    return templates.TemplateResponse("patients/new.html", {"request": request, "user": current_user, "form_data": {}})

@app.post("/patients/new")
@require_permission("write")
async def create_new_patient(
    request: Request, name: str = Form(...), phone: str = Form(...), email: Optional[EmailStr] = Form(None), language: str = Form("es"),
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    """Crea un nuevo paciente."""
    logger.info(f"Usuario '{current_user.username}' intentando crear paciente: {name}")
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
            logger.info(f"Paciente '{name}' (ID: {new_patient_id}) creado por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="create", resource_type="patient", resource_id=new_patient_id, details={"name": name, "language": language, "metadata_keys": list(metadata.keys())})
            return RedirectResponse(url="/patients", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido al crear paciente.")
            logger.error(f"Error creando paciente '{name}': {error_msg}")
            return templates.TemplateResponse("patients/new.html", {"request": request, "user": current_user, "error": error_msg, "form_data": {"name": name, "phone": phone, "email": email, "language": language}}, status_code=400)
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
        sessions_data_task = get_all_citas()
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
@require_permission("read")
async def list_sessions(
    request: Request,
    status_filter: Optional[str] = None, session_type_filter: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    search: Optional[str] = None, modality_filter: Optional[str] = None,
    sort_by: str = "scheduled_at", sort_order: str = "desc", page: int = 1,
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    logger.info(f"Usuario '{current_user.username}' listando sesiones con filtros: status={status_filter}, type={session_type_filter}, search={search}, page={page}")
    # (Asegúrate que la plantilla sessions/list.html existe)
    try:
        sessions_data_task = get_all_citas()
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

        await log_audit_event(request=request, user_id=current_user.username, action="view_list", resource_type="session", details={"filters": {"status": status_filter, "type": session_type_filter, "search": search, "page": page}, "count": len(paginated_sessions), "total_found": total_items})
        return templates.TemplateResponse("sessions/list.html", {
            "request": request, "sessions": paginated_sessions, "current_page": page, "total_pages": total_pages, "total_items": total_items,
            "filters": {"status_filter": status_filter, "session_type_filter": session_type_filter, "date_from": date_from, "date_to": date_to, "search": search, "modality_filter": modality_filter, "sort_by": sort_by, "sort_order": sort_order},
            "user": current_user
        })
    except Exception as e: logger.error(f"Error listando sesiones: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error listando sesiones: {e}"}, status_code=500)

@app.get("/sessions/new", response_class=HTMLResponse)
@require_permission("write")
async def new_session_form(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    # (Asegúrate que la plantilla sessions/new.html existe)
    try:
        patients_data = await get_all_patients()
        patients = patients_data.get("results", [])
        # Obtener lista de terapeutas (real o mock)
        therapists = [{"id": 1, "name": "Terapeuta 1"}, {"id": 2, "name": "Terapeuta 2"}] # Mock
        return templates.TemplateResponse("sessions/new.html", {"request": request, "patients": patients, "therapists": therapists, "center_address": settings.CENTER_ADDRESS, "user": current_user})
    except Exception as e: logger.error(f"Error form nueva sesión: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)

@app.post("/sessions/create") # Debería ser /sessions/new o /sessions
@require_permission("write")
async def create_new_session(
    request: Request, patient_id: str = Form(...), session_type: str = Form(...), modality: str = Form(...),
    session_date: str = Form(...), session_time: str = Form(...), duration: int = Form(60), therapist_name: str = Form(None),
    video_link: str = Form(None), notes: str = Form(None), send_notification: bool = Form(False), send_reminder: bool = Form(False),
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    logger.info(f"Usuario '{current_user.username}' creando nueva sesión para paciente ID: {patient_id}")
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
            logger.info(f"Sesión ID {new_session_id} creada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="create", resource_type="session", resource_id=new_session_id, details=sanitize_data_for_logs({"patient_id":patient_id, "type": session_type, "modality": modality}))

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

@app.get("/sessions/{session_id}", response_class=HTMLResponse)
@require_permission("read")
async def view_session(request: Request, session_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    # (Asegúrate que la plantilla sessions/view.html existe)
    logger.info(f"Usuario '{current_user.username}' viendo sesión ID: {session_id}")
    try:
        session_data = await get_session_by_id(session_id)
        session = session_data.get("results", [{}])[0] if session_data.get("results") else None
        if not session: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

        # Desencriptar notas para mostrar si es necesario
        session["metadata_parsed"] = {}
        decrypted_notes = "N/A"
        try:
            metadata_dict = json.loads(session.get("metadata", "{}"))
            session["metadata_parsed"] = metadata_dict
            notes_encrypted = metadata_dict.get("notes")
            if notes_encrypted:
                dec_notes = await asyncio.get_running_loop().run_in_executor(None, _decrypt_data_sync, notes_encrypted)
                if dec_notes != "Error al desencriptar": decrypted_notes = dec_notes
                else: logger.warning(f"Fallo desencriptar notas sesión {session_id}")
        except json.JSONDecodeError: pass
        except Exception as dec_err: logger.error(f"Error desencriptando notas sesión {session_id}: {dec_err}")

        session["notes_decrypted"] = decrypted_notes # Añadir notas desencriptadas

        patient_data = await get_patient_by_id(session.get("patient_id")); patient = patient_data.get("results", [{}])[0]
        # Obtener historial de cambios y sesiones anteriores (lógica original o adaptada)
        session_history = [] # Mock
        previous_sessions = [] # Mock

        await log_audit_event(request=request, user_id=current_user.username, action="view_details", resource_type="session", resource_id=session_id)
        return templates.TemplateResponse("sessions/view.html", {"request": request, "session": session, "patient": patient, "session_history": session_history, "previous_sessions": previous_sessions, "user": current_user})
    except HTTPException: raise
    except Exception as e: logger.error(f"Error viendo sesión {session_id}: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error cargando sesión: {e}"}, status_code=500)

@app.get("/sessions/{session_id}/edit", response_class=HTMLResponse)
@require_permission("write")
async def edit_session_form(request: Request, session_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    # (Asegúrate que la plantilla sessions/edit.html existe)
    logger.info(f"Usuario '{current_user.username}' editando sesión ID: {session_id}")
    try:
        session_data = await get_session_by_id(session_id); session = session_data.get("results", [{}])[0]
        if not session: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

        session["metadata_parsed"] = {} ; decrypted_notes = ""
        try:
            metadata_dict = json.loads(session.get("metadata", "{}")); session["metadata_parsed"] = metadata_dict
            notes_encrypted = metadata_dict.get("notes")
            if notes_encrypted:
                 dec_notes = await asyncio.get_running_loop().run_in_executor(None, _decrypt_data_sync, notes_encrypted)
                 if dec_notes != "Error al desencriptar": decrypted_notes = dec_notes
        except: pass
        session["notes_decrypted"] = decrypted_notes

        patient_data = await get_patient_by_id(session.get("patient_id")); patient = patient_data.get("results", [{}])[0]
        therapists = [{"id": 1, "name": "Terapeuta 1"}, {"id": 2, "name": "Terapeuta 2"}] # Mock
        return templates.TemplateResponse("sessions/edit.html", {"request": request, "session": session, "patient": patient, "therapists": therapists, "user": current_user})
    except HTTPException: raise
    except Exception as e: logger.error(f"Error form edición sesión {session_id}: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error cargando datos sesión: {e}"}, status_code=500)

@app.post("/sessions/{session_id}/update") # Ruta original era /update
@require_permission("write")
async def update_session_data(
    request: Request, session_id: str, session_type: str = Form(...), modality: str = Form(...), session_date: str = Form(...), session_time: str = Form(...),
    duration: int = Form(60), therapist_name: str = Form(None), video_link: str = Form(None), notes: str = Form(None), status: str = Form("scheduled"),
    send_notification: bool = Form(False), current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    logger.info(f"Usuario '{current_user.username}' actualizando sesión ID: {session_id}")
    try:
        session_data = await get_session_by_id(session_id); current_session = session_data.get("results", [{}])[0]
        if not current_session: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

        scheduled_at = f"{session_date}T{session_time}:00"
        encrypted_notes = notes
        if notes: encrypted_notes = await asyncio.get_running_loop().run_in_executor(None, _encrypt_data_sync, notes)
        if encrypted_notes == "Error de encriptación": raise ValueError("Fallo encriptando notas al actualizar sesión.")

        # Obtener metadata actual y actualizarla
        current_metadata = {}
        try: current_metadata = json.loads(current_session.get("metadata", "{}"))
        except: pass
        updated_metadata = current_metadata.copy()
        updated_metadata.update({"modality": modality, "duration": duration, "therapist_name": therapist_name})
        if modality == "online" and video_link: updated_metadata["video_link"] = video_link
        if notes is not None: updated_metadata["notes"] = encrypted_notes # Actualizar notas si se enviaron

        updated_session_data = {"id": session_id, "patient_id": current_session.get("patient_id"), "session_type": session_type, "status": status, "scheduled_at": scheduled_at, "metadata": json.dumps(updated_metadata)}
        result = await update_session(updated_session_data)

        if result.get("success"):
            logger.info(f"Sesión ID {session_id} actualizada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="update", resource_type="session", resource_id=session_id, details=sanitize_data_for_logs({"type": session_type, "status": status, "modality": modality}))
            # Lógica para enviar notificación de actualización
            if send_notification:
                 # ... (obtener paciente, construir mensaje, crear notificación) ...
                 message = f"Detalles de tu sesión actualizados. Nueva fecha: {session_date} {session_time}."
                 notif_data = {"patient_id": current_session.get("patient_id"), "message": message, "channel": "whatsapp", "status": "pending", "scheduled_at": datetime.now(timezone.utc).isoformat(), "metadata": json.dumps({"session_id": session_id, "type":"update"})}
                 await create_notification(notif_data)

            return RedirectResponse(url=f"/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido actualizando sesión.")
            logger.error(f"Error actualizando sesión ID {session_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": error_msg}, status_code=400)
    except HTTPException: raise
    except ValueError as ve: logger.error(f"Error valor/encriptación actualizando sesión {session_id}: {ve}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error interno procesando datos: {ve}"}, status_code=500)
    except Exception as e: logger.exception(f"Excepción no controlada actualizando sesión {session_id}: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado actualizando sesión: {e}"}, status_code=500)

@app.post("/sessions/{session_id}/complete")
@require_permission("write")
async def complete_session(request: Request, session_id: str, completion_notes: str = Form(None), current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.info(f"Usuario '{current_user.username}' completando sesión ID: {session_id}")
    try:
        session_data = await get_session_by_id(session_id); current_session = session_data.get("results", [{}])[0]
        if not current_session: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

        # Obtener metadata actual y añadir info de completado
        current_metadata = {};
        try: current_metadata = json.loads(current_session.get("metadata", "{}"))
        except: pass
        updated_metadata = current_metadata.copy()
        if completion_notes: updated_metadata["completion_notes"] = completion_notes # Considerar encriptar?
        updated_metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
        updated_metadata["completed_by"] = current_user.username

        updated_session_data = current_session.copy() # Copiar todos los campos
        updated_session_data.update({"id": session_id, "status": "completed", "metadata": json.dumps(updated_metadata)})

        result = await update_session(updated_session_data)
        if result.get("success"):
            logger.info(f"Sesión ID {session_id} completada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="complete", resource_type="session", resource_id=session_id, details={"notes_added": bool(completion_notes)})
            return RedirectResponse(url=f"/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido completando sesión.")
            logger.error(f"Error completando sesión ID {session_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": error_msg}, status_code=400)
    except HTTPException: raise
    except Exception as e: logger.exception(f"Excepción no controlada completando sesión {session_id}: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado completando sesión: {e}"}, status_code=500)

@app.post("/sessions/{session_id}/cancel")
@require_permission("write")
async def cancel_session(
    request: Request, session_id: str, cancellation_reason: str = Form(...), cancellation_notes: str = Form(None),
    notify_patient: bool = Form(False), current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    logger.warning(f"Usuario '{current_user.username}' cancelando sesión ID: {session_id}, Razón: {cancellation_reason}")
    try:
        session_data = await get_session_by_id(session_id); current_session = session_data.get("results", [{}])[0]
        if not current_session: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

        current_metadata = {};
        try: current_metadata = json.loads(current_session.get("metadata", "{}"))
        except: pass
        updated_metadata = current_metadata.copy()
        updated_metadata["cancellation_reason"] = cancellation_reason
        if cancellation_notes: updated_metadata["cancellation_notes"] = cancellation_notes
        updated_metadata["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        updated_metadata["cancelled_by"] = current_user.username

        updated_session_data = current_session.copy()
        updated_session_data.update({"id": session_id, "status": "cancelled", "metadata": json.dumps(updated_metadata)})

        result = await update_session(updated_session_data)
        if result.get("success"):
            logger.info(f"Sesión ID {session_id} cancelada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="cancel", resource_type="session", resource_id=session_id, details={"reason": cancellation_reason})
            # Lógica para enviar notificación de cancelación
            if notify_patient:
                # ... (obtener paciente, construir mensaje, crear notificación) ...
                 message = f"Tu sesión del {parse_iso_date_flexible(current_session.get('scheduled_at')).strftime('%d/%m %H:%M')} ha sido cancelada."
                 notif_data = {"patient_id": current_session.get("patient_id"), "message": message, "channel": "whatsapp", "status": "pending", "scheduled_at": datetime.now(timezone.utc).isoformat(), "metadata": json.dumps({"session_id": session_id, "type":"cancellation"})}
                 await create_notification(notif_data)

            return RedirectResponse(url=f"/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido cancelando sesión.")
            logger.error(f"Error cancelando sesión ID {session_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": error_msg}, status_code=400)
    except HTTPException: raise
    except Exception as e: logger.exception(f"Excepción no controlada cancelando sesión {session_id}: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado cancelando sesión: {e}"}, status_code=500)

# --- Rutas de gestión de notificaciones ---
# (Esta sección debe ser idéntica a la original)
@app.get("/notifications", response_class=HTMLResponse)
@require_permission("read")
async def list_notifications(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.info(f"Usuario '{current_user.username}' listando notificaciones.")
    # (Asegúrate que la plantilla notifications/list.html existe)
    try:
        notifications_data_task = get_all_notifications()
        patients_data_task = get_all_patients()
        notifications_data, patients_data = await asyncio.gather(notifications_data_task, patients_data_task)
        notifications = notifications_data.get("results", [])
        patients_dict = {p.get("id"): p for p in patients_data.get("results", [])}
        for notification in notifications:
            patient_id = notification.get("patient_id"); patient_info = patients_dict.get(patient_id)
            notification["patient_name"] = patient_info.get("name", "Paciente Desconocido") if patient_info else "Paciente Desconocido"
            notification["created_at_dt"] = parse_iso_date_flexible(notification.get("created_at"))
            notification["scheduled_at_dt"] = parse_iso_date_flexible(notification.get("scheduled_at"), default_offset_days=0)
        notifications.sort(key=lambda n: n["created_at_dt"], reverse=True)
        await log_audit_event(request=request, user_id=current_user.username, action="view_list", resource_type="notification", details={"count": len(notifications)})
        return templates.TemplateResponse("notifications/list.html", {"request": request, "notifications": notifications, "user": current_user})
    except Exception as e: logger.error(f"Error listando notificaciones: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error listando notificaciones: {e}"}, status_code=500)

@app.get("/notifications/new", response_class=HTMLResponse)
@require_permission("write")
async def new_notification_form(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    # (Asegúrate que la plantilla notifications/new.html existe)
    try:
        patients_data = await get_all_patients(); patients = patients_data.get("results", [])
        return templates.TemplateResponse("notifications/new.html", {"request": request, "patients": patients, "user": current_user})
    except Exception as e: logger.error(f"Error form nueva notificación: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": str(e)}, status_code=500)

@app.post("/notifications/new")
@require_permission("write")
async def create_new_notification(
    request: Request, patient_id: str = Form(...), message: str = Form(...), channel: str = Form("whatsapp"), status: str = Form("pending"), scheduled_at: Optional[str] = Form(None),
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    logger.info(f"Usuario '{current_user.username}' creando notificación manual para paciente ID: {patient_id}")
    try:
        notification_data = {
            "patient_id": patient_id, "message": message, "channel": channel, "status": status,
            "scheduled_at": scheduled_at or datetime.now(timezone.utc).isoformat(), "metadata": json.dumps({})
        }
        result = await create_notification(notification_data); new_notif_id = result.get("id")
        if result.get("success"):
            logger.info(f"Notificación ID {new_notif_id} creada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="create", resource_type="notification", resource_id=new_notif_id, details=sanitize_data_for_logs({"patient_id":patient_id, "channel":channel, "status":status}))
            return RedirectResponse(url="/notifications", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido creando notificación.")
            logger.error(f"Error creando notificación para paciente {patient_id}: {error_msg}")
            return templates.TemplateResponse("error.html", {"request": request, "error": error_msg}, status_code=400) # Simplificado
    except Exception as e: logger.exception(f"Excepción no controlada creando notificación: {e}"); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado creando notificación: {e}"}, status_code=500)


# --- Rutas de configuración del sistema ---
# (Esta sección debe ser idéntica a la original)
@app.get("/config", response_class=HTMLResponse)
@require_permission("manage_users") # O "manage_config"
async def system_config(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.info(f"Usuario '{current_user.username}' accediendo config sistema.")
    # (Asegúrate que la plantilla config/list.html existe)
    try:
        config_data = await get_all_system_config(); config_items = config_data.get("results", [])
        await log_audit_event(request=request, user_id=current_user.username, action="view_list", resource_type="system_config", details={"count": len(config_items)})
        return templates.TemplateResponse("config/list.html", {"request": request, "config": config_items, "user": current_user})
    except Exception as e: logger.error(f"Error mostrando config: {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error mostrando config: {e}"}, status_code=500)

@app.post("/config/{key}")
@require_permission("manage_users") # O "manage_config"
async def update_config_value(request: Request, key: str, value: str = Form(...), current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.warning(f"Usuario '{current_user.username}' actualizando config: Clave='{key}'")
    try:
        result = await update_system_config(key, value)
        if result.get("success"):
            logger.info(f"Config Clave='{key}' actualizada por '{current_user.username}'.")
            await log_audit_event(request=request, user_id=current_user.username, action="update_config", resource_type="system_config", resource_id=key, details={"new_value": sanitize_data_for_logs({"value":value}).get("value")})
            return RedirectResponse(url="/config", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido actualizando config.")
            logger.error(f"Error actualizando config key='{key}': {error_msg}")
            config_data = await get_all_system_config(); config_items = config_data.get("results", [])
            return templates.TemplateResponse("config/list.html", {"request": request, "config": config_items, "user": current_user, "error": error_msg, "error_key": key}, status_code=400)
    except Exception as e: logger.error(f"Error actualizando config key='{key}': {e}", exc_info=True); return templates.TemplateResponse("error.html", {"request": request, "error": f"Error actualizando config: {e}"}, status_code=500)


# --- API para obtener datos en formato JSON ---
# (Esta sección debe ser idéntica a la original, reemplazar mocks con lógica real)
# Import JSONResponse if not already imported
from fastapi.responses import JSONResponse
import random # Import random if needed for mock data

@app.get("/api/stats/patients")
@require_permission("view_dashboard")
async def api_patient_stats(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.debug(f"Usuario '{current_user.username}' API stats pacientes.")
    try:
        patients_data = await get_all_patients(); patients = patients_data.get("results", [])
        patients_by_month = {}
        for patient in patients:
            created_at_str = patient.get("created_at")
            if created_at_str: created_at_dt = parse_iso_date_flexible(created_at_str); month = created_at_dt.strftime('%Y-%m'); patients_by_month[month] = patients_by_month.get(month, 0) + 1
        sorted_months = sorted(patients_by_month.keys()); labels = sorted_months; data = [patients_by_month[month] for month in sorted_months]
        return JSONResponse({"labels": labels, "data": data, "total": len(patients)})
    except Exception as e: logger.error(f"Error API stats pacientes: {e}", exc_info=True); raise HTTPException(status_code=500, detail=f"Error stats pacientes: {e}")

@app.get("/api/stats/sessions")
@require_permission("view_dashboard")
async def api_session_stats(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    logger.debug(f"Usuario '{current_user.username}' API stats sesiones.")
    try:
        sessions_data = await get_all_citas(); sessions = sessions_data.get("results", [])
        sessions_by_type = {}
        for session in sessions:
            session_type = session.get("session_type", "unknown"); sessions_by_type[session_type] = sessions_by_type.get(session_type, 0) + 1
        labels = list(sessions_by_type.keys()); data = list(sessions_by_type.values())
        return JSONResponse({"labels": labels, "data": data, "total": len(sessions)})
    except Exception as e: logger.error(f"Error API stats sesiones: {e}", exc_info=True); raise HTTPException(status_code=500, detail=f"Error stats sesiones: {e}")

@app.get("/api/stats/dashboard")
@require_permission("view_dashboard")
async def api_dashboard_stats(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Endpoint para obtener estadísticas generales para el dashboard."""
    logger.debug(f"Usuario '{current_user.username}' API stats dashboard.")
    # Reemplazar con lógica real para obtener estadísticas
    stats = { # Mock data
        "patients": {"total": 156, "new_this_month": 12, "active": 98},
        "sessions": {"total": 423, "scheduled": 45, "completed": 356},
        "notifications": {"total": 567, "pending": 12, "failed": 12},
        "security": {"last_backup": (datetime.now() - timedelta(days=1)).isoformat(), "failed_logins_today": 3} # Ejemplo
    }
    return JSONResponse(stats)

@app.get("/api/stats/security")
@require_permission("view_security_stats")
async def api_security_stats(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Endpoint para obtener estadísticas detalladas de seguridad."""
    logger.debug(f"Usuario '{current_user.username}' API stats seguridad.")
    # Reemplazar con lógica real para obtener estadísticas de seguridad
    stats = { # Mock data
        "encryption": {"status": "Activo", "algorithm": "AES-256", "last_key_rotation": (datetime.now() - timedelta(days=30)).isoformat()},
        "backups": {"status": "Activo", "last_backup": (datetime.now() - timedelta(days=1)).isoformat(), "total_backups": 30},
        "access": {"total_logins_today": 12, "failed_logins_today": 3, "suspicious_activities": 0},
        "audit": {"total_logs_today": 156}
    }
    return JSONResponse(stats)

# --- Funciones de utilidad para procesar datos sensibles ---
# (Función sanitize_data_for_logs ya definida arriba y mejorada)
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


# --- Rutas de Seguridad (/security/...) ---
# (Esta sección debe ser idéntica a la original, pendiente de implementar lógica CRUD usuarios con DB)
@app.get("/security/audit-logs", response_class=HTMLResponse)
@require_permission("view_audit_logs")
async def view_audit_logs(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra los registros de auditoría."""
    logger.info(f"Admin '{current_user.username}' viendo logs auditoría.")
    # (Asegúrate que la plantilla security/audit_logs.html existe)
    # Lógica real para obtener logs de DB con filtros y paginación aquí
    audit_logs_example = [] # Mock data (igual que antes)
    actions = ["view_list", "create", "update", "delete", "login_success", "failed_login", "access_denied", "update_config"]
    resources = ["patient", "session", "notification", "user", "auth", "dashboard", "system_config", "endpoint"]
    users = ["admin", "therapist", "receptionist", "system"]
    for i in range(50):
        log_time = datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60*24*3)); action = random.choice(actions)
        resource = random.choice(resources); user_id = random.choice(users) if action not in ["failed_login", "access_denied"] else random.choice(["unknown_user", "therapist", "viewer"])
        details = {"count": random.randint(1, 100) if action == "view_list" else None, "reason": "Invalid credentials" if action == "failed_login" else None, "required_permission": "delete" if action == "access_denied" else None, "updated_fields": ["status", "notes"] if action == "update" else None, "roles": ["admin"] if action == "login_success" and user_id == "admin" else None}
        details = {k: v for k, v in details.items() if v is not None}
        audit_logs_example.append(AuditLog(timestamp=log_time, user_id=user_id, action=action, resource_type=resource, resource_id=f"{resource[:1].upper()}{random.randint(100, 999)}" if resource not in ["auth", "dashboard", "endpoint"] else None, details=details if details else None, ip_address=f"192.168.{random.randint(0,1)}.{random.randint(1, 254)}"))
    audit_logs_example.sort(key=lambda x: x.timestamp, reverse=True)
    return templates.TemplateResponse("security/audit_logs.html", {"request": request, "audit_logs": audit_logs_example, "user": current_user})

@app.get("/security/users", response_class=HTMLResponse)
@require_permission("manage_users") # Permiso específico
async def list_users(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Lista los usuarios del sistema desde la base de datos."""
    logger.info(f"Admin '{current_user.username}' listando usuarios.")
    # (Asegúrate que la plantilla security/users.html existe)
    template_path = "admin/templates/security/users_list.html"
    if not os.path.exists(os.path.dirname(template_path)): os.makedirs(os.path.dirname(template_path), exist_ok=True)
    if not os.path.exists(template_path):
        logger.warning(f"Creando plantilla de ejemplo en: {template_path}")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestionar Usuarios</title>
    <!-- Añadir CSS básico si se desea -->
</head>
<body>
    <h1>Usuarios del Sistema</h1>
    <p><a href="/security/user/new">Crear Nuevo Usuario</a></p>
    {% if error %}<p style="color:red;">Error: {{ error }}</p>{% endif %}
    <table border="1">
        <thead>
            <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Nombre Completo</th>
                <th>Roles</th>
                <th>Activo</th>
                <th>Bloqueado</th>
                <th>Último Login</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for u in users %}
            <tr>
                <td>{{ u.username }}</td>
                <td>{{ u.email or 'N/A' }}</td>
                <td>{{ u.full_name or 'N/A' }}</td>
                <td>{{ u.roles | join(', ') if u.roles else 'N/A' }}</td>
                <td>{{ 'Sí' if u.is_active else 'No' }}</td>
                <td>{{ 'Sí' if u.is_locked else 'No' }}</td>
                <td>{{ u.last_login | format_datetime if u.last_login else 'Nunca' }}</td>
                <td>
                    <a href="/security/user/{{ u.id }}">Ver</a> |
                    <a href="/security/user/{{ u.id }}/edit">Editar</a> |
                    <form action="/security/user/{{ u.id }}/delete" method="post" style="display:inline;" onsubmit="return confirm('¿Eliminar usuario {{ u.username }}?');">
                        <button type="submit">Eliminar</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="8">No se encontraron usuarios.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <p><a href="/dashboard">Volver al Dashboard</a></p>
    <script>
        // Añadir filtro de formato datetime si no está global
        function format_datetime(iso_string) {
            if (!iso_string) return 'Nunca';
            try {
                const dt = new Date(iso_string);
                // Formato simple YYYY-MM-DD HH:MM
                return dt.toISOString().slice(0, 16).replace('T', ' ');
            } catch (e) { return iso_string; }
        }
    </script>
</body>
</html>""")

    users = []
    error_msg = None
    try:
        # Lógica real: llamar a get_all_db_users() de d1_client
        users_data = await get_all_db_users()
        if users_data.get("success"):
            users = users_data.get("users", [])
            logger.info(f"Se obtuvieron {len(users)} usuarios de la DB.")
        else:
            error_msg = users_data.get("error", "Error desconocido al obtener usuarios.")
            logger.error(f"Error al obtener usuarios de la DB: {error_msg}")

        # Registrar auditoría (incluso si falla la obtención, para registrar intento)
        await log_audit_event(
            request=request,
            user_id=current_user.username,
            action="view_list",
            resource_type="user",
            details={"count": len(users), "error_if_any": error_msg}
        )

    except Exception as e:
        logger.exception(f"Excepción al listar usuarios: {e}")
        error_msg = f"Error inesperado del servidor: {e}"
        # Registrar error también en auditoría si ocurre aquí
        await log_audit_event(request=request, user_id=current_user.username, action="view_list_error", resource_type="user", details={"exception": str(e)})

    # Renderizar plantilla pasando usuarios y posible error
    return templates.TemplateResponse(
        template_path,
        {"request": request, "users": users, "user": current_user, "error": error_msg}
    )

@app.get("/security/data-protection", response_class=HTMLResponse)
@require_permission("view_security_stats") # O permiso específico
async def data_protection_dashboard(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Dashboard de protección de datos."""
    logger.info(f"Admin '{current_user.username}' viendo dashboard protección datos.")
    # (Asegúrate que la plantilla security/data_protection.html existe)
    # Lógica real para obtener stats
    stats = {"total_encrypted_fields": 1245, "total_patients": 42, "last_backup": (datetime.now() - timedelta(hours=6)).isoformat()} # Mock
    sensitive_data_events = [{"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), "user_id": random.choice(["admin", "therapist"]), "data_type": random.choice(["session_notes", "payment_info"]), "action": "view"} for i in range(1, 6)] # Mock
    return templates.TemplateResponse("security/data_protection.html", {"request": request, "stats": stats, "sensitive_data_events": sensitive_data_events, "user": current_user})

@app.get("/security/user/new", response_class=HTMLResponse)
@require_permission("manage_users")
async def new_user_form(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra el formulario para crear un nuevo usuario."""
    logger.info(f"Admin '{current_user.username}' solicitando formulario para nuevo usuario.")
    template_path = "admin/templates/security/new_user.html"
    if not os.path.exists(os.path.dirname(template_path)): os.makedirs(os.path.dirname(template_path), exist_ok=True)
    if not os.path.exists(template_path):
        logger.warning(f"Creando plantilla de ejemplo en: {template_path}")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Crear Nuevo Usuario</title>
    <!-- Añadir CSS básico -->
</head>
<body>
    <h1>Crear Nuevo Usuario</h1>
    {% if error %}<p style="color:red;">Error: {{ error }}</p>{% endif %}
    <form action="/security/user/create" method="post">
        <label for="username">Username:</label><br>
        <input type="text" id="username" name="username" required minlength="3" value="{{ form_data.username or '' }}"><br><br>

        <label for="password">Contraseña:</label><br>
        <input type="password" id="password" name="password" required minlength="8"><br><br>

        <label for="email">Email (opcional):</label><br>
        <input type="email" id="email" name="email" value="{{ form_data.email or '' }}"><br><br>

        <label for="full_name">Nombre Completo (opcional):</label><br>
        <input type="text" id="full_name" name="full_name" value="{{ form_data.full_name or '' }}"><br><br>

        <label>Roles:</label><br>
        {% for role in available_roles %}
        <input type="checkbox" id="role_{{ role }}" name="roles" value="{{ role }}" {% if role in (form_data.roles or ['viewer']) %}checked{% endif %}>
        <label for="role_{{ role }}">{{ role }}</label><br>
        {% endfor %}<br>

        <button type="submit">Crear Usuario</button>
    </form>
    <p><a href="/security/users">Cancelar y Volver a la Lista</a></p>
</body>
</html>""")

    available_roles = list(ROLES.keys()) # Obtener roles definidos
    return templates.TemplateResponse(
        template_path,
        {"request": request, "user": current_user, "available_roles": available_roles, "form_data": {}} # Pasar roles y form_data vacío
    )


@app.get("/security/user/{user_id}/edit", response_class=HTMLResponse)
@require_permission("manage_users")
async def edit_user_form(request: Request, user_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Muestra el formulario para editar un usuario existente."""
    logger.info(f"Admin '{current_user.username}' solicitando formulario para editar usuario ID: {user_id}")
    template_path = "admin/templates/security/edit_user.html"
    if not os.path.exists(os.path.dirname(template_path)): os.makedirs(os.path.dirname(template_path), exist_ok=True)
    if not os.path.exists(template_path):
        logger.warning(f"Creando plantilla de ejemplo en: {template_path}")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Editar Usuario</title>
</head>
<body>
    <h1>Editar Usuario: {{ user_data.username }}</h1>
    {% if error %}<p style="color:red;">Error: {{ error }}</p>{% endif %}
    <form action="/security/user/{{ user_data.id }}/update" method="post">
        <label for="username">Username:</label><br>
        <input type="text" id="username" name="username" required minlength="3" value="{{ form_data.get('username', user_data.username) }}"><br><br>

        <label for="email">Email (opcional):</label><br>
        <input type="email" id="email" name="email" value="{{ form_data.get('email', user_data.email or '') }}"><br><br>

        <label for="full_name">Nombre Completo (opcional):</label><br>
        <input type="text" id="full_name" name="full_name" value="{{ form_data.get('full_name', user_data.full_name or '') }}"><br><br>

        <label>Roles:</label><br>
        {% set current_roles = form_data.get('roles', user_data.roles or []) %}
        {% for role in available_roles %}
        <input type="checkbox" id="role_{{ role }}" name="roles" value="{{ role }}" {% if role in current_roles %}checked{% endif %}>
        <label for="role_{{ role }}">{{ role }}</label><br>
        {% endfor %}<br>

        <label for="is_active">Activo:</label>
        <input type="checkbox" id="is_active" name="is_active" value="true" {% if form_data.get('is_active', user_data.is_active) %}checked{% endif %}><br><br>

        <label for="is_locked">Bloqueado:</label>
        <input type="checkbox" id="is_locked" name="is_locked" value="true" {% if form_data.get('is_locked', user_data.is_locked) %}checked{% endif %}><br><br>

        <label for="password">Nueva Contraseña (dejar en blanco para no cambiar):</label><br>
        <input type="password" id="password" name="password" minlength="8"><br><br>

        <button type="submit">Actualizar Usuario</button>
    </form>
    <p><a href="/security/users">Cancelar y Volver a la Lista</a></p>
</body>
</html>""")

    user_data_db = None
    error_msg = None
    try:
        # Lógica real: llamar a get_user_by_id(user_id)
        result = await get_user_by_id(user_id)
        if result.get("success") and result.get("user"):
            user_data_db = result["user"]
            logger.debug(f"Datos del usuario ID {user_id} obtenidos para edición.")
        else:
            error_msg = result.get("error", "Usuario no encontrado.")
            logger.error(f"Error al obtener usuario ID {user_id} para editar: {error_msg}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

        available_roles = list(ROLES.keys())
        return templates.TemplateResponse(
            template_path,
            {
                "request": request,
                "user": current_user,
                "user_data": user_data_db,
                "available_roles": available_roles,
                "form_data": {}, # En GET, form_data está vacío
                "error": None
            }
        )

    except HTTPException:
        # Redirigir a la lista con un mensaje de error (idealmente flash)
        # Por ahora, redirigimos sin mensaje.
        return RedirectResponse(url="/security/users", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.exception(f"Excepción al preparar formulario de edición para usuario ID {user_id}: {e}")
        # También redirigir o mostrar página de error genérica
        return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado: {e}"}, status_code=500)


@app.post("/security/user/{user_id}/update")
@require_permission("manage_users")
async def update_user(
    request: Request,
    user_id: str,
    username: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    full_name: Optional[str] = Form(None),
    roles: List[str] = Form(...),
    is_active: Optional[bool] = Form(None), # Usa Form(None) para booleanos opcionales desde checkbox
    is_locked: Optional[bool] = Form(None), # Checkbox envía valor solo si está marcado
    password: Optional[str] = Form(None), # Nueva contraseña opcional
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    """Procesa la actualización de un usuario existente."""
    logger.warning(f"Admin '{current_user.username}' intentando ACTUALIZAR usuario ID: {user_id}")

    # Mapear valores de checkbox (Form devuelve 'true' o None si no se marca)
    # Convertir a booleano explícitamente
    is_active_bool = True if is_active is not None else False
    is_locked_bool = True if is_locked is not None else False

    # Guardar datos del formulario por si hay error
    form_data = {
        "username": username, "email": email, "full_name": full_name,
        "roles": roles, "is_active": is_active_bool, "is_locked": is_locked_bool
    }
    error_msg = None
    available_roles = list(ROLES.keys())
    template_path = "admin/templates/security/edit_user.html" # Plantilla para mostrar errores

    # --- Validación ---
    if not username or len(username) < 3:
        error_msg = "El nombre de usuario debe tener al menos 3 caracteres."
    if password and len(password) < 8:
        error_msg = "La nueva contraseña debe tener al menos 8 caracteres."
    invalid_roles = [r for r in roles if r not in available_roles]
    if invalid_roles:
        error_msg = f"Roles inválidos seleccionados: {invalid_roles}."

    if error_msg:
        logger.error(f"Error de validación al actualizar usuario ID {user_id}: {error_msg}")
        # Necesitamos volver a obtener los datos del usuario para re-renderizar el form
        user_data_db_result = await get_user_by_id(user_id)
        if not user_data_db_result.get("success"):
             # Si falla obtener los datos originales, no podemos mostrar el form bien
             return templates.TemplateResponse("error.html", {"request": request, "error": f"Error de validación Y no se pudo obtener usuario: {error_msg}"}, status_code=500)

        return templates.TemplateResponse(
            template_path,
            {
                "request": request, "user": current_user,
                "user_data": user_data_db_result["user"], # Datos originales
                "available_roles": available_roles,
                "error": error_msg,
                "form_data": form_data # Datos enviados que causaron error
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # --- Procesamiento ---
    try:
        updates = {
            "username": username.lower().strip(),
            "email": email.lower().strip() if email else None,
            "full_name": full_name.strip() if full_name else None,
            "roles": roles,
            "is_active": is_active_bool,
            "is_locked": is_locked_bool
            # No incluir hashed_password aquí directamente
        }

        # Hashear nueva contraseña solo si se proporcionó
        if password:
            loop = asyncio.get_running_loop()
            hashed_password = await loop.run_in_executor(None, _get_password_hash_sync, password)
            updates["hashed_password"] = hashed_password
            logger.info(f"Se actualizará la contraseña para el usuario ID {user_id}")

        # Llamar a update_db_user de d1_client
        result = await update_db_user(user_id, updates)

        if result.get("success"):
            updated_user_data = result.get("user", {})
            logger.info(f"Usuario ID {user_id} actualizado exitosamente por '{current_user.username}'.")
            # Registrar auditoría
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="update",
                resource_type="user",
                resource_id=user_id,
                details=sanitize_data_for_logs(updates) # Sanitizar antes de loguear
            )
            # Redirigir a la lista de usuarios (idealmente con mensaje flash)
            return RedirectResponse(url="/security/users", status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_msg = result.get("error", "Error desconocido al actualizar usuario en la DB.")
            logger.error(f"Error al actualizar usuario ID {user_id} en DB: {error_msg}")
            # Registrar auditoría del fallo
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="update_failed",
                resource_type="user",
                resource_id=user_id,
                details={"error": error_msg}
            )
            # Volver a mostrar el formulario de edición con el error
            user_data_db_result = await get_user_by_id(user_id) # Reobtener datos base
            if not user_data_db_result.get("success"):
                 return templates.TemplateResponse("error.html", {"request": request, "error": f"Error al actualizar Y no se pudo obtener usuario: {error_msg}"}, status_code=500)

            return templates.TemplateResponse(
                template_path,
                {
                    "request": request, "user": current_user,
                    "user_data": user_data_db_result["user"], # Datos originales
                    "available_roles": available_roles,
                    "error": error_msg,
                    "form_data": form_data # Datos enviados que causaron error
                },
                status_code=status.HTTP_400_BAD_REQUEST # O 500 si es error DB
            )

    except Exception as e:
        logger.exception(f"Excepción al actualizar usuario ID {user_id}: {e}")
        error_msg = f"Error inesperado del servidor: {e}"
        # Registrar auditoría
        await log_audit_event(request=request, user_id=current_user.username, action="update_exception", resource_type="user", resource_id=user_id, details={"exception": str(e)})
        # Mostrar formulario de edición con el error genérico
        user_data_db_result = await get_user_by_id(user_id) # Reobtener datos base
        if not user_data_db_result.get("success"):
             return templates.TemplateResponse("error.html", {"request": request, "error": f"Error inesperado Y no se pudo obtener usuario: {error_msg}"}, status_code=500)

        return templates.TemplateResponse(
            template_path,
            {
                "request": request, "user": current_user,
                "user_data": user_data_db_result["user"], # Datos originales
                "available_roles": available_roles,
                "error": error_msg,
                "form_data": form_data # Mantener datos del form
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.post("/security/user/create")
@require_permission("manage_users")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    full_name: Optional[str] = Form(None),
    roles: List[str] = Form(...),
    current_user: UserWithRoles = Depends(get_current_active_user_with_roles)
):
    """Procesa la creación de un nuevo usuario desde el formulario."""
    logger.warning(f"Admin '{current_user.username}' intentando crear usuario: {username}")
    form_data = {"username": username, "email": email, "full_name": full_name, "roles": roles}
    error_msg = None
    available_roles = list(ROLES.keys())
    template_path = "admin/templates/security/new_user.html"

    # --- Validación ---
    if not password or len(password) < 8:
        error_msg = "La contraseña debe tener al menos 8 caracteres."

    if not username or len(username) < 3:
        error_msg = "El nombre de usuario debe tener al menos 3 caracteres."

    # Validar roles seleccionados
    invalid_roles = [r for r in roles if r not in available_roles]
    if invalid_roles:
        error_msg = f"Roles inválidos seleccionados: {invalid_roles}. Roles disponibles: {available_roles}"

    if error_msg:
        logger.error(f"Error de validación al crear usuario '{username}': {error_msg}")
        return templates.TemplateResponse(
            template_path,
            {"request": request, "user": current_user, "available_roles": available_roles, "error": error_msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # --- Procesamiento ---
    try:
        # 1. Hashear contraseña en hilo separado
        loop = asyncio.get_running_loop()
        hashed_password = await loop.run_in_executor(None, _get_password_hash_sync, password)
        logger.info(f"Hash de contraseña generado para nuevo usuario '{username}'")

        # 2. Preparar datos para la base de datos
        new_user_data = {
            "username": username.lower().strip(), # Guardar en minúsculas
            "email": email.lower().strip() if email else None, # Guardar en minúsculas
            "full_name": full_name.strip() if full_name else None,
            "hashed_password": hashed_password,
            "roles": roles,
            "is_active": True,
            "is_locked": False
            # created_at, updated_at se manejan en DB
        }

        # 3. Llamar a create_db_user de d1_client
        result = await create_db_user(new_user_data)

        if result.get("success"):
            new_user = result.get("user", {})
            new_user_id = new_user.get("id", "N/A")
            logger.info(f"Usuario '{username}' (ID: {new_user_id}) creado exitosamente por '{current_user.username}'.")
            # 4. Registrar auditoría
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="create",
                resource_type="user",
                resource_id=new_user_id,
                details={"username": username, "email": email, "roles": roles}
            )
            # 5. Redirigir a la lista de usuarios
            # TODO: Añadir mensaje flash de éxito si se implementa un sistema de mensajes
            return RedirectResponse(url="/security/users", status_code=status.HTTP_303_SEE_OTHER)
        else:
            # Error devuelto por d1_client (ej: usuario duplicado)
            error_msg = result.get("error", "Error desconocido al crear usuario en la DB.")
            logger.error(f"Error al crear usuario '{username}' en DB: {error_msg}")
            # 4. Registrar auditoría del fallo
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="create_failed",
                resource_type="user",
                details={"username": username, "error": error_msg}
            )
            # 5. Mostrar formulario de nuevo con el error
            return templates.TemplateResponse(
                template_path,
                {"request": request, "user": current_user, "available_roles": available_roles, "error": error_msg, "form_data": form_data},
                status_code=status.HTTP_400_BAD_REQUEST # O 409 si es conflicto
            )

    except Exception as e:
        logger.exception(f"Excepción al crear usuario '{username}': {e}")
        error_msg = f"Error inesperado del servidor: {e}"
        # Registrar auditoría de la excepción
        await log_audit_event(request=request, user_id=current_user.username, action="create_exception", resource_type="user", details={"username": username, "exception": str(e)})
        # Mostrar formulario de nuevo con el error
        return templates.TemplateResponse(
            template_path,
            {"request": request, "user": current_user, "available_roles": available_roles, "error": error_msg, "form_data": form_data},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.post("/security/user/{user_id}/delete")
@require_permission("manage_users")
async def delete_user(request: Request, user_id: str, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Elimina un usuario de la base de datos."""
    # IMPORTANTE: Evitar que el usuario actual se elimine a sí mismo.
    # Añadir 'id' al modelo UserWithRoles o recuperarlo al principio si es necesario
    # Para este ejemplo, asumimos que el 'id' no está directamente en current_user.
    # Necesitaríamos obtener el ID del usuario actual desde la DB si fuera una comprobación estricta.
    # Simplificación: Comparamos el 'username' que sí está en UserWithRoles.
    # Si 'user_id' pudiera ser diferente al 'username', se necesita una lógica más robusta.

    # Recuperar el usuario que se quiere borrar para comparar username (o id si estuviera disponible)
    target_user_data = await get_user_by_id(user_id)
    target_username = None
    if target_user_data and target_user_data.get("success"):
        target_username = target_user_data.get("user", {}).get("username")

    if target_username and target_username == current_user.username:
        logger.error(f"El usuario '{current_user.username}' intentó eliminarse a sí mismo (ID: {user_id}). Operación denegada.")
        # TODO: Mostrar mensaje de error en la lista (usando sistema de mensajes flash)
        return RedirectResponse(url="/security/users", status_code=status.HTTP_303_SEE_OTHER)

    logger.warning(f"Admin '{current_user.username}' intentando ELIMINAR usuario ID: {user_id} (Username: {target_username or 'desconocido'})")
    error_msg = None
    success = False

    try:
        # Lógica real: Llamar a delete_db_user(user_id)
        result = await delete_db_user(user_id)
        success = result.get("success")

        if success:
            logger.info(f"Usuario ID {user_id} (Username: {target_username or 'eliminado'}) eliminado exitosamente por '{current_user.username}'.")
            # Registrar auditoría del éxito
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="delete",
                resource_type="user",
                resource_id=user_id,
                details={"deleted_username": target_username} # Loguear username si lo obtuvimos
            )
        else:
            error_msg = result.get("error", "Error desconocido al eliminar usuario.")
            logger.error(f"Error al eliminar usuario ID {user_id}: {error_msg}")
            # Registrar auditoría del fallo
            await log_audit_event(
                request=request,
                user_id=current_user.username,
                action="delete_failed",
                resource_type="user",
                resource_id=user_id,
                details={"error": error_msg}
            )
            # TODO: Mostrar error_msg en la página de lista de usuarios (mensaje flash)

    except Exception as e:
        logger.exception(f"Excepción al eliminar usuario ID {user_id}: {e}")
        error_msg = f"Error inesperado del servidor: {e}"
        # Registrar auditoría de la excepción
        await log_audit_event(
            request=request,
            user_id=current_user.username,
            action="delete_exception",
            resource_type="user",
            resource_id=user_id,
            details={"exception": str(e)}
        )
        # TODO: Mostrar error_msg en la página de lista de usuarios (mensaje flash)

    # Siempre redirigir a la lista (idealmente con mensaje flash de éxito/error)
    return RedirectResponse(url="/security/users", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/security/backup", response_class=HTMLResponse)
@require_permission("admin") # O permiso específico
async def backup_dashboard(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Dashboard de copias de seguridad."""
    logger.info(f"Admin '{current_user.username}' viendo dashboard backups.")
    # (Asegúrate que la plantilla security/backups.html existe)
    # Lógica real para obtener info de backups
    backups_example = [{"id": f"backup_{i}", "timestamp": (datetime.now() - timedelta(days=i)).isoformat(), "size_mb": random.randint(50, 500), "status": random.choice(["completed", "failed"]), "type": "full" if i%7==0 else "incremental"} for i in range(1, 11)] # Mock
    return templates.TemplateResponse("security/backups.html", {"request": request, "backups": backups_example, "user": current_user})

@app.post("/security/backup/create")
@require_permission("admin") # O permiso específico
async def create_backup(request: Request, backup_type: str = Form("full"), include_files: bool = Form(True), current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Crea una nueva copia de seguridad (pendiente implementar)."""
    logger.warning(f"Admin '{current_user.username}' iniciando backup tipo: {backup_type}")
    # Lógica real para iniciar backup (posiblemente en background task)
    # background_tasks.add_task(run_backup_process, backup_type, include_files)
    await log_audit_event(request=request, user_id=current_user.username, action="create_backup", resource_type="backup", details={"backup_type": backup_type, "include_files": include_files})
    # Redirigir o devolver JSON con estado
    return RedirectResponse(url="/security/backup", status_code=status.HTTP_303_SEE_OTHER) # Simplificado

@app.get("/security/encryption", response_class=HTMLResponse)
@require_permission("admin") # O permiso específico
async def encryption_dashboard(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Dashboard de encriptación."""
    logger.info(f"Admin '{current_user.username}' viendo dashboard encriptación.")
    # (Asegúrate que la plantilla security/encryption.html existe)
    # Lógica real para obtener stats de encriptación
    encryption_stats = {"status": "active", "algorithm": "AES-256 via Fernet", "last_key_rotation": (datetime.now() - timedelta(days=15)).isoformat(), "encrypted_fields_count": 4} # Mock
    return templates.TemplateResponse("security/encryption.html", {"request": request, "encryption_stats": encryption_stats, "user": current_user})

@app.post("/security/encryption/rotate-keys")
@require_permission("admin") # O permiso específico
async def rotate_encryption_keys(request: Request, current_user: UserWithRoles = Depends(get_current_active_user_with_roles)):
    """Rota las claves de encriptación (pendiente implementar)."""
    logger.critical(f"¡Admin '{current_user.username}' iniciando ROTACIÓN DE CLAVES DE ENCRIPTACIÓN!")
    # Lógica real MUY CUIDADOSA para rotar claves (requiere re-encriptar datos o manejar claves antiguas)
    # Esta es una operación compleja y peligrosa si no se hace bien.
    await log_audit_event(request=request, user_id=current_user.username, action="rotate_keys", resource_type="encryption", details={"status": "initiated"})
    return RedirectResponse(url="/security/encryption", status_code=status.HTTP_303_SEE_OTHER) # Simplificado


# --- Función principal para ejecutar la aplicación ---
def run_admin_panel():
    """Ejecuta el panel de administración."""
    logger.info(f"Iniciando Mark Admin Panel v1.1.0 en {settings.HOST}:{settings.ADMIN_PORT}")
    logger.info(f"ENVIRONMENT={settings.ENVIRONMENT}, MAX_LOGIN_ATTEMPTS={MAX_LOGIN_ATTEMPTS}")
    # module_name = os.path.splitext(os.path.basename(__file__))[0] # Ya no es necesario
    uvicorn.run(
        # f"{module_name}:app", # Incorrecto cuando se ejecuta con python -m
        "admin.admin_panel:app", # Ruta de importación correcta desde la raíz del proyecto
        host=settings.HOST, port=settings.ADMIN_PORT,
        reload=(settings.ENVIRONMENT == "development"),
        log_level="info"
    )

if __name__ == "__main__":
    run_admin_panel()


