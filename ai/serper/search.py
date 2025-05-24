"""
Integración con Serper para búsquedas web.
Proporciona funcionalidades para realizar búsquedas en la web y formatear resultados.
"""
import os
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
import httpx

# Configurar logging
logger = logging.getLogger("mark.serper")

class SerperSearch:
    """
    Cliente para interactuar con la API de Serper para búsquedas web.
    Permite realizar búsquedas en Google y formatear los resultados.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializar el cliente de Serper.
        
        Args:
            api_key: Clave API de Serper (opcional, por defecto usa la de settings)
        """
        # Intentar importar configuración
        try:
            from core.config import settings
            self.settings = settings
            self.api_key = api_key or settings.SERPER_API_KEY
            self.base_url = settings.SERPER_ENDPOINT
        except ImportError:
            self.settings = None
            self.api_key = api_key or os.getenv("SERPER_API_KEY")
            self.base_url = os.getenv("SERPER_ENDPOINT", "https://serper.dev/api")
        
        # Validar API key
        if not self.api_key:
            logger.error("No se ha proporcionado una clave API para Serper")
            raise ValueError("Se requiere una clave API para Serper")
        
        # Configurar cliente HTTP
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info("Cliente de Serper inicializado")
    
    async def search(
        self,
        query: str,
        language: str = "es",
        country: str = "es",
        num_results: int = 5,
        include_knowledge_graph: bool = True,
        include_organic_results: bool = True,
        include_related_searches: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza una búsqueda en Google a través de la API de Serper.
        
        Args:
            query: Consulta de búsqueda
            language: Código de idioma (es, ca, en, ar)
            country: Código de país (es, us, etc.)
            num_results: Número de resultados a devolver
            include_knowledge_graph: Incluir gráfico de conocimiento
            include_organic_results: Incluir resultados orgánicos
            include_related_searches: Incluir búsquedas relacionadas
            
        Returns:
            Resultados de la búsqueda
        """
        # Mapear idiomas a códigos aceptados por Serper
        language_map = {
            "es": "es",
            "ca": "ca",
            "en": "en",
            "ar": "ar"
        }
        
        # Mapear países a códigos aceptados por Serper
        country_map = {
            "es": "es",
            "us": "us",
            "uk": "gb",
            "ca": "ca",
            "ar": "ar"
        }
        
        # Usar los códigos mapeados o los valores predeterminados
        lang = language_map.get(language, "es")
        country_code = country_map.get(country, "es")
        
        # Preparar la solicitud
        payload = {
            "q": query,
            "gl": country_code,
            "hl": lang,
            "num": num_results
        }
        
        logger.debug(f"Enviando búsqueda a Serper: {query}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    json=payload
                )
                
                # Verificar respuesta
                if response.status_code != 200:
                    logger.error(f"Error en la API de Serper: {response.status_code} - {response.text}")
                    raise Exception(f"Error al realizar búsqueda: {response.status_code}")
                
                # Procesar respuesta
                results = response.json()
                
                # Filtrar resultados según parámetros
                if not include_knowledge_graph and "knowledgeGraph" in results:
                    del results["knowledgeGraph"]
                    
                if not include_organic_results and "organic" in results:
                    del results["organic"]
                    
                if not include_related_searches and "relatedSearches" in results:
                    del results["relatedSearches"]
                
                logger.info(f"Búsqueda completada: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Error al comunicarse con la API de Serper: {e}")
            raise
    
    async def format_search_results(
        self,
        results: Dict[str, Any],
        max_organic_results: int = 3,
        include_snippets: bool = True,
        include_links: bool = True
    ) -> str:
        """
        Formatea los resultados de búsqueda en un texto legible.
        
        Args:
            results: Resultados de la búsqueda de Serper
            max_organic_results: Número máximo de resultados orgánicos a incluir
            include_snippets: Incluir fragmentos de texto de los resultados
            include_links: Incluir enlaces a los resultados
            
        Returns:
            Texto formateado con los resultados
        """
        formatted_text = "Resultados de la búsqueda:\n\n"
        
        # Formatear gráfico de conocimiento si existe
        if "knowledgeGraph" in results:
            kg = results["knowledgeGraph"]
            title = kg.get("title", "")
            description = kg.get("description", "")
            
            if title:
                formatted_text += f"📌 {title}\n"
            if description:
                formatted_text += f"{description}\n\n"
        
        # Formatear resultados orgánicos
        if "organic" in results and results["organic"]:
            formatted_text += "Resultados principales:\n"
            
            for i, result in enumerate(results["organic"][:max_organic_results]):
                title = result.get("title", "")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                
                formatted_text += f"{i+1}. {title}\n"
                
                if include_snippets and snippet:
                    formatted_text += f"   {snippet}\n"
                    
                if include_links and link:
                    formatted_text += f"   🔗 {link}\n"
                
                formatted_text += "\n"
        
        # Formatear búsquedas relacionadas
        if "relatedSearches" in results and results["relatedSearches"]:
            formatted_text += "Búsquedas relacionadas:\n"
            
            for i, search in enumerate(results["relatedSearches"][:5]):
                query = search.get("query", "")
                
                if query:
                    formatted_text += f"• {query}\n"
            
            formatted_text += "\n"
        
        return formatted_text
    
    async def search_and_format(
        self,
        query: str,
        language: str = "es",
        country: str = "es",
        num_results: int = 5,
        max_organic_results: int = 3
    ) -> str:
        """
        Realiza una búsqueda y formatea los resultados en un solo paso.
        
        Args:
            query: Consulta de búsqueda
            language: Código de idioma (es, ca, en, ar)
            country: Código de país (es, us, etc.)
            num_results: Número total de resultados a solicitar
            max_organic_results: Número máximo de resultados orgánicos a incluir
            
        Returns:
            Texto formateado con los resultados
        """
        try:
            results = await self.search(
                query=query,
                language=language,
                country=country,
                num_results=num_results
            )
            
            formatted_results = await self.format_search_results(
                results=results,
                max_organic_results=max_organic_results
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error al buscar y formatear resultados: {e}")
            return f"Lo siento, no pude completar la búsqueda: {str(e)}"

# Crear instancia global del cliente
serper_search = SerperSearch() 