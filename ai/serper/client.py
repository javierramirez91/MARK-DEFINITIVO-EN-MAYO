"""
Cliente para el servicio Serper.dev que permite realizar búsquedas web.
Se utiliza para proporcionar información actualizada a Mark cuando sea necesario.
"""
import logging
import json
import time
import urllib.parse
from typing import Dict, List, Optional, Any, Union
import httpx

from core.config import ApiConfig
from ai.langsmith.client import trace_function

logger = logging.getLogger("mark-assistant.serper")

@trace_function(name="serper_search", run_type="tool")
async def search_web(
    query: str,
    search_type: str = "search",
    num_results: int = 5,
    country: str = "es", 
    language: str = "es",
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Realiza una búsqueda web utilizando Serper.dev
    
    Args:
        query: Consulta de búsqueda
        search_type: Tipo de búsqueda ("search", "news", "images", "places")
        num_results: Número de resultados a devolver
        country: Código de país para la búsqueda
        language: Código de idioma para la búsqueda
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Resultados de la búsqueda como diccionario
    """
    if not ApiConfig.SERPER_API_KEY:
        logger.error("Clave API de Serper no configurada")
        return {"error": "API key no configurada", "results": []}
    
    # Asegurar que la consulta sea segura para URL
    query = urllib.parse.quote_plus(query)
    
    # Mapear código de idioma de nuestra app a código Google
    language_mapping = {
        "es": "es",
        "ca": "ca",
        "en": "en",
        "ar": "ar",
    }
    
    # Usar idioma español por defecto si no está en el mapeo
    search_language = language_mapping.get(language, "es")
    
    # Definir los headers con la clave API
    headers = {
        "X-API-KEY": ApiConfig.SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Construir el payload para la solicitud
    payload = {
        "q": query,
        "gl": country,
        "hl": search_language,
        "num": num_results
    }
    
    # Determinar la URL correcta según el tipo de búsqueda
    if search_type == "news":
        endpoint = f"{ApiConfig.SERPER_ENDPOINT}/news"
    elif search_type == "images":
        endpoint = f"{ApiConfig.SERPER_ENDPOINT}/images"
    elif search_type == "places":
        endpoint = f"{ApiConfig.SERPER_ENDPOINT}/places"
    else:  # búsqueda web estándar
        endpoint = f"{ApiConfig.SERPER_ENDPOINT}/search"
    
    try:
        logger.info(f"Realizando búsqueda: '{query}' en {search_type}, idioma: {search_language}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # Verificar si la respuesta es exitosa
            response.raise_for_status()
            
            # Parsear respuesta JSON
            results = response.json()
            
            return {
                "query": query,
                "type": search_type,
                "results": results
            }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP al buscar: {e}")
        return {
            "error": f"Error HTTP: {e.response.status_code}",
            "results": []
        }
    except httpx.RequestError as e:
        logger.error(f"Error de solicitud al buscar: {e}")
        return {
            "error": f"Error de solicitud: {str(e)}",
            "results": []
        }
    except Exception as e:
        logger.error(f"Error al buscar con Serper: {e}")
        return {
            "error": f"Error inesperado: {str(e)}",
            "results": []
        }

def extract_snippets(search_results: Dict[str, Any], max_snippets: int = 3) -> str:
    """
    Extrae snippets de los resultados de búsqueda para proporcionar contexto
    
    Args:
        search_results: Resultados de la búsqueda de search_web()
        max_snippets: Número máximo de snippets a extraer
        
    Returns:
        Texto con los snippets extraídos
    """
    snippets = []
    
    # Verificar si hay un error en los resultados
    if "error" in search_results and search_results["error"]:
        return f"Error al buscar información: {search_results['error']}"
    
    # Extraer datos según el tipo de búsqueda
    search_type = search_results.get("type", "search")
    results = search_results.get("results", {})
    
    if search_type == "search":
        # Búsqueda web estándar
        organic = results.get("organic", [])
        for item in organic[:max_snippets]:
            title = item.get("title", "Sin título")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            
            snippets.append(f"• {title}\n{snippet}\nFuente: {link}")
    
    elif search_type == "news":
        # Búsqueda de noticias
        news_results = results.get("news", [])
        for item in news_results[:max_snippets]:
            title = item.get("title", "Sin título")
            snippet = item.get("snippet", "")
            date = item.get("date", "")
            source = item.get("source", "")
            link = item.get("link", "")
            
            snippets.append(f"• {title} ({source}, {date})\n{snippet}\nFuente: {link}")
    
    elif search_type == "places":
        # Búsqueda de lugares
        places = results.get("places", [])
        for item in places[:max_snippets]:
            title = item.get("title", "Sin título")
            address = item.get("address", "")
            rating = item.get("rating", "")
            reviews = item.get("reviews", "")
            
            snippets.append(f"• {title}\nDirección: {address}\nCalificación: {rating} ({reviews} reseñas)")
    
    # Unir todos los snippets
    if snippets:
        return "\n\n".join(snippets)
    else:
        return "No se encontró información relevante para esta consulta."

async def search_for_context(
    query: str,
    language: str = "es",
    search_type: str = "search",
    max_snippets: int = 3
) -> str:
    """
    Realiza una búsqueda y formatea los resultados para proporcionar contexto
    
    Args:
        query: Consulta de búsqueda
        language: Idioma para la búsqueda
        search_type: Tipo de búsqueda
        max_snippets: Número máximo de snippets a incluir
        
    Returns:
        Texto con la información relevante para usar como contexto
    """
    # Determinar el país según el idioma
    country_mapping = {
        "es": "es",
        "ca": "es",  # Catalán -> España
        "en": "us",  # Inglés -> Estados Unidos
        "ar": "ae",  # Árabe -> Emiratos Árabes Unidos
    }
    country = country_mapping.get(language, "es")
    
    # Realizar la búsqueda
    search_results = await search_web(
        query=query,
        search_type=search_type,
        num_results=max_snippets + 2,  # Pedir algunos resultados extra
        country=country,
        language=language
    )
    
    # Extraer y formatear los snippets
    context = extract_snippets(search_results, max_snippets)
    
    # Añadir metadata
    timestamp = time.strftime("%Y-%m-%d")
    context += f"\n\nFuente: Búsqueda web realizada el {timestamp}."
    
    return context 