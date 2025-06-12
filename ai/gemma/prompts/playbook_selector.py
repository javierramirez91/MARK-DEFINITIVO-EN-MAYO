"""
Selector de playbooks para el asistente Mark con Gemma.
Determina qué playbook utilizar en base al contexto de la conversación.
"""

import enum
from typing import Dict, Any, List, Optional
import re
from core.config import logger

class PlaybookType(enum.Enum):
    """Tipos de playbooks disponibles para el asistente Mark"""
    
    GENERAL = "general"
    INTAKE = "intake"
    SCHEDULING = "scheduling"
    PAYMENT = "payment"
    CRISIS = "crisis"
    
    @classmethod
    def from_string(cls, value: str) -> "PlaybookType":
        """
        Convierte un string a un valor de PlaybookType
        
        Args:
            value: String a convertir
            
        Returns:
            Valor de PlaybookType correspondiente, o GENERAL si no hay coincidencia
        """
        try:
            return cls(value.lower())
        except:
            return cls.GENERAL

def select_playbook(user_message: str, conversation_history=None):
    """
    Selecciona el playbook adecuado según el mensaje del usuario.
    Devuelve (playbook_type, system_prompt)
    """
    from ai.gemma.prompts.playbook1 import SYSTEM_PROMPT as SYSTEM_PROMPT_1
    from ai.claude.prompts.playbook2 import system_prompt as SYSTEM_PROMPT_2
    from ai.claude.prompts.playbook3 import system_prompt as SYSTEM_PROMPT_3
    from ai.claude.prompts.playbook4 import system_prompt as SYSTEM_PROMPT_4

    msg = user_message.lower().strip()
    # Playbook 2: Crisis/Urgencia
    if any(word in msg for word in ["urgencia", "suicidio", "emergencia", "crisis", "ayuda urgente", "dina", "psicóloga de guardia"]):
        logger.info(f"Mensaje del usuario: '{user_message}'. Playbook seleccionado: 2 (crisis)")
        return 2, SYSTEM_PROMPT_2
    # Playbook 3: Citas/Pagos
    if any(word in msg for word in ["cita", "terapia", "hora", "psicólogo", "psicologa", "pagar", "pago", "reserva", "agenda", "turno"]):
        logger.info(f"Mensaje del usuario: '{user_message}'. Playbook seleccionado: 3 (citas/pagos)")
        return 3, SYSTEM_PROMPT_3
    # Playbook 4: Seguridad
    if any(word in msg for word in ["seguridad", "privacidad", "datos", "protección", "rgpd", "gdpr", "confidencial"]):
        logger.info(f"Mensaje del usuario: '{user_message}'. Playbook seleccionado: 4 (seguridad)")
        return 4, SYSTEM_PROMPT_4
    # Playbook 1: Saludo o general
    if re.match(r"^(hola|hello|bon dia|buenos días|hi|hey|qué tal|buenas|salut|السلام|مرحبا)", msg):
        logger.info(f"Mensaje del usuario: '{user_message}'. Playbook seleccionado: 1 (saludo/identidad)")
        return 1, SYSTEM_PROMPT_1
    # Por defecto, playbook 1
    logger.info(f"Mensaje del usuario: '{user_message}'. Playbook seleccionado: 1 (default)")
    return 1, SYSTEM_PROMPT_1

def _contains_crisis_keywords(messages: List[Dict[str, str]]) -> bool:
    """
    Verifica si los mensajes contienen palabras clave relacionadas con crisis
    
    Args:
        messages: Lista de mensajes de la conversación
        
    Returns:
        True si se detectan palabras clave de crisis, False en caso contrario
    """
    crisis_keywords = [
        "suicid", "matar", "morir", "muerte", "acabar con todo",
        "no aguanto más", "no puedo seguir", "quiero desaparecer",
        "emergency", "emergencia", "crisis", "urgente", "ayuda inmediata",
        "daño", "peligro", "riesgo", "lastimar", "autolesion"
    ]
    
    # Buscar palabras clave en los últimos 3 mensajes del usuario
    user_messages = [msg.get("content", "").lower() for msg in messages[-5:] if msg.get("role") == "user"]
    
    for message in user_messages:
        for keyword in crisis_keywords:
            if keyword in message:
                return True
    
    return False

def _is_scheduling_conversation(messages: List[Dict[str, str]]) -> bool:
    """
    Verifica si la conversación está relacionada con la programación de citas
    
    Args:
        messages: Lista de mensajes de la conversación
        
    Returns:
        True si se detecta intención de programación, False en caso contrario
    """
    scheduling_keywords = [
        "cita", "reservar", "programar", "calendario", "disponibilidad", 
        "horario", "cuándo", "fecha", "hora", "día", "semana",
        "appointment", "schedule", "booking", "availability", "calendar"
    ]
    
    # Buscar palabras clave en los últimos 3 mensajes del usuario
    user_messages = [msg.get("content", "").lower() for msg in messages[-3:] if msg.get("role") == "user"]
    
    for message in user_messages:
        keyword_count = sum(1 for keyword in scheduling_keywords if keyword in message)
        if keyword_count >= 2:  # Requerir al menos 2 coincidencias para mayor precisión
            return True
    
    return False

def _is_payment_conversation(messages: List[Dict[str, str]]) -> bool:
    """
    Verifica si la conversación está relacionada con pagos o tarifas
    
    Args:
        messages: Lista de mensajes de la conversación
        
    Returns:
        True si se detecta intención de pago, False en caso contrario
    """
    payment_keywords = [
        "pago", "tarifa", "precio", "costo", "cuánto cuesta", "factura",
        "payment", "fee", "price", "cost", "invoice", "how much", "pay"
    ]
    
    # Buscar palabras clave en los últimos 3 mensajes del usuario
    user_messages = [msg.get("content", "").lower() for msg in messages[-3:] if msg.get("role") == "user"]
    
    for message in user_messages:
        for keyword in payment_keywords:
            if keyword in message:
                return True
    
    return False

def _is_intake_conversation(messages: List[Dict[str, str]], user_context: Dict[str, Any]) -> bool:
    """
    Verifica si la conversación está relacionada con intake inicial
    
    Args:
        messages: Lista de mensajes de la conversación
        user_context: Contexto del usuario
        
    Returns:
        True si se detecta intención de intake, False en caso contrario
    """
    # Si es un nuevo usuario o tiene pocas interacciones, priorizar intake
    message_count = len(messages)
    is_new_user = user_context.get("is_new", True)
    has_completed_intake = user_context.get("completed_intake", False)
    
    if (is_new_user or message_count < 10) and not has_completed_intake:
        return True
    
    # Buscar palabras clave relacionadas con intake
    intake_keywords = [
        "primera vez", "nuevo paciente", "consulta inicial", "empezar terapia",
        "first time", "new patient", "initial consultation", "start therapy",
        "comenzar", "iniciar", "información personal", "datos personales"
    ]
    
    # Buscar palabras clave en los últimos 3 mensajes del usuario
    user_messages = [msg.get("content", "").lower() for msg in messages[-3:] if msg.get("role") == "user"]
    
    for message in user_messages:
        for keyword in intake_keywords:
            if keyword in message:
                return True
    
    return False 