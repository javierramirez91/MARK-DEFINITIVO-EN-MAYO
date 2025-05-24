"""
Pruebas para el grafo de conversación
"""
import pytest
import asyncio
from typing import Dict, Any, List
from ai.langgraph.playbook_graph import (
    conversation_graph,
    ConversationState,
    detect_language,
    select_playbook,
    check_web_search_needed,
    perform_web_search,
    generate_response,
)

# Pruebas para la función detect_language
@pytest.mark.asyncio
async def test_detect_language_empty_messages():
    """Prueba la detección de idioma con mensajes vacíos"""
    state = ConversationState(messages=[])
    result = await detect_language(state)
    assert "language" in result
    assert result["language"] == "es"  # Idioma por defecto

@pytest.mark.asyncio
async def test_detect_language_spanish():
    """Prueba la detección de idioma con un mensaje en español"""
    state = ConversationState(
        messages=[{"role": "user", "content": "Hola, ¿cómo estás?"}]
    )
    result = await detect_language(state)
    assert "language" in result
    assert result["language"] == "es"

# Pruebas para la función select_playbook
@pytest.mark.asyncio
async def test_select_playbook_empty_messages():
    """Prueba la selección de PlayBook con mensajes vacíos"""
    state = ConversationState(messages=[])
    result = await select_playbook(state)
    assert "current_playbook" in result
    assert result["current_playbook"] == "general"  # PlayBook por defecto

@pytest.mark.asyncio
async def test_select_playbook_appointment():
    """Prueba la selección de PlayBook con un mensaje sobre citas"""
    state = ConversationState(
        messages=[{"role": "user", "content": "Quiero programar una cita para la próxima semana"}]
    )
    result = await select_playbook(state)
    assert "current_playbook" in result
    assert result["current_playbook"] == "appointment"
    assert "appointment_requested" in result
    assert result["appointment_requested"] is True

# Pruebas para la función check_web_search_needed
@pytest.mark.asyncio
async def test_check_web_search_needed_empty_messages():
    """Prueba la verificación de necesidad de búsqueda web con mensajes vacíos"""
    state = ConversationState(messages=[])
    result = await check_web_search_needed(state)
    assert "needs_web_search" in result
    assert result["needs_web_search"] is False

@pytest.mark.asyncio
async def test_check_web_search_needed_general_question():
    """Prueba la verificación de necesidad de búsqueda web con una pregunta general"""
    state = ConversationState(
        messages=[{"role": "user", "content": "¿Cómo puedo manejar la ansiedad?"}]
    )
    result = await check_web_search_needed(state)
    assert "needs_web_search" in result
    # El resultado puede variar dependiendo de la implementación

# Pruebas para el grafo completo
@pytest.mark.asyncio
async def test_conversation_graph_simple_message():
    """Prueba el grafo de conversación con un mensaje simple"""
    initial_state = ConversationState(
        messages=[{"role": "user", "content": "Hola, ¿cómo estás?"}]
    )
    result = await conversation_graph.ainvoke(initial_state)
    
    # Verificar que el resultado contiene los campos esperados
    assert hasattr(result, "messages")
    assert hasattr(result, "language")
    assert hasattr(result, "current_playbook")
    
    # Verificar que hay al menos un mensaje de respuesta
    assert len(result.messages) > 1
    assert result.messages[-1]["role"] == "assistant"
    assert result.messages[-1]["content"] != ""

@pytest.mark.asyncio
async def test_conversation_graph_appointment_request():
    """Prueba el grafo de conversación con una solicitud de cita"""
    initial_state = ConversationState(
        messages=[{"role": "user", "content": "Quiero programar una cita para la próxima semana"}]
    )
    result = await conversation_graph.ainvoke(initial_state)
    
    # Verificar que el PlayBook seleccionado es el correcto
    assert result.current_playbook == "appointment"
    assert result.appointment_requested is True
    
    # Verificar que hay una respuesta relacionada con citas
    assert len(result.messages) > 1
    assert result.messages[-1]["role"] == "assistant"
    assert result.messages[-1]["content"] != ""

# Pruebas de integración con múltiples mensajes
@pytest.mark.asyncio
async def test_conversation_graph_multiple_messages():
    """Prueba el grafo de conversación con múltiples mensajes"""
    messages = [
        {"role": "user", "content": "Hola, ¿cómo estás?"},
        {"role": "assistant", "content": "Estoy bien, ¿en qué puedo ayudarte?"},
        {"role": "user", "content": "Tengo problemas para dormir"}
    ]
    
    initial_state = ConversationState(messages=messages)
    result = await conversation_graph.ainvoke(initial_state)
    
    # Verificar que el resultado contiene los mensajes originales más la respuesta
    assert len(result.messages) == len(messages) + 1
    assert result.messages[-1]["role"] == "assistant"
    assert result.messages[-1]["content"] != "" 