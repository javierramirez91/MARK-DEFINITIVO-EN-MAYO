"""
Motor de conversación basado en LangGraph para el asistente virtual Mark.
Implementa un grafo de conversación para gestionar el flujo de diálogo.
"""
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, TypedDict, Literal, Union, cast
import asyncio
import json

# Configurar logging
logger = logging.getLogger("mark.langgraph")

class ConversationEngine:
    """
    Motor de conversación basado en LangGraph.
    Gestiona el flujo de diálogo utilizando un grafo de estados.
    """
    
    def __init__(self):
        """Inicializar el motor de conversación"""
        self.active_conversations = {}
        logger.info("Motor de conversación inicializado")
        
        # Intentar importar componentes necesarios
        try:
            from core.config import settings
            from ai.claude.client import claude_client
            from ai.langsmith.tracing import langsmith_tracing
            
            self.settings = settings
            self.claude_client = claude_client
            self.langsmith_tracing = langsmith_tracing
            self.components_loaded = True
            
            # Intentar importar LangGraph
            try:
                import langgraph.graph
                from langgraph.graph import StateGraph, END
                from langgraph.prebuilt import create_agent_executor
                
                self.langgraph = langgraph
                self.StateGraph = StateGraph
                self.END = END
                self.create_agent_executor = create_agent_executor
                
                # Inicializar el grafo de conversación
                self._initialize_graph()
                
                logger.info("LangGraph cargado correctamente")
            except ImportError as e:
                logger.error(f"Error al cargar LangGraph: {e}")
                self.langgraph = None
                
            logger.info("Componentes del motor de conversación cargados correctamente")
        except ImportError as e:
            logger.error(f"Error al cargar componentes del motor de conversación: {e}")
            self.components_loaded = False
    
    def _initialize_graph(self):
        """Inicializa el grafo de conversación con LangGraph"""
        if not hasattr(self, 'langgraph') or not self.langgraph:
            logger.error("No se puede inicializar el grafo: LangGraph no está disponible")
            return
        
        try:
            # Definir el estado del grafo
            class ConversationState(TypedDict):
                messages: List[Dict[str, str]]
                user_id: str
                conversation_id: str
                language: str
                context: Dict[str, Any]
                current_node: str
                
            # Crear el grafo de estados
            graph = self.StateGraph(ConversationState)
            
            # Definir nodos del grafo
            graph.add_node("start", self._start_conversation)
            graph.add_node("process_message", self._process_message)
            graph.add_node("generate_response", self._generate_response)
            graph.add_node("post_process", self._post_process)
            
            # Definir bordes del grafo
            graph.add_edge("start", "process_message")
            graph.add_edge("process_message", "generate_response")
            graph.add_edge("generate_response", "post_process")
            graph.add_edge("post_process", self.END)
            
            # Compilar el grafo
            self.graph = graph.compile()
            
            logger.info("Grafo de conversación inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar el grafo de conversación: {e}")
            self.graph = None
    
    async def process_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        language: str = "es",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario a través del grafo de conversación.
        
        Args:
            message: Texto del mensaje del usuario
            user_id: Identificador único del usuario
            conversation_id: Identificador de la conversación
            language: Código de idioma (es, ca, en, ar)
            context: Contexto adicional para la conversación
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        # Validar componentes
        if not self.components_loaded:
            logger.error("No se pueden procesar mensajes: componentes no cargados")
            return {"response": "Lo siento, el motor de conversación no está disponible en este momento."}
        
        # Generar IDs si no se proporcionan
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Usuario no proporcionado, generando ID: {user_id}")
            
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            logger.info(f"Conversación no proporcionada, generando ID: {conversation_id}")
        
        # Inicializar contexto si es necesario
        if context is None:
            context = {}
        
        # Añadir información al contexto
        context.update({
            "language": language,
            "user_id": user_id,
            "conversation_id": conversation_id
        })
        
        logger.info(f"Procesando mensaje para usuario {user_id}, conversación {conversation_id}, idioma {language}")
        
        # Si tenemos LangGraph disponible, usar el grafo
        if hasattr(self, 'graph') and self.graph:
            try:
                # Preparar el estado inicial
                initial_state = {
                    "messages": [{"role": "user", "content": message}],
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "language": language,
                    "context": context,
                    "current_node": "start"
                }
                
                # Ejecutar el grafo
                with self.langsmith_tracing.get_tracer(
                    conversation_id=conversation_id,
                    user_id=user_id
                ) as tracer:
                    result = await self.graph.ainvoke(initial_state, config={"callbacks": [tracer]})
                
                # Extraer la respuesta
                response = ""
                for msg in result["messages"]:
                    if msg["role"] == "assistant":
                        response = msg["content"]
                        break
                
                # Guardar la conversación activa
                self.active_conversations[conversation_id] = result
                
                return {
                    "response": response,
                    "conversation_id": conversation_id,
                    "messages": result["messages"]
                }
                
            except Exception as e:
                logger.error(f"Error al ejecutar el grafo de conversación: {e}")
                # Fallback a Claude directo
        
        # Fallback: usar Claude directamente
        try:
            # Usar el cliente de Claude para generar una respuesta
            system_prompt = self._get_system_prompt(language)
            
            response = await self.claude_client.generate_response(
                message=message,
                system_prompt=system_prompt,
                language=language,
                context=context
            )
            
            # Crear mensajes
            messages = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
            
            return {
                "response": response,
                "conversation_id": conversation_id,
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Error al generar respuesta con Claude: {e}")
            return {
                "response": "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo.",
                "conversation_id": conversation_id,
                "messages": [{"role": "user", "content": message}]
            }
    
    async def _start_conversation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nodo inicial del grafo de conversación"""
        logger.info(f"Iniciando conversación: {state['conversation_id']}")
        state["current_node"] = "start"
        return state
    
    async def _process_message(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa el mensaje del usuario"""
        logger.info(f"Procesando mensaje en conversación: {state['conversation_id']}")
        state["current_node"] = "process_message"
        # Aquí se podrían aplicar preprocesamiento, detección de intenciones, etc.
        return state
    
    async def _generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Genera una respuesta utilizando Claude"""
        logger.info(f"Generando respuesta en conversación: {state['conversation_id']}")
        state["current_node"] = "generate_response"
        
        try:
            # Extraer el último mensaje del usuario
            user_message = ""
            for msg in state["messages"]:
                if msg["role"] == "user":
                    user_message = msg["content"]
            
            # Generar respuesta con Claude
            system_prompt = self._get_system_prompt(state["language"])
            
            response = await self.claude_client.generate_response(
                message=user_message,
                system_prompt=system_prompt,
                language=state["language"],
                context=state["context"]
            )
            
            # Añadir la respuesta a los mensajes
            state["messages"].append({"role": "assistant", "content": response})
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            state["messages"].append({
                "role": "assistant", 
                "content": "Lo siento, ha ocurrido un error al generar una respuesta."
            })
        
        return state
    
    async def _post_process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza procesamiento posterior a la generación de la respuesta"""
        logger.info(f"Post-procesando respuesta en conversación: {state['conversation_id']}")
        state["current_node"] = "post_process"
        # Aquí se podrían aplicar filtros, evaluación de calidad, etc.
        return state
    
    def _get_system_prompt(self, language: str = "es") -> str:
        """
        Obtiene el prompt de sistema según el idioma.
        
        Args:
            language: Código de idioma (es, ca, en, ar)
            
        Returns:
            Prompt de sistema
        """
        # Usar el método del cliente de Claude para obtener el prompt
        if hasattr(self, 'claude_client'):
            return self.claude_client._get_default_system_prompt(language)
        
        # Fallback a prompt predeterminado en español
        return """Eres Mark, el asistente virtual del Centre de Psicologia Jaume I en Castellón, España. 
Tu objetivo es ayudar a los usuarios proporcionando información sobre los servicios del centro, 
respondiendo preguntas frecuentes, y facilitando la programación de citas. 
Debes ser amable, profesional y empático en todo momento."""

# Crear instancia global del motor
conversation_engine = ConversationEngine() 