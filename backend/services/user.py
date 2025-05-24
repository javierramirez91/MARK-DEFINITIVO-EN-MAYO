"""
Servicio de usuario
Gestiona la información de los usuarios del sistema
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import time

# Crear router
router = APIRouter()

# Modelos de datos
class UserCreate(BaseModel):
    """Modelo para crear un nuevo usuario"""
    name: str
    email: str
    language: Optional[str] = "es"
    metadata: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    """Modelo para actualizar un usuario existente"""
    name: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class User(BaseModel):
    """Modelo completo de usuario"""
    id: str
    name: str
    email: str
    language: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]
    conversation_ids: List[str]

# Almacenamiento en memoria para usuarios (en producción sería una base de datos)
users: Dict[str, User] = {}

@router.post("", response_model=User)
async def create_user(user_data: UserCreate):
    """
    Crea un nuevo usuario en el sistema
    """
    # Generar ID único
    user_id = str(uuid.uuid4())
    
    # Obtener timestamp actual
    current_time = time.time()
    
    # Crear usuario
    user = User(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        language=user_data.language,
        created_at=current_time,
        updated_at=current_time,
        metadata=user_data.metadata or {},
        conversation_ids=[]
    )
    
    # Guardar usuario
    users[user_id] = user
    
    return user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """
    Recupera un usuario por su ID
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return users[user_id]

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate):
    """
    Actualiza un usuario existente
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Recuperar usuario existente
    user = users[user_id]
    
    # Actualizar campos
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.language is not None:
        user.language = user_data.language
    if user_data.metadata is not None:
        user.metadata.update(user_data.metadata)
    
    # Actualizar timestamp
    user.updated_at = time.time()
    
    # Guardar usuario actualizado
    users[user_id] = user
    
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """
    Elimina un usuario del sistema
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Eliminar usuario
    del users[user_id]
    
    return {"message": "Usuario eliminado correctamente"} 