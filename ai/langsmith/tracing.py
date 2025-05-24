"""
Integración con LangSmith para monitoreo y observabilidad.
Proporciona funcionalidades para rastrear y evaluar conversaciones.
"""
import os
import logging
from typing import Dict, List, Optional, Any, Callable
from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer
from langchain_core.callbacks.manager import CallbackManager

# Configurar logging
logger = logging.getLogger("mark.langsmith")

class LangSmithTracing:
    """
    Cliente para interactuar con LangSmith para monitoreo y observabilidad.
    Permite rastrear conversaciones y evaluar respuestas.
    """
    
    def __init__(self, api_key: Optional[str] = None, project_name: Optional[str] = None):
        """
        Inicializar el cliente de LangSmith.
        
        Args:
            api_key: Clave API de LangSmith (opcional, por defecto usa la de settings)
            project_name: Nombre del proyecto en LangSmith (opcional, por defecto usa el de settings)
        """
        self.client: Optional[Client] = None
        self.api_key: Optional[str] = None
        self.project_name: Optional[str] = "default"
        self.endpoint: Optional[str] = "https://api.smith.langchain.com"
        self.tracing_enabled: bool = False

        # Intentar importar configuración
        try:
            from core.config import settings
            self.api_key = api_key or settings.LANGCHAIN_API_KEY
            self.project_name = project_name or settings.LANGCHAIN_PROJECT
            self.endpoint = settings.LANGCHAIN_ENDPOINT
            # Assuming settings object has a boolean flag now, or adjust as needed
            self.tracing_enabled = getattr(settings, 'LANGSMITH_TRACING_ENABLED', False)
        except ImportError:
            logger.warning("Could not import core.config settings. Falling back to environment variables for LangSmith.")
            self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
            self.project_name = project_name or os.getenv("LANGCHAIN_PROJECT", "mark-assistant")
            self.endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
            self.tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

        # Configurar variables de entorno para LangSmith (needed for some integrations)
        if self.api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.api_key
        if self.project_name:
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
        if self.endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
        if self.tracing_enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        else:
            # Ensure tracing is explicitly disabled if needed by other parts of langchain
            os.environ["LANGCHAIN_TRACING_V2"] = "false"

        # Inicializar cliente si hay API key y tracing habilitado
        if self.api_key and self.tracing_enabled:
            try:
                self.client = Client(
                    api_key=self.api_key,
                    api_url=self.endpoint
                )
                logger.info(f"LangSmith Client initialized for project '{self.project_name}'. Tracing enabled.")
            except Exception as e:
                logger.error(f"Error initializing LangSmith Client: {e}")
                self.client = None # Ensure client is None on failure
                self.tracing_enabled = False # Disable tracing if client fails
        elif not self.tracing_enabled:
             logger.info("LangSmith tracing explicitly disabled.")
        else: # No API Key
             logger.warning("LangSmith API Key not found. LangSmith tracing disabled.")
             self.tracing_enabled = False
    
    def get_tracer(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[LangChainTracer]:
        """
        Obtiene un tracer de LangChain para rastrear una conversación, si el tracing está habilitado.
        
        Args:
            conversation_id: ID de la conversación a rastrear
            user_id: ID del usuario asociado a la conversación
            
        Returns:
            Tracer de LangChain configurado o None si el tracing está deshabilitado.
        """
        if not self.tracing_enabled or not self.client:
            return None

        # Crear metadatos para el tracer
        metadata = {}
        if conversation_id:
            metadata["conversation_id"] = conversation_id
        if user_id:
            metadata["user_id"] = user_id

        # Crear tracer
        try:
            # Note: LangChainTracer might have slightly different args or be deprecated
            # depending on the exact langchain-core version. Check documentation if issues arise.
            tracer = LangChainTracer(
                project_name=self.project_name,
                # client=self.client, # Client might be implicitly used via env vars
                tags=["mark-assistant"],
                # metadata=metadata # Metadata might be passed differently now
            )
            # TODO: Verify how to pass metadata correctly in newer versions if needed.
            return tracer
        except Exception as e:
            logger.error(f"Error creating LangChainTracer: {e}")
            return None
    
    def get_callback_manager(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[CallbackManager]:
        """
        Obtiene un gestor de callbacks con el tracer configurado, si el tracing está habilitado.
        
        Args:
            conversation_id: ID de la conversación a rastrear
            user_id: ID del usuario asociado a la conversación
            
        Returns:
            Gestor de callbacks configurado o None.
        """
        tracer = self.get_tracer(conversation_id, user_id)
        if tracer:
            try:
                 # CallbackManager might take optional list or varargs depending on version
                return CallbackManager([tracer])
            except Exception as e:
                 logger.error(f"Error creating CallbackManager: {e}")
                 return None
        return None
    
    async def evaluate_response(
        self,
        response: str,
        criteria: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        prompt: Optional[str] = None, # Added prompt for context
        expected_language: Optional[str] = None # Added expected language
    ) -> Dict[str, Any]:
        """
        Evalúa la calidad de una respuesta según criterios predefinidos.
        
        Args:
            response: Texto de la respuesta a evaluar
            criteria: Criterios de evaluación adicionales
            conversation_id: ID de la conversación
            user_id: ID del usuario
            prompt: El prompt o mensaje del usuario que generó la respuesta
            expected_language: El idioma esperado de la respuesta
            
        Returns:
            Resultados de la evaluación
        """
        if not self.client or not self.tracing_enabled:
            # logger.error("Cannot evaluate response: LangSmith client not initialized or tracing disabled.")
            # Reduce log noise if evaluation is not implemented yet
            return {"evaluation_skipped": "LangSmith client/tracing not enabled"}

        # Criterios predeterminados de evaluación
        default_criteria = {
            "helpfulness": "¿La respuesta es útil y relevante para la consulta del usuario?",
            "accuracy": "¿La respuesta es precisa y correcta?",
            "clarity": "¿La respuesta es clara y fácil de entender?",
            "empathy": "¿La respuesta muestra empatía y comprensión hacia el usuario?",
            "safety": "¿La respuesta es segura y apropiada?"
        }
        if expected_language:
            default_criteria["language_match"] = f"¿La respuesta está en el idioma esperado ({expected_language})?"

        # Combinar con criterios adicionales
        if criteria:
            default_criteria.update(criteria)

        # Crear metadatos
        metadata = {}
        if conversation_id:
            metadata["conversation_id"] = conversation_id
        if user_id:
            metadata["user_id"] = user_id

        try:
            # TODO: Implement actual LangSmith evaluation logic here.
            # This might involve creating runs, feedback, or using evaluation functions.
            # Example: client.create_feedback(...) or using evaluation utilities.
            # For now, returning a simulated result.
            results = {
                criterion: {"score": 0.9, "reasoning": f"Evaluation for '{criterion}' pending implementation."}
                for criterion in default_criteria
            }

            # Simulate language check if applicable
            if expected_language and "language_match" in results:
                 # Basic check (replace with actual language detection if needed)
                 # detected_lang = detect(response) # Needs langdetect library
                 # results["language_match"]["score"] = 1.0 if detected_lang == expected_language else 0.0
                 results["language_match"]["score"] = 0.8 # Placeholder
                 results["language_match"]["reasoning"] = f"Placeholder score for language match ({expected_language})"

            overall_score = sum(result.get("score", 0) for result in results.values()) / len(results) if results else 0

            logger.debug(f"Simulated evaluation complete for conv {conversation_id}. Score: {overall_score:.2f}")

            return {
                "overall_score": overall_score,
                "criteria_scores": results,
                "metadata": metadata,
                "status": "pending_implementation"
            }

        except Exception as e:
            logger.error(f"Error during evaluate_response: {e}", exc_info=True)
            return {"error": str(e)}

# Crear instancia global
langsmith_tracing = LangSmithTracing() 