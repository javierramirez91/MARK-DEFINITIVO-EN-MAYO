#!/usr/bin/env python3
"""
Script para crear un paciente directamente via API de Mark
"""
import requests
import json

def create_patient_via_api():
    """Crea un paciente directamente via API"""
    
    # URL de tu API en Render
    api_url = "https://mark-api.onrender.com"
    
    print("🤖 CREAR PACIENTE VIA API")
    print("=" * 40)
    
    # Solicitar datos del paciente
    name = input("Nombre del paciente: ")
    phone = input("Teléfono (formato: +34XXXXXXXXX): ")
    email = input("Email (opcional, presiona Enter para omitir): ") or None
    language = input("Idioma (es/en/ca/ar) [es]: ") or "es"
    
    # Datos del paciente
    patient_data = {
        "name": name,
        "phone": phone,
        "language": language,
        "metadata": {
            "source": "admin_script",
            "created_by": "admin"
        }
    }
    
    if email:
        patient_data["email"] = email
    
    try:
        print("\n📤 Enviando datos a la API...")
        print(f"URL: {api_url}/api/patients")
        print(f"Datos: {json.dumps(patient_data, indent=2)}")
        
        response = requests.post(f"{api_url}/api/patients", json=patient_data)
        
        print(f"\n📊 Respuesta del servidor:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            print("✅ ¡Paciente creado correctamente!")
            try:
                result = response.json()
                print(f"Respuesta: {json.dumps(result, indent=2)}")
            except:
                print(f"Respuesta (texto): {response.text}")
            return True
        else:
            print(f"❌ Error creando paciente: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_api_health():
    """Prueba si la API está funcionando"""
    api_url = "https://mark-api.onrender.com"
    
    try:
        print("🔍 Probando conexión con Mark API...")
        response = requests.get(f"{api_url}/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Mark API está funcionando correctamente!")
            return True
        else:
            print(f"❌ Error en Mark API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando con Mark API: {e}")
        return False

def list_existing_patients():
    """Lista los pacientes existentes"""
    api_url = "https://mark-api.onrender.com"
    
    try:
        print("📋 Obteniendo lista de pacientes...")
        response = requests.get(f"{api_url}/api/patients", timeout=10)
        
        if response.status_code == 200:
            try:
                patients = response.json()
                print(f"✅ Pacientes encontrados: {len(patients)}")
                for i, patient in enumerate(patients, 1):
                    print(f"{i}. {patient.get('name', 'Sin nombre')} - {patient.get('phone', 'Sin teléfono')}")
                return True
            except:
                print(f"Respuesta (texto): {response.text}")
                return False
        else:
            print(f"❌ Error obteniendo pacientes: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 MARK ASSISTANT - GESTIÓN DE PACIENTES")
    print("=" * 50)
    
    # Prueba 1: Verificar API
    print("\n1️⃣ Verificando API...")
    api_ok = test_api_health()
    
    if not api_ok:
        print("\n❌ La API no está funcionando. Verifica que Mark esté desplegado correctamente.")
        exit(1)
    
    # Prueba 2: Listar pacientes existentes
    print("\n2️⃣ Pacientes existentes:")
    list_existing_patients()
    
    # Prueba 3: Crear nuevo paciente
    print("\n3️⃣ Crear nuevo paciente:")
    create_patient_via_api()
    
    # Prueba 4: Listar pacientes después de crear
    print("\n4️⃣ Pacientes después de crear:")
    list_existing_patients()
    
    print("\n" + "=" * 50)
    print("✅ Proceso completado!")
    print("\n📱 Próximos pasos:")
    print("1. Configura WhatsApp Business API")
    print("2. Envía un mensaje al número de WhatsApp configurado")
    print("3. Mark responderá automáticamente") 