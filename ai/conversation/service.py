"""
Servicio de conversación para el asistente virtual Mark.
Gestiona el procesamiento de mensajes y la generación de respuestas.
"""
import logging
import uuid
from typing import Dict, List, Optional, Any
import asyncio

# Configurar logging
logger = logging.getLogger("mark.conversation")

class ConversationService:
    """
    Servicio principal para gestionar conversaciones con el asistente virtual.
    Coordina el flujo de conversación, el procesamiento de mensajes y la generación de respuestas.
    """
    
    def __init__(self):
        """Inicializar el servicio de conversación"""
        self.active_sessions = {}
        logger.info("Servicio de conversación inicializado")
        
        # Intentar importar componentes necesarios
        try:
            from core.config import settings
            from ai.claude.client import claude_client
            from ai.langgraph.engine import conversation_engine
            
            self.settings = settings
            self.claude_client = claude_client
            self.conversation_engine = conversation_engine
            self.components_loaded = True
            logger.info("Componentes del servicio de conversación cargados correctamente")
        except ImportError as e:
            logger.error(f"Error al cargar componentes del servicio de conversación: {e}")
            self.components_loaded = False
    
    async def process_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        language: str = "es",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            message: Texto del mensaje del usuario
            user_id: Identificador único del usuario
            session_id: Identificador de la sesión de conversación
            language: Código de idioma (es, ca, en, ar)
            context: Contexto adicional para la conversación
            
        Returns:
            Respuesta generada por el asistente
        """
        # Validar componentes
        if not self.components_loaded:
            logger.error("No se pueden procesar mensajes: componentes no cargados")
            return "Lo siento, el servicio de conversación no está disponible en este momento."
        
        # Generar IDs si no se proporcionan
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Usuario no proporcionado, generando ID: {user_id}")
            
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Sesión no proporcionada, generando ID: {session_id}")
        
        # Inicializar contexto si es necesario
        if context is None:
            context = {}
        
        # Añadir información al contexto
        context.update({
            "language": language,
            "user_id": user_id,
            "session_id": session_id
        })
        
        logger.info(f"Procesando mensaje para usuario {user_id}, sesión {session_id}, idioma {language}")
        
        try:
            # Usar el motor de conversación para procesar el mensaje
            if hasattr(self, 'conversation_engine'):
                result = await self.conversation_engine.process_message(
                    message=message,
                    user_id=user_id,
                    conversation_id=session_id,
                    language=language,
                    context=context
                )
                response = result.get("response", "")
            # Fallback a Claude directo si no hay motor de conversación
            elif hasattr(self, 'claude_client'):
                response = await self.claude_client.generate_response(
                    message=message,
                    language=language,
                    context=context
                )
            else:
                response = "Lo siento, no puedo procesar tu mensaje en este momento."
                
            logger.info(f"Respuesta generada para usuario {user_id}: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de mensajes de una sesión.
        
        Args:
            session_id: Identificador de la sesión
            
        Returns:
            Lista de mensajes en la sesión
        """
        # Implementar recuperación de historial desde la base de datos o memoria
        # Por ahora devolvemos una lista vacía
        return []
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Limpia una sesión de conversación.
        
        Args:
            session_id: Identificador de la sesión a limpiar
            
        Returns:
            True si se limpió correctamente, False en caso contrario
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Sesión {session_id} limpiada")
            return True
        return False

# Crear instancia global del servicio
conversation_service = ConversationService() 