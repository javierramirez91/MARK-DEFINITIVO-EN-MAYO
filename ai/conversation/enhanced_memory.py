"""
Sistema mejorado de memoria contextual para el asistente Mark.
Permite recordar detalles importantes de las conversaciones con los pacientes.
"""
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta

import asyncio
from core.config import settings

# Configurar logging
logger = logging.getLogger("mark.enhanced-memory")

try:
    # Updated imports for langchain > 0.1
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.embeddings import HuggingFaceEmbeddings
    VECTOR_DB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import vector store components. Vector memory disabled: {e}")
    VECTOR_DB_AVAILABLE = False

class PatientMemory:
    """
    Clase para almacenar y gestionar la memoria de un paciente específico.
    Incluye atributos personales, preferencias y datos estructurados.
    """
    def __init__(self, user_id: str):
        """Inicializar la memoria del paciente"""
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_updated = self.created_at
        
        # Atributos básicos
        self.personal_info = {
            "nombre": None,
            "edad": None,
            "género": None,
            "terapeuta_preferido": None,
            "idioma_preferido": None,
        }
        
        # Preferencias
        self.preferences = {
            "formato_comunicación": None,  # "texto", "audio", "video"
            "hora_preferida_citas": None,
            "días_preferidos": [],
        }
        
        # Historial médico y psicológico
        self.medical_history = {
            "condiciones_previas": [],
            "medicación_actual": [],
            "alergias": [],
        }
        
        # Temas importantes discutidos
        self.important_topics = []
        
        # Eventos clave en la terapia
        self.key_events = []
        
        # Objetivos terapéuticos
        self.therapeutic_goals = []
        
        # Técnicas que funcionan bien con este paciente
        self.effective_techniques = []
        
        # Conversaciones recientes
        self.recent_conversations = []
        
    def update_personal_info(self, key: str, value: Any) -> None:
        """Actualizar información personal"""
        if key in self.personal_info:
            self.personal_info[key] = value
            self.last_updated = datetime.now()
    
    def update_preference(self, key: str, value: Any) -> None:
        """Actualizar preferencias"""
        if key in self.preferences:
            self.preferences[key] = value
            self.last_updated = datetime.now()
    
    def add_medical_info(self, category: str, item: str) -> None:
        """Añadir información médica"""
        if category in self.medical_history and item not in self.medical_history[category]:
            self.medical_history[category].append(item)
            self.last_updated = datetime.now()
    
    def add_important_topic(self, topic: str, date: Optional[datetime] = None) -> None:
        """Añadir un tema importante discutido"""
        if date is None:
            date = datetime.now()
        
        self.important_topics.append({
            "topic": topic,
            "date": date,
            "last_mentioned": date
        })
        self.last_updated = datetime.now()
    
    def add_key_event(self, event: str, date: Optional[datetime] = None) -> None:
        """Añadir un evento clave en la terapia"""
        if date is None:
            date = datetime.now()
            
        self.key_events.append({
            "event": event,
            "date": date
        })
        self.last_updated = datetime.now()
    
    def add_therapeutic_goal(self, goal: str, priority: int = 1) -> None:
        """Añadir un objetivo terapéutico"""
        self.therapeutic_goals.append({
            "goal": goal,
            "priority": priority,
            "date_added": datetime.now(),
            "achieved": False
        })
        self.last_updated = datetime.now()
    
    def add_effective_technique(self, technique: str, effectiveness: int = 1) -> None:
        """Añadir una técnica efectiva"""
        self.effective_techniques.append({
            "technique": technique,
            "effectiveness": effectiveness,
            "date_added": datetime.now()
        })
        self.last_updated = datetime.now()
    
    def add_conversation(self, messages: List[Dict[str, Any]]) -> None:
        """Añadir una conversación reciente"""
        self.recent_conversations.append({
            "timestamp": datetime.now(),
            "messages": messages
        })
        
        # Mantener solo las últimas 10 conversaciones
        if len(self.recent_conversations) > 10:
            self.recent_conversations = self.recent_conversations[-10:]
            
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir la memoria a diccionario para almacenamiento"""
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "personal_info": self.personal_info,
            "preferences": self.preferences,
            "medical_history": self.medical_history,
            "important_topics": self.important_topics,
            "key_events": self.key_events,
            "therapeutic_goals": self.therapeutic_goals,
            "effective_techniques": self.effective_techniques,
            # No incluimos conversaciones para no hacer el objeto demasiado grande
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatientMemory':
        """Crear una memoria desde un diccionario"""
        memory = cls(data["user_id"])
        memory.created_at = datetime.fromisoformat(data["created_at"])
        memory.last_updated = datetime.fromisoformat(data["last_updated"])
        memory.personal_info = data["personal_info"]
        memory.preferences = data["preferences"]
        memory.medical_history = data["medical_history"]
        memory.important_topics = data["important_topics"]
        memory.key_events = data["key_events"]
        memory.therapeutic_goals = data["therapeutic_goals"]
        memory.effective_techniques = data["effective_techniques"]
        return memory


class EnhancedMemoryService:
    """
    Servicio para gestionar la memoria mejorada del asistente.
    Combina almacenamiento estructurado con retrieval semántico.
    """
    
    def __init__(self):
        """Inicializar el servicio de memoria mejorada"""
        self.patient_memories = {}
        self.vector_enabled = VECTOR_DB_AVAILABLE
        self.vector_stores = {}
        self.embeddings = None # Initialize embeddings attribute

        # Inicializar embeddings si están disponibles
        if self.vector_enabled:
            try:
                # Check for OpenAI API Key first
                openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if openai_api_key:
                    self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
                    logger.info("OpenAI Embeddings initialized for vector memory.")
                else:
                    # Fallback to HuggingFace embeddings
                    logger.info("OpenAI API Key not found, attempting HuggingFace Embeddings.")
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                    )
                    logger.info("HuggingFace Embeddings initialized for vector memory.")

            except Exception as e:
                logger.error(f"Error initializing embeddings: {e}. Vector memory disabled.")
                self.vector_enabled = False
        else:
             logger.warning("Required libraries not found. Vector memory features disabled.")
    
    async def get_patient_memory(self, user_id: str) -> PatientMemory:
        """
        Obtiene la memoria del paciente, cargándola si es necesario.
        
        Args:
            user_id: ID del usuario/paciente
            
        Returns:
            Objeto PatientMemory con la memoria del paciente
        """
        if user_id not in self.patient_memories:
            # Intentar cargar desde la base de datos
            try:
                # Assuming db_client is correctly set up elsewhere or imported
                from database.d1_client import db_client # Keep import local if not always needed
                memory_data = await db_client.get_patient_memory(user_id)
                
                if memory_data:
                    self.patient_memories[user_id] = PatientMemory.from_dict(memory_data)
                    logger.info(f"Loaded memory for patient {user_id} from DB.")
                else:
                    # Crear nueva memoria si no existe
                    logger.info(f"No existing memory found for patient {user_id}. Creating new memory.")
                    self.patient_memories[user_id] = PatientMemory(user_id)
            except ImportError:
                 logger.error("Could not import db_client. Cannot load patient memory from DB.")
                 self.patient_memories[user_id] = PatientMemory(user_id) # Create new memory as fallback
            except Exception as e:
                logger.error(f"Error loading memory for patient {user_id}: {e}. Creating new memory.")
                # Crear nueva memoria si hay error
                self.patient_memories[user_id] = PatientMemory(user_id)
        
        return self.patient_memories[user_id]
    
    async def save_patient_memory(self, user_id: str) -> bool:
        """
        Guarda la memoria del paciente en la base de datos.
        
        Args:
            user_id: ID del usuario/paciente
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if user_id not in self.patient_memories:
             logger.warning(f"Attempted to save memory for non-loaded user_id: {user_id}")
             return False

        try:
            # Assuming db_client is correctly set up elsewhere or imported
            from database.d1_client import db_client # Keep import local if not always needed
            memory_dict = self.patient_memories[user_id].to_dict()
            success = await db_client.save_patient_memory(user_id, memory_dict)
            if success:
                 logger.info(f"Successfully saved memory for patient {user_id} to DB.")
                 return True
            else:
                 logger.error(f"Failed to save memory for patient {user_id} to DB.")
                 return False
        except ImportError:
             logger.error("Could not import db_client. Cannot save patient memory to DB.")
             return False
        except Exception as e:
            logger.error(f"Error saving memory for patient {user_id}: {e}")
            return False
    
    async def extract_entities_from_message(self, message: str) -> Dict[str, Any]:
        """
        Extrae entidades relevantes (nombre, edad, etc.) de un mensaje.
        (Implementación simplificada, podría usar un LLM o NER)
        """
        entities = {}
        # Ejemplo básico: buscar nombres (simplificado)
        # En un caso real, usaríamos modelos de NER o un LLM con un prompt específico
        # para extraer información estructurada de manera más robusta.
        
        # Expresión regular simple para nombres (solo como ejemplo)
        # name_match = re.search(r"(me llamo|soy)\s+([A-Z][a-záéíóúñ]+)\b", message, re.IGNORECASE)
        # if name_match:
        #     entities['nombre'] = name_match.group(2)

        # Ejemplo: buscar edad (muy simplificado)
        # age_match = re.search(r"tengo\s+(\d+)\s+años", message, re.IGNORECASE)
        # if age_match:
        #     try:
        #         entities['edad'] = int(age_match.group(1))
        #     except ValueError:
        #         pass # Ignore if conversion fails

        logger.debug(f"Extracted entities (simplified): {entities}")
        return entities # Devolver diccionario vacío por ahora

    async def update_memory_from_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Actualiza la memoria estructurada del paciente basándose en la conversación.
        Extrae entidades e información relevante.
        """
        memory = await self.get_patient_memory(user_id)
        logger.info(f"Updating structured memory for user {user_id} from conversation.")

        # Extraer texto completo de la conversación
        conversation_text = "\n".join([msg['content'] for msg in messages])

        # TODO: Implementar extracción de entidades más avanzada usando LLM
        # Por ahora, solo extraemos de los mensajes individuales como ejemplo
        for message in messages:
            if message['role'] == 'user':
                entities = await self.extract_entities_from_message(message['content'])
                for key, value in entities.items():
                    if key in memory.personal_info and memory.personal_info[key] is None:
                        logger.info(f"Updating personal info '{key}' for user {user_id}")
                        memory.update_personal_info(key, value)
                    # Podríamos añadir lógica para actualizar otras secciones (preferencias, etc.)

        # TODO: Implementar lógica para identificar y añadir temas importantes,
        #       eventos clave, objetivos, etc., usando análisis de conversación con LLM.
        # Ejemplo: Si se detecta "quiero programar una cita", podríamos actualizar
        # memory.add_key_event("Solicitud de cita")

        # Actualizar el vector store si está habilitado
        if self.vector_enabled:
            await self.update_vector_store(user_id, messages)

        # Guardar cambios en la memoria estructurada
        await self.save_patient_memory(user_id)

    async def update_vector_store(self, user_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Actualiza el almacén vectorial con los mensajes de la conversación.
        """
        if not self.vector_enabled or not self.embeddings:
            logger.debug("Vector store update skipped: vector features or embeddings disabled.")
            return

        logger.info(f"Updating vector store for user {user_id}.")
        try:
            # Crear o obtener el vector store para el usuario
            if user_id not in self.vector_stores:
                # TODO: Consider persistence for ChromaDB
                # persist_directory = f"./vector_store/{user_id}" # Example path
                # os.makedirs(persist_directory, exist_ok=True)
                # self.vector_stores[user_id] = Chroma(
                #     persist_directory=persist_directory,
                #     embedding_function=self.embeddings
                # )
                # Using in-memory Chroma for now
                self.vector_stores[user_id] = Chroma(embedding_function=self.embeddings)
                logger.info(f"Created new in-memory vector store for user {user_id}")

            vector_store = self.vector_stores[user_id]

            # Preparar documentos para añadir
            documents_to_add = []
            for msg in messages:
                doc = Document(
                    page_content=msg['content'],
                    metadata={
                        "role": msg['role'],
                        "timestamp": datetime.now().isoformat(), # Use current time or message time if available
                        "user_id": user_id,
                        # Add conversation_id if available
                    }
                )
                documents_to_add.append(doc)

            if documents_to_add:
                # Usar text splitter para trocear mensajes largos si es necesario
                # text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                # split_docs = text_splitter.split_documents(documents_to_add)

                # Add documents to the vector store
                # Chroma's add_documents is synchronous in older versions, check library specifics
                # If Chroma API is async:
                # await vector_store.aadd_documents(documents_to_add)
                # If Chroma API is sync:
                try:
                    vector_store.add_documents(documents_to_add) # Assuming sync add_documents
                    logger.info(f"Added {len(documents_to_add)} documents to vector store for user {user_id}.")
                    # TODO: Add persistence call if using persistent Chroma
                    # vector_store.persist()
                except Exception as e:
                     logger.error(f"Error adding documents to Chroma (sync): {e}")


        except Exception as e:
            logger.error(f"Failed to update vector store for user {user_id}: {e}")


    async def query_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca en el almacén vectorial memorias relevantes para una consulta.
        """
        if not self.vector_enabled or user_id not in self.vector_stores:
            logger.debug("Vector store query skipped: vector features disabled or store not found.")
            return []

        logger.info(f"Querying vector store for user {user_id} with query: '{query[:50]}...'")
        try:
            vector_store = self.vector_stores[user_id]
            # Perform similarity search
            # Assuming Chroma API is sync:
            results = vector_store.similarity_search_with_score(query, k=limit)
            # If Chroma API is async:
            # results = await vector_store.asimilarity_search_with_score(query, k=limit)

            relevant_memories = []
            for doc, score in results:
                relevant_memories.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })

            logger.info(f"Found {len(relevant_memories)} relevant memories for user {user_id}.")
            return relevant_memories

        except Exception as e:
            logger.error(f"Error querying vector store for user {user_id}: {e}")
            return []

    async def get_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Genera un resumen conciso de la memoria del paciente.
        Combina información estructurada y recuerdos semánticos clave.
        """
        memory = await self.get_patient_memory(user_id)
        summary = {}

        # Información personal clave
        summary["personal_info"] = {k: v for k, v in memory.personal_info.items() if v is not None}
        summary["preferences"] = {k: v for k, v in memory.preferences.items() if v is not None}

        # Temas importantes recientes
        recent_topics = sorted(
            [t for t in memory.important_topics if isinstance(t, dict) and 'date' in t],
            key=lambda x: x.get('last_mentioned', x.get('date')),
            reverse=True
        )
        summary["recent_topics"] = [t['topic'] for t in recent_topics[:3]] # Top 3

        # Objetivos activos
        summary["active_goals"] = [g['goal'] for g in memory.therapeutic_goals if isinstance(g, dict) and not g.get('achieved')]

        # Podríamos añadir aquí resultados de query_relevant_memories si fuera necesario
        # para el contexto inmediato, pero el objetivo es un resumen general.

        logger.info(f"Generated memory summary for user {user_id}")
        return summary

# Instancia global del servicio de memoria
enhanced_memory_service = EnhancedMemoryService() 