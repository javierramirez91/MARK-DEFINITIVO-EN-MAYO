"""
Enrutador principal para la API
Organiza y gestiona todas las rutas de la aplicación
"""
from fastapi import APIRouter
from core.config import settings

# Crear router principal
router = APIRouter()

# Importar y registrar sub-routers
from backend.services.conversation import router as conversation_router
from backend.services.user import router as user_router
from backend.services.playbook import router as playbook_router

# Incluir sub-routers
router.include_router(
    conversation_router,
    prefix="/conversation",
    tags=["conversation"],
)

router.include_router(
    user_router,
    prefix="/user",
    tags=["user"],
)

router.include_router(
    playbook_router,
    prefix="/playbook",
    tags=["playbook"],
)

# Ruta de información de la API
@router.get("/info")
async def api_info() -> dict:
    """Devuelve información sobre la API"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "default_language": settings.DEFAULT_LANGUAGE,
    } 