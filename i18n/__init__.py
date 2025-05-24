"""
Módulo de internacionalización para el asistente Mark.
Proporciona mensajes en diferentes idiomas.
"""

from i18n.messages import (
    get_message, 
    validate_messages,
    update_message,
    add_language,
    translate_missing_keys,
    save_messages_to_json,
    load_messages_from_json
)

__all__ = [
    "get_message", 
    "validate_messages",
    "update_message",
    "add_language",
    "translate_missing_keys",
    "save_messages_to_json",
    "load_messages_from_json"
] 