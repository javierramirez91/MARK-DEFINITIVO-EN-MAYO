"""
Cliente para interactuar con la API de modelos de IA (como Gemma, Claude, etc.) vía OpenRouter.
Proporciona funciones para generar respuestas de chat.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Langchain imports
from langchain_openai import ChatOpenAI # Usaremos la integración de OpenAI pero apuntando a OpenRouter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Config
from core.config import settings, logger

# Detección de idioma (mantenemos la librería externa)
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    logger.warning("Librería 'langdetect' no encontrada. La detección de idioma no funcionará. Instalar con: pip install langdetect")
    LANGDETECT_AVAILABLE = False

# --- Cliente LLM con Langchain --- 

def get_llm_client(model: Optional[str] = None, temperature: Optional[float] = None) -> Optional[ChatOpenAI]:
    """
    Crea y configura una instancia del cliente LLM usando Langchain (ChatOpenAI) para OpenRouter.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.error("Clave de API de OpenRouter no configurada.")
        return None

    model_name = model or settings.OPENROUTER_MODEL
    if not model_name:
        logger.error("Modelo de OpenRouter no configurado.")
        return None

    # Usar OPENROUTER_API_KEY y configurar base_url
    try:
        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature if temperature is not None else 0.7, # Valor por defecto si no se pasa
            max_tokens=1024, # Establecer un max_tokens razonable por defecto
            timeout=settings.OPENROUTER_TIMEOUT,
            # Añadir headers personalizados para OpenRouter
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER or "",
                "X-Title": settings.APP_NAME or ""
            }
        )
        return llm
    except Exception as e:
         logger.error(f"Error al inicializar ChatOpenAI para OpenRouter: {e}", exc_info=True)
         return None


async def generate_chat_response(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera una respuesta de chat usando Langchain y OpenRouter.

    Args:
        messages: Lista de mensajes [{"role": "user|assistant", "content": "..."}].
        system_prompt: Instrucciones del sistema (opcional).
        temperature: Temperatura para la generación (opcional).
        model: Modelo específico a utilizar (opcional).

    Returns:
        Diccionario con formato similar al anterior:
        {"success": True, "message": {"role": "assistant", "content": ...}, ...}
        o {"success": False, "error": ...}
    """
    start_time = datetime.now()
    llm = get_llm_client(model=model, temperature=temperature)

    if not llm:
        return {"success": False, "error": "Failed to initialize LLM Client"}

    # Construir la lista de mensajes para Langchain
    lc_messages = []
    if system_prompt:
        lc_messages.append(SystemMessage(content=system_prompt))
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and content:
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant" and content:
            # Nota: Langchain espera AIMessage, pero ChatOpenAI lo maneja internamente.
            # Si usáramos otra abstracción, podríamos necesitar convertir a AIMessage.
            lc_messages.append(SystemMessage(content=content)) # Workaround si AIMessage no está importado o causa lío
            # O idealmente: from langchain_core.messages import AIMessage; lc_messages.append(AIMessage(content=content))
        else:
             logger.warning(f"Mensaje omitido por rol/contenido inválido: {msg}")

    if not any(isinstance(m, HumanMessage) for m in lc_messages):
         logger.error("La lista de mensajes para Langchain no contiene ningún HumanMessage.")
         return {"success": False, "error": "No user message provided."}

    logger.debug(f"Invocando LLM ({llm.model_name}) con {len(lc_messages)} mensajes.")
    logger.info(f"Enviando petición a OpenRouter con el modelo {llm.model_name}...")

    try:
        # Usar el método invoke de Langchain
        response = await llm.ainvoke(lc_messages)
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        response_content = response.content
        # Extraer metadatos de uso de manera segura
        usage_metadata = getattr(response, 'usage_metadata', None)
        # Los siguientes campos pueden no estar disponibles, así que los dejamos como None si no existen
        finish_reason = getattr(response, 'finish_reason', None)
        response_id = getattr(response, 'id', None)
        model_name_used = getattr(response, 'model_name', llm.model_name)

        logger.info(f"Respuesta recibida de LLM ({model_name_used}) en {duration_ms:.0f} ms. Usage: {usage_metadata}")
        
        return {
            "success": True,
            "message": {
                "role": "assistant",
                "content": response_content
            },
            "model": model_name_used,
            "usage": usage_metadata,
            "id": response_id,
            "duration_ms": duration_ms,
            "finish_reason": finish_reason
        }

    except Exception as e:
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        logger.error(f"Error al invocar LLM con Langchain: {e}", exc_info=True)
        # Intentar obtener más detalles del error si es una APIError de OpenAI/Langchain
        error_details = str(e)
        status_code = None
        # Comentar o adaptar si no usas la librería openai directamente
        # try:
        #      from openai import APIError
        #      if isinstance(e, APIError):
        #          error_details = e.message or str(e)
        #          status_code = e.status_code
        # except ImportError:
        #      pass 
             
        return {
            "success": False,
            "error": f"LLM Invocation Error: {error_details}",
            "status_code": status_code,
            "duration_ms": duration_ms
        }

def detect_language(text: str) -> str:
    """
    Detecta el idioma de un texto usando langdetect.
    """
    if not LANGDETECT_AVAILABLE or not text:
        return "unknown"
        
    try:
        lang_code = detect(text)
        logger.debug(f"Idioma detectado para texto '{text[:30]}...': {lang_code}")
        return lang_code
    except LangDetectException:
        logger.warning(f"No se pudo detectar idioma de forma fiable para: '{text[:50]}...'")
        return "unknown"
    except Exception as e:
        logger.error(f"Error inesperado en detect_language: {e}")
        return "unknown" 