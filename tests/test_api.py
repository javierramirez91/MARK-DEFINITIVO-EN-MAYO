"""
Pruebas automatizadas para la API del asistente Mark.
"""
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Importar la aplicación
from main import app
from backend.api_server import process_message, determine_playbook
from services.whatsapp import verify_twilio_signature, send_whatsapp_message
from database.d1_client import get_patient_by_phone
from i18n.messages import get_message

# Cliente de prueba
client = TestClient(app)

# Configuración de pruebas
@pytest.fixture
def mock_claude_response():
    """Mock para respuestas de Claude"""
    with patch("ai.claude.client.generate_claude_response") as mock:
        mock.return_value = "Esta es una respuesta de prueba de Claude."
        yield mock

@pytest.fixture
def mock_twilio_client():
    """Mock para el cliente de Twilio"""
    with patch("services.whatsapp.get_twilio_client") as mock:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(sid="SM123456", status="queued")
        mock.return_value = mock_client
        yield mock

@pytest.fixture
def mock_db_client():
    """Mock para el cliente de base de datos"""
    with patch("database.d1_client.execute_query") as mock:
        mock.return_value = {"success": True, "results": []}
        yield mock

# Pruebas de endpoints
def test_health_endpoint():
    """Prueba del endpoint de salud"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_message_endpoint(mock_claude_response):
    """Prueba del endpoint de mensajes"""
    test_message = {
        "message": "Hola, ¿cómo estás?",
        "session_id": None,
        "user_id": "test_user",
        "phone": "+34600000000",
        "context": None
    }
    
    response = client.post("/api/message", json=test_message)
    assert response.status_code == 200
    assert "message" in response.json()
    assert "session_id" in response.json()
    assert "detected_language" in response.json()

def test_whatsapp_webhook(mock_twilio_client):
    """Prueba del webhook de WhatsApp"""
    # Datos de prueba para el webhook
    webhook_data = {
        "SmsMessageSid": "SM123456",
        "NumMedia": "0",
        "SmsSid": "SM123456",
        "SmsStatus": "received",
        "Body": "Hola, quiero una cita",
        "To": "whatsapp:+14155238886",
        "NumSegments": "1",
        "MessageSid": "SM123456",
        "AccountSid": "AC123456",
        "From": "whatsapp:+34600000000",
        "ApiVersion": "2010-04-01"
    }
    
    # Simular la firma de Twilio
    with patch("services.whatsapp.verify_twilio_signature", return_value=True):
        response = client.post(
            "/api/whatsapp/webhook",
            json=webhook_data,
            headers={"X-Twilio-Signature": "fake_signature"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "processing"

# Pruebas de funciones
def test_determine_playbook():
    """Prueba la función de determinación de playbook"""
    # Playbook de crisis
    assert determine_playbook("Estoy en crisis y necesito ayuda urgente", "1") == "2"
    assert determine_playbook("No puedo más, necesito hablar con Dina", "1") == "2"
    
    # Playbook de citas
    assert determine_playbook("Quiero pedir una cita para la próxima semana", "1") == "3"
    assert determine_playbook("¿Cuánto cuesta una sesión?", "1") == "3"
    
    # Playbook de seguridad
    assert determine_playbook("¿Cómo protegéis mis datos personales?", "1") == "4"
    
    # Mantener playbook actual si no hay coincidencias
    assert determine_playbook("Hola, ¿cómo estás?", "1") == "1"

@pytest.mark.asyncio
async def test_process_message(mock_claude_response):
    """Prueba la función de procesamiento de mensajes"""
    message_request = MagicMock()
    message_request.message = "Hola, ¿cómo estás?"
    message_request.session_id = None
    message_request.user_id = "test_user"
    message_request.phone = None
    message_request.context = None
    
    # Mock para detect_language
    with patch("ai.claude.client.detect_language", return_value="es"):
        # Mock para handle_conversation
        with patch("backend.api_server.handle_conversation") as mock_handle:
            mock_handle.return_value = {
                "response": "Hola, soy Mark. ¿En qué puedo ayudarte?",
                "session_data": {
                    "language": "es",
                    "messages": [],
                    "playbook_id": "1"
                }
            }
            
            response = await process_message(message_request)
            
            assert response.message == "Hola, soy Mark. ¿En qué puedo ayudarte?"
            assert response.detected_language == "es"
            assert response.playbook_id == "1"

def test_send_whatsapp_message(mock_twilio_client):
    """Prueba la función de envío de mensajes de WhatsApp"""
    result = send_whatsapp_message(
        to="+34600000000",
        message="Este es un mensaje de prueba"
    )
    
    assert result["success"] is True
    assert "message_sid" in result
    assert result["message_sid"] == "SM123456"

@pytest.mark.asyncio
async def test_get_patient_by_phone(mock_db_client):
    """Prueba la función de búsqueda de pacientes por teléfono"""
    # Configurar el mock para devolver un paciente
    mock_db_client.return_value = {
        "success": True,
        "results": [{
            "id": "patient_123",
            "name": "Juan Pérez",
            "phone": "+34600000000",
            "email": "juan@example.com",
            "language": "es"
        }]
    }
    
    patient = await get_patient_by_phone("+34600000000")
    
    assert patient is not None
    assert patient["name"] == "Juan Pérez"
    assert patient["phone"] == "+34600000000"

def test_get_message():
    """Prueba la función de obtención de mensajes"""
    # Mock de mensajes
    messages = {
        "es": {
            "welcome": "Bienvenido al Centre de Psicologia Jaume I"
        },
        "en": {
            "welcome": "Welcome to Centre de Psicologia Jaume I"
        }
    }
    
    with patch("i18n.messages._messages", messages):
        # Probar mensaje en español
        assert get_message("welcome", "es") == "Bienvenido al Centre de Psicologia Jaume I"
        
        # Probar mensaje en inglés
        assert get_message("welcome", "en") == "Welcome to Centre de Psicologia Jaume I"
        
        # Probar fallback a español si el idioma no existe
        assert get_message("welcome", "fr") == "Bienvenido al Centre de Psicologia Jaume I"
        
        # Probar mensaje que no existe
        assert get_message("nonexistent", "es") == "nonexistent"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 