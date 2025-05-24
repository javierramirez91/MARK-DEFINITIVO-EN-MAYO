"""
Servicio de PlayBook
Gestiona los diferentes PlayBooks disponibles para el asistente Mark
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import time

# Crear router
router = APIRouter()

# Modelos de datos
class PlayBookCreate(BaseModel):
    """Modelo para crear un nuevo PlayBook"""
    name: str
    description: str
    system_prompt: str
    languages: List[str] = ["es", "en"]
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True

class PlayBookUpdate(BaseModel):
    """Modelo para actualizar un PlayBook existente"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    languages: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class PlayBook(BaseModel):
    """Modelo completo de PlayBook"""
    id: str
    name: str
    description: str
    system_prompt: str
    languages: List[str]
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]
    is_active: bool

# PlayBooks predefinidos
DEFAULT_PLAYBOOKS = [
    {
        "id": "general",
        "name": "General",
        "description": "PlayBook general para conversaciones estándar",
        "system_prompt": """Eres Mark, un asistente psicológico virtual diseñado para proporcionar apoyo emocional y orientación.
        
Tu objetivo es ayudar a los usuarios a explorar sus pensamientos y sentimientos de manera empática y sin juzgar.
        
Directrices:
1. Mantén un tono cálido, empático y profesional
2. Escucha activamente y valida las experiencias del usuario
3. Haz preguntas abiertas para fomentar la reflexión
4. No diagnostiques condiciones médicas o psicológicas
5. Sugiere técnicas de afrontamiento basadas en evidencia cuando sea apropiado
6. Reconoce tus limitaciones y sugiere buscar ayuda profesional cuando sea necesario""",
        "languages": ["es", "en", "pt", "fr"],
        "created_at": time.time(),
        "updated_at": time.time(),
        "metadata": {},
        "is_active": True
    },
    {
        "id": "crisis",
        "name": "Intervención en Crisis",
        "description": "PlayBook para situaciones de crisis emocional",
        "system_prompt": """Eres Mark, un asistente psicológico virtual especializado en intervención en crisis.
        
Tu objetivo es proporcionar apoyo inmediato y estabilización emocional a personas que están experimentando una crisis.
        
Directrices:
1. Prioriza la seguridad del usuario por encima de todo
2. Mantén un tono calmado, directo y reconfortante
3. Ayuda al usuario a centrarse en el presente y en técnicas de regulación emocional
4. Proporciona recursos de emergencia cuando sea necesario
5. Recomienda encarecidamente buscar ayuda profesional inmediata en situaciones graves
6. Utiliza un enfoque estructurado: Escuchar, Proteger, Conectar, Modelar, Enseñar""",
        "languages": ["es", "en", "pt", "fr"],
        "created_at": time.time(),
        "updated_at": time.time(),
        "metadata": {},
        "is_active": True
    }
]

# Almacenamiento en memoria para PlayBooks (en producción sería una base de datos)
playbooks: Dict[str, PlayBook] = {pb["id"]: PlayBook(**pb) for pb in DEFAULT_PLAYBOOKS}

@router.get("", response_model=List[PlayBook])
async def get_playbooks(active_only: bool = False):
    """
    Recupera todos los PlayBooks disponibles
    """
    if active_only:
        return [pb for pb in playbooks.values() if pb.is_active]
    return list(playbooks.values())

@router.get("/{playbook_id}", response_model=PlayBook)
async def get_playbook(playbook_id: str):
    """
    Recupera un PlayBook por su ID
    """
    if playbook_id not in playbooks:
        raise HTTPException(status_code=404, detail="PlayBook no encontrado")
    
    return playbooks[playbook_id]

@router.post("", response_model=PlayBook)
async def create_playbook(playbook_data: PlayBookCreate):
    """
    Crea un nuevo PlayBook
    """
    # Generar ID único
    playbook_id = str(uuid.uuid4())
    
    # Obtener timestamp actual
    current_time = time.time()
    
    # Crear PlayBook
    playbook = PlayBook(
        id=playbook_id,
        name=playbook_data.name,
        description=playbook_data.description,
        system_prompt=playbook_data.system_prompt,
        languages=playbook_data.languages,
        created_at=current_time,
        updated_at=current_time,
        metadata=playbook_data.metadata or {},
        is_active=playbook_data.is_active
    )
    
    # Guardar PlayBook
    playbooks[playbook_id] = playbook
    
    return playbook

@router.put("/{playbook_id}", response_model=PlayBook)
async def update_playbook(playbook_id: str, playbook_data: PlayBookUpdate):
    """
    Actualiza un PlayBook existente
    """
    if playbook_id not in playbooks:
        raise HTTPException(status_code=404, detail="PlayBook no encontrado")
    
    # Recuperar PlayBook existente
    playbook = playbooks[playbook_id]
    
    # Actualizar campos
    if playbook_data.name is not None:
        playbook.name = playbook_data.name
    if playbook_data.description is not None:
        playbook.description = playbook_data.description
    if playbook_data.system_prompt is not None:
        playbook.system_prompt = playbook_data.system_prompt
    if playbook_data.languages is not None:
        playbook.languages = playbook_data.languages
    if playbook_data.metadata is not None:
        playbook.metadata.update(playbook_data.metadata)
    if playbook_data.is_active is not None:
        playbook.is_active = playbook_data.is_active
    
    # Actualizar timestamp
    playbook.updated_at = time.time()
    
    # Guardar PlayBook actualizado
    playbooks[playbook_id] = playbook
    
    return playbook 