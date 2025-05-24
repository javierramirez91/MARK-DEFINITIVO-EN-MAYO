"""
Servicio de conversación
Gestiona las interacciones con el asistente Mark
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ai.langgraph.playbook_graph import conversation_graph, ConversationState, ConversationMessage
from ai.claude.client import claude
from core.config import settings
import uuid
import time

# Crear router
router = APIRouter()

# Modelos de datos
class MessageRequest(BaseModel):
    """Modelo para solicitar una respuesta del asistente"""
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Modelo para la respuesta del asistente"""
    conversation_id: str
    response: str
    messages: List[ConversationMessage]
    playbook: str
    language: str
    metadata: Dict[str, Any]

# Almacenamiento en memoria para conversaciones (en producción sería una base de datos)
conversations: Dict[str, ConversationState] = {}

@router.post("/message", response_model=MessageResponse)
async def process_message(request: MessageRequest, background_tasks: BackgroundTasks):
    """
    Procesa un mensaje del usuario y devuelve una respuesta del asistente
    """
    # Obtener o crear una conversación
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    if conversation_id in conversations:
        # Recuperar conversación existente
        state = conversations[conversation_id]
    else:
        # Crear nueva conversación
        state = ConversationState(
            language=request.language or settings.DEFAULT_LANGUAGE,
            metadata=request.metadata or {}
        )
    
    # Añadir el mensaje del usuario
    user_message = {"role": "user", "content": request.message}
    state.messages.append(user_message)
    
    # Procesar el mensaje a través del grafo de conversación
    result = await conversation_graph.ainvoke(state)
    
    # Actualizar el estado de la conversación
    conversations[conversation_id] = result
    
    # Obtener la respuesta del asistente
    assistant_message = next((m for m in reversed(result.messages) if m["role"] == "assistant"), None)
    
    # Programar tarea en segundo plano para guardar la conversación en la base de datos
    background_tasks.add_task(save_conversation_to_db, conversation_id, result)
    
    # Devolver la respuesta
    return MessageResponse(
        conversation_id=conversation_id,
        response=assistant_message["content"] if assistant_message else "",
        messages=result.messages,
        playbook=result.current_playbook,
        language=result.language,
        metadata=result.metadata
    )

@router.get("/conversation/{conversation_id}", response_model=MessageResponse)
async def get_conversation(conversation_id: str):
    """
    Recupera una conversación existente por su ID
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    state = conversations[conversation_id]
    
    # Obtener la última respuesta del asistente
    assistant_message = next((m for m in reversed(state.messages) if m["role"] == "assistant"), None)
    
    return MessageResponse(
        conversation_id=conversation_id,
        response=assistant_message["content"] if assistant_message else "",
        messages=state.messages,
        playbook=state.current_playbook,
        language=state.language,
        metadata=state.metadata
    )

async def save_conversation_to_db(conversation_id: str, state: ConversationState):
    """
    Guarda la conversación en la base de datos (simulado)
    En una implementación real, esto guardaría en una base de datos
    """
    # Simulación de guardado en base de datos
    print(f"Guardando conversación {conversation_id} en la base de datos...")
    time.sleep(0.1)  # Simular latencia de base de datos
    print(f"Conversación guardada con {len(state.messages)} mensajes") 