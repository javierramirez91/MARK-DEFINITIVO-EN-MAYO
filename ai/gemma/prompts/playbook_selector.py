"""
Selector de playbooks para el asistente Mark con Gemma.
Determina qué playbook utilizar en base al contexto de la conversación.
"""

import enum
from typing import Dict, Any, List, Optional

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

def select_playbook(conversation_context: Dict[str, Any]) -> PlaybookType:
    """
    Selecciona el playbook más adecuado según el contexto de la conversación
    
    Args:
        conversation_context: Contexto de la conversación, incluyendo historial y metadatos
        
    Returns:
        Tipo de playbook a utilizar
    """
    # Extraer información relevante del contexto
    messages = conversation_context.get("messages", [])
    metadata = conversation_context.get("metadata", {})
    user_context = conversation_context.get("user", {})
    
    # Verificar flags de emergencia
    if _contains_crisis_keywords(messages):
        return PlaybookType.CRISIS
    
    # Verificar el propósito explícito si está definido
    explicit_purpose = metadata.get("purpose")
    if explicit_purpose:
        return PlaybookType.from_string(explicit_purpose)
    
    # Analizar el contexto para determinar el playbook
    if _is_scheduling_conversation(messages):
        return PlaybookType.SCHEDULING
    
    if _is_payment_conversation(messages):
        return PlaybookType.PAYMENT
    
    if _is_intake_conversation(messages, user_context):
        return PlaybookType.INTAKE
    
    # Por defecto, usar el playbook general
    return PlaybookType.GENERAL

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