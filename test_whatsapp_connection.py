#!/usr/bin/env python3
"""
Script para probar la conexión de WhatsApp con Mark Assistant
"""
import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_whatsapp_connection():
    """Prueba la conexión con WhatsApp Business API"""
    
    # Configuración desde variables de entorno
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not token or not phone_number_id:
        print("❌ Error: WHATSAPP_TOKEN y WHATSAPP_PHONE_NUMBER_ID deben estar configurados")
        print("Configúralos en tu archivo .env o en las variables de entorno de Render")
        return False
    
    # URL de la API de WhatsApp
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Mensaje de prueba (cambia este número por tu número de WhatsApp)
    test_phone = input("Introduce tu número de WhatsApp (formato: +34XXXXXXXXX): ")
    
    payload = {
        "messaging_product": "whatsapp",
        "to": test_phone,
        "type": "text",
        "text": {
            "body": "¡Hola! Soy Mark, tu asistente de salud mental. Esta es una prueba de conexión. ¿Cómo te sientes hoy?"
        }
    }
    
    try:
        print("📤 Enviando mensaje de prueba...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("✅ ¡Mensaje enviado correctamente!")
            print(f"Respuesta: {response.json()}")
            return True
        else:
            print(f"❌ Error al enviar mensaje: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_mark_api():
    """Prueba la conexión con la API de Mark"""
    
    # URL de tu API en Render
    api_url = "https://mark-api.onrender.com"
    
    try:
        print("🔍 Probando conexión con Mark API...")
        response = requests.get(f"{api_url}/health")
        
        if response.status_code == 200:
            print("✅ Mark API está funcionando correctamente!")
            return True
        else:
            print(f"❌ Error en Mark API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando con Mark API: {e}")
        return False

def create_test_patient():
    """Crea un paciente de prueba"""
    
    api_url = "https://mark-api.onrender.com"
    
    patient_data = {
        "name": "Usuario de Prueba",
        "phone": input("Introduce el número de teléfono del paciente (formato: +34XXXXXXXXX): "),
        "email": "prueba@example.com",
        "language": "es",
        "metadata": {
            "source": "test_script",
            "created_by": "admin"
        }
    }
    
    try:
        print("👤 Creando paciente de prueba...")
        response = requests.post(f"{api_url}/api/patients", json=patient_data)
        
        if response.status_code in [200, 201]:
            print("✅ Paciente creado correctamente!")
            print(f"Datos: {response.json()}")
            return True
        else:
            print(f"❌ Error creando paciente: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 MARK ASSISTANT - PRUEBA DE CONEXIÓN")
    print("=" * 50)
    
    # Prueba 1: API de Mark
    print("\n1️⃣ Probando Mark API...")
    api_ok = test_mark_api()
    
    # Prueba 2: WhatsApp
    print("\n2️⃣ Probando WhatsApp...")
    whatsapp_ok = test_whatsapp_connection()
    
    # Prueba 3: Crear paciente (opcional)
    if api_ok:
        print("\n3️⃣ ¿Quieres crear un paciente de prueba? (s/n): ", end="")
        if input().lower() == 's':
            create_test_patient()
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    print(f"Mark API: {'✅ OK' if api_ok else '❌ ERROR'}")
    print(f"WhatsApp: {'✅ OK' if whatsapp_ok else '❌ ERROR'}")
    
    if api_ok and whatsapp_ok:
        print("\n🎉 ¡Todo está funcionando! Ya puedes usar Mark Assistant.")
        print("\n📱 Para empezar a chatear:")
        print("1. Envía un mensaje a tu número de WhatsApp Business")
        print("2. Mark responderá automáticamente")
        print("3. Puedes monitorear las conversaciones desde el panel de admin")
    else:
        print("\n⚠️ Hay problemas de configuración. Revisa las variables de entorno.") 