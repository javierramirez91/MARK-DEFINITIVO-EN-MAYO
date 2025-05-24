"""
Grafo de flujo de conversación para PlayBooks
Implementa la lógica de flujo de conversación utilizando LangGraph
"""
from typing import Dict, List, Any, Literal, TypedDict, Optional, Tuple, Union
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from ai.claude.client import claude
from ai.serper.search import serper
from ai.langsmith.tracing import langsmith
from core.config import settings
import re

# Definición de tipos para el estado del grafo
class ConversationMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str

class ConversationState(BaseModel):
    messages: List[ConversationMessage] = Field(default_factory=list)
    current_playbook: str = "general"
    language: str = "es"
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    needs_web_search: bool = False
    search_results: Optional[str] = None
    appointment_requested: bool = False
    payment_requested: bool = False
    user_id: Optional[str] = None

# Nodos del grafo
async def detect_language(state: ConversationState) -> Dict[str, Any]:
    """Detecta el idioma del mensaje del usuario"""
    if not state.messages:
        return {"language": settings.DEFAULT_LANGUAGE}
    
    last_user_message = next((m for m in reversed(state.messages) if m["role"] == "user"), None)
    if not last_user_message:
        return {"language": state.language}
    
    # Usar Claude para detectar el idioma
    prompt = f"""
    Detecta el idioma del siguiente texto y devuelve solo el código de idioma correspondiente.
    Códigos de idioma soportados: es (Español), ca (Catalán), en (Inglés), ar (Árabe).
    Si no estás seguro o el idioma no está en la lista, devuelve 'es'.
    
    Texto: {last_user_message["content"]}
    
    Responde solo con el código de idioma, sin explicaciones ni puntuación adicional.
    """
    
    try:
        # Usar el cliente de Claude para detectar el idioma
        language_response = await claude.get_response_text(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        
        # Limpiar la respuesta para obtener solo el código de idioma
        detected_language = language_response.strip().lower()
        
        # Verificar que el idioma detectado sea uno de los soportados
        if detected_language in settings.SUPPORTED_LANGUAGES:
            return {"language": detected_language}
        else:
            return {"language": settings.DEFAULT_LANGUAGE}
    except Exception as e:
        print(f"Error al detectar idioma: {e}")
        return {"language": settings.DEFAULT_LANGUAGE}

async def select_playbook(state: ConversationState) -> Dict[str, str]:
    """Selecciona el PlayBook adecuado basado en el mensaje del usuario"""
    if not state.messages:
        return {"current_playbook": "general"}
    
    last_user_message = next((m for m in reversed(state.messages) if m["role"] == "user"), None)
    if not last_user_message:
        return {"current_playbook": state.current_playbook}
    
    # Usar Claude para determinar el PlayBook adecuado
    prompt = f"""
    Analiza el siguiente mensaje y determina qué PlayBook debería usarse para responder.
    
    Mensaje: {last_user_message["content"]}
    
    PlayBooks disponibles:
    - general: Para conversaciones estándar y apoyo emocional general.
    - crisis: Para situaciones que requieren apoyo inmediato y estabilización emocional.
    - appointment: Para solicitudes de programación de citas.
    - payment: Para consultas relacionadas con pagos.
    - info: Para preguntas sobre el Centre de Psicologia Jaume I.
    
    Responde solo con el nombre del PlayBook, sin explicaciones ni puntuación adicional.
    """
    
    try:
        # Usar el cliente de Claude para seleccionar el PlayBook
        playbook_response = await claude.get_response_text(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        
        # Limpiar la respuesta para obtener solo el nombre del PlayBook
        selected_playbook = playbook_response.strip().lower()
        
        # Verificar que el PlayBook seleccionado sea uno de los disponibles
        valid_playbooks = ["general", "crisis", "appointment", "payment", "info"]
        if selected_playbook in valid_playbooks:
            
            # Actualizar flags según el PlayBook seleccionado
            updates = {"current_playbook": selected_playbook}
            
            if selected_playbook == "appointment":
                updates["appointment_requested"] = True
                
            if selected_playbook == "payment":
                updates["payment_requested"] = True
                
            return updates
        else:
            return {"current_playbook": "general"}
    except Exception as e:
        print(f"Error al seleccionar PlayBook: {e}")
        return {"current_playbook": "general"}

async def check_web_search_needed(state: ConversationState) -> Dict[str, Any]:
    """Determina si se necesita realizar una búsqueda web"""
    if not state.messages:
        return {"needs_web_search": False}
    
    last_user_message = next((m for m in reversed(state.messages) if m["role"] == "user"), None)
    if not last_user_message:
        return {"needs_web_search": False}
    
    # Usar Claude para determinar si se necesita búsqueda web
    prompt = f"""
    Analiza el siguiente mensaje y determina si requiere información actualizada de internet para responder adecuadamente.
    
    Mensaje: {last_user_message["content"]}
    
    Responde solo con "sí" o "no", sin explicaciones ni puntuación adicional.
    """
    
    try:
        # Usar el cliente de Claude para determinar si se necesita búsqueda web
        search_response = await claude.get_response_text(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        
        # Limpiar la respuesta
        needs_search = search_response.strip().lower()
        
        if needs_search in ["sí", "si", "yes", "true", "verdadero"]:
            return {"needs_web_search": True}
        else:
            return {"needs_web_search": False}
    except Exception as e:
        print(f"Error al determinar si se necesita búsqueda web: {e}")
        return {"needs_web_search": False}

async def perform_web_search(state: ConversationState) -> Dict[str, Any]:
    """Realiza una búsqueda web si es necesario"""
    if not state.needs_web_search:
        return {"search_results": None}
    
    last_user_message = next((m for m in reversed(state.messages) if m["role"] == "user"), None)
    if not last_user_message:
        return {"search_results": None}
    
    try:
        # Extraer la consulta de búsqueda del mensaje del usuario
        search_query = last_user_message["content"]
        
        # Realizar la búsqueda web
        search_results = await serper.search_and_format(
            query=search_query,
            language=state.language,
            max_results=3
        )
        
        return {"search_results": search_results}
    except Exception as e:
        print(f"Error al realizar búsqueda web: {e}")
        return {"search_results": None}

async def generate_response(state: ConversationState) -> Dict[str, Any]:
    """Genera una respuesta utilizando el PlayBook actual"""
    # Construir el sistema prompt basado en el PlayBook y el idioma
    system_prompts = {
        "general": {
            "es": """Eres Mark, un asistente psicológico virtual del Centre de Psicologia Jaume I. Tu objetivo es proporcionar apoyo emocional y orientación de manera empática y profesional. Responde siempre en español.""",
            "ca": """Ets Mark, un assistent psicològic virtual del Centre de Psicologia Jaume I. El teu objectiu és proporcionar suport emocional i orientació de manera empàtica i professional. Respon sempre en català.""",
            "en": """You are Mark, a virtual psychological assistant from the Centre de Psicologia Jaume I. Your goal is to provide emotional support and guidance in an empathetic and professional manner. Always respond in English.""",
            "ar": """أنت مارك، مساعد نفسي افتراضي من مركز علم النفس خاومي الأول. هدفك هو تقديم الدعم العاطفي والتوجيه بطريقة متعاطفة ومهنية. قم دائمًا بالرد باللغة العربية."""
        },
        "crisis": {
            "es": """Eres Mark, un asistente psicológico virtual del Centre de Psicologia Jaume I especializado en intervención en crisis. Tu prioridad es la seguridad del usuario y proporcionar apoyo inmediato. Responde siempre en español.""",
            "ca": """Ets Mark, un assistent psicològic virtual del Centre de Psicologia Jaume I especialitzat en intervenció en crisis. La teva prioritat és la seguretat de l'usuari i proporcionar suport immediat. Respon sempre en català.""",
            "en": """You are Mark, a virtual psychological assistant from the Centre de Psicologia Jaume I specialized in crisis intervention. Your priority is the user's safety and providing immediate support. Always respond in English.""",
            "ar": """أنت مارك، مساعد نفسي افتراضي من مركز علم النفس خاومي الأول متخصص في التدخل في الأزمات. أولويتك هي سلامة المستخدم وتقديم الدعم الفوري. قم دائمًا بالرد باللغة العربية."""
        },
        "appointment": {
            "es": """Eres Mark, un asistente virtual del Centre de Psicologia Jaume I encargado de gestionar citas. Ayuda al usuario a programar, modificar o cancelar citas con los psicólogos del centro. Responde siempre en español.""",
            "ca": """Ets Mark, un assistent virtual del Centre de Psicologia Jaume I encarregat de gestionar cites. Ajuda a l'usuari a programar, modificar o cancel·lar cites amb els psicòlegs del centre. Respon sempre en català.""",
            "en": """You are Mark, a virtual assistant from the Centre de Psicologia Jaume I in charge of managing appointments. Help the user schedule, modify, or cancel appointments with the center's psychologists. Always respond in English.""",
            "ar": """أنت مارك، مساعد افتراضي من مركز علم النفس خاومي الأول مسؤول عن إدارة المواعيد. ساعد المستخدم في جدولة أو تعديل أو إلغاء المواعيد مع أخصائيي علم النفس في المركز. قم دائمًا بالرد باللغة العربية."""
        },
        "payment": {
            "es": """Eres Mark, un asistente virtual del Centre de Psicologia Jaume I encargado de gestionar pagos. Ayuda al usuario con información sobre precios, métodos de pago y facturación. Responde siempre en español.""",
            "ca": """Ets Mark, un assistent virtual del Centre de Psicologia Jaume I encarregat de gestionar pagaments. Ajuda a l'usuari amb informació sobre preus, mètodes de pagament i facturació. Respon sempre en català.""",
            "en": """You are Mark, a virtual assistant from the Centre de Psicologia Jaume I in charge of managing payments. Help the user with information about prices, payment methods, and billing. Always respond in English.""",
            "ar": """أنت مارك، مساعد افتراضي من مركز علم النفس خاومي الأول مسؤول عن إدارة المدفوعات. ساعد المستخدم بمعلومات حول الأسعار وطرق الدفع والفواتير. قم دائمًا بالرد باللغة العربية."""
        },
        "info": {
            "es": """Eres Mark, un asistente virtual del Centre de Psicologia Jaume I. Proporciona información precisa sobre los servicios, horarios, ubicación y profesionales del centro. Responde siempre en español.""",
            "ca": """Ets Mark, un assistent virtual del Centre de Psicologia Jaume I. Proporciona informació precisa sobre els serveis, horaris, ubicació i professionals del centre. Respon sempre en català.""",
            "en": """You are Mark, a virtual assistant from the Centre de Psicologia Jaume I. Provide accurate information about the center's services, hours, location, and professionals. Always respond in English.""",
            "ar": """أنت مارك، مساعد افتراضي من مركز علم النفس خاومي الأول. قدم معلومات دقيقة حول خدمات المركز وساعات العمل والموقع والمهنيين. قم دائمًا بالرد باللغة العربية."""
        }
    }
    
    # Obtener el sistema prompt adecuado
    playbook = state.current_playbook
    language = state.language
    
    # Si no existe el playbook o idioma específico, usar el general en español
    system_prompt = system_prompts.get(playbook, system_prompts["general"]).get(language, system_prompts["general"]["es"])
    
    # Añadir información de búsqueda web si está disponible
    if state.search_results:
        system_prompt += f"\n\nInformación adicional de búsqueda web:\n{state.search_results}"
    
    # Generar respuesta con Claude
    try:
        # Crear un tracer de LangSmith para monitorear la generación
        tracer = langsmith.get_tracer(run_name=f"mark_response_{playbook}_{language}")
        callbacks = [tracer] if tracer else []
        
        # Configurar el modelo de Claude con LangChain para trazabilidad
        model = ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            anthropic_api_key=settings.CLAUDE_API_KEY,
            temperature=0.7,
        )
        
        # Convertir mensajes al formato de LangChain Core
        langchain_messages = []
        langchain_messages.append(SystemMessage(content=system_prompt))
        
        for msg in state.messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        # Generar respuesta usando ainvoke con callbacks
        response = await model.ainvoke(langchain_messages, config={"callbacks": callbacks})
        response_text = response.content
        
        # Evaluar la calidad de la respuesta
        last_user_message = next((m for m in reversed(state.messages) if m["role"] == "user"), None)
        if last_user_message:
            try:
                await langsmith.evaluate_response(
                    prompt=last_user_message["content"],
                    response=response_text,
                    expected_language=language
                )
            except Exception as eval_err:
                print(f"Error during LangSmith evaluation: {eval_err}")
        
        # Crear mensaje del asistente
        assistant_message = {
            "role": "assistant",
            "content": response_text
        }
        
        # Actualizar los mensajes con la respuesta del asistente
        updated_messages = state.messages.copy()
        updated_messages.append(assistant_message)
        
        return {"messages": updated_messages}
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        
        # En caso de error, proporcionar una respuesta de fallback
        fallback_responses = {
            "es": "Lo siento, estoy teniendo problemas para procesar tu solicitud. Por favor, inténtalo de nuevo más tarde o contacta directamente con el centro al +34 637885915.",
            "ca": "Ho sento, estic tenint problemes per processar la teva sol·licitud. Si us plau, intenta-ho de nou més tard o contacta directament amb el centre al +34 637885915.",
            "en": "I'm sorry, I'm having trouble processing your request. Please try again later or contact the center directly at +34 637885915.",
            "ar": "آسف، أواجه مشكلة في معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا أو الاتصال بالمركز مباشرة على +34 637885915."
        }
        
        fallback_message = {
            "role": "assistant",
            "content": fallback_responses.get(language, fallback_responses["es"])
        }
        
        updated_messages = state.messages.copy()
        updated_messages.append(fallback_message)
        
        return {"messages": updated_messages}

def should_search_web(state: ConversationState) -> Literal["perform_web_search", "generate_response"]:
    """Decide si realizar una búsqueda web o generar una respuesta"""
    if state.needs_web_search:
        return "perform_web_search"
    else:
        return "generate_response"

def router(state: ConversationState) -> str:
    """Función de enrutamiento condicional"""
    # Aquí podríamos añadir lógica más compleja si fuera necesario
    return "should_search_web"

def build_conversation_graph() -> StateGraph:
    """Construye y compila el grafo de conversación"""
    graph = StateGraph(ConversationState)

    # Añadir nodos
    graph.add_node("detect_language", detect_language)
    graph.add_node("select_playbook", select_playbook)
    graph.add_node("check_web_search", check_web_search_needed)
    graph.add_node("perform_web_search", perform_web_search)
    graph.add_node("generate_response", generate_response)

    # Definir punto de entrada
    graph.set_entry_point("detect_language")

    # Añadir bordes
    graph.add_edge("detect_language", "select_playbook")
    graph.add_edge("select_playbook", "check_web_search")

    # Borde condicional después de verificar si se necesita búsqueda web
    graph.add_conditional_edges(
        "check_web_search",
        should_search_web,
        {
            "perform_web_search": "perform_web_search",
            "generate_response": "generate_response"
        }
    )

    # Borde desde la búsqueda web a la generación de respuesta
    graph.add_edge("perform_web_search", "generate_response")

    # Borde final
    graph.add_edge("generate_response", END)

    # Compilar el grafo
    return graph.compile()

# Crear instancia del grafo compilado
playbook_graph = build_conversation_graph() 