#!/usr/bin/env python3
"""
Script para crear un paciente via el panel de administración de Mark
"""
import requests
import json

def create_patient_via_admin():
    """Crea un paciente via el panel de administración"""
    
    # URL del panel de administración en Render
    admin_url = "https://mark-admin.onrender.com"
    
    print("🤖 CREAR PACIENTE VIA PANEL DE ADMINISTRACIÓN")
    print("=" * 50)
    
    # Solicitar datos del paciente
    name = input("Nombre del paciente: ")
    phone = input("Teléfono (formato: +34XXXXXXXXX): ")
    email = input("Email (opcional, presiona Enter para omitir): ") or ""
    language = input("Idioma (es/en/ca/ar) [es]: ") or "es"
    
    # Datos del formulario (como si fuera enviado desde el navegador)
    form_data = {
        "name": name,
        "phone": phone,
        "email": email,
        "language": language
    }
    
    try:
        print("\n📤 Enviando datos al panel de administración...")
        print(f"URL: {admin_url}/patients/new")
        print(f"Datos: {json.dumps(form_data, indent=2)}")
        
        # Enviar como form data (no JSON)
        response = requests.post(f"{admin_url}/patients/new", data=form_data, allow_redirects=False)
        
        print(f"\n📊 Respuesta del servidor:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201, 303]:  # 303 es redirect después de crear
            print("✅ ¡Paciente creado correctamente!")
            if response.status_code == 303:
                print(f"Redirigido a: {response.headers.get('location', 'N/A')}")
            return True
        else:
            print(f"❌ Error creando paciente: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_admin_panel():
    """Prueba si el panel de administración está funcionando"""
    admin_url = "https://mark-admin.onrender.com"
    
    try:
        print("🔍 Probando conexión con Panel de Administración...")
        response = requests.get(f"{admin_url}/dashboard", timeout=10)
        
        if response.status_code == 200:
            print("✅ Panel de Administración está funcionando correctamente!")
            return True
        else:
            print(f"❌ Error en Panel de Administración: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando con Panel de Administración: {e}")
        return False

def check_patients_page():
    """Verifica si la página de pacientes está accesible"""
    admin_url = "https://mark-admin.onrender.com"
    
    try:
        print("📋 Verificando página de pacientes...")
        response = requests.get(f"{admin_url}/patients", timeout=10)
        
        if response.status_code == 200:
            print("✅ Página de pacientes accesible!")
            print(f"Contenido: {len(response.text)} caracteres")
            return True
        else:
            print(f"❌ Error accediendo a pacientes: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 MARK ASSISTANT - CREAR PACIENTE VIA ADMIN PANEL")
    print("=" * 60)
    
    # Prueba 1: Verificar panel de admin
    print("\n1️⃣ Verificando Panel de Administración...")
    admin_ok = test_admin_panel()
    
    if not admin_ok:
        print("\n❌ El panel de administración no está funcionando.")
        exit(1)
    
    # Prueba 2: Verificar página de pacientes
    print("\n2️⃣ Verificando página de pacientes...")
    patients_ok = check_patients_page()
    
    # Prueba 3: Crear nuevo paciente
    print("\n3️⃣ Crear nuevo paciente:")
    if patients_ok:
        create_patient_via_admin()
    else:
        print("❌ No se puede crear paciente porque la página no es accesible.")
    
    print("\n" + "=" * 60)
    print("✅ Proceso completado!")
    print("\n🌐 URLs útiles:")
    print("• Dashboard: https://mark-admin.onrender.com/dashboard")
    print("• Pacientes: https://mark-admin.onrender.com/patients")
    print("• Crear paciente: https://mark-admin.onrender.com/patients/new")
    print("\n📱 Próximos pasos:")
    print("1. Configura WhatsApp Business API")
    print("2. Envía un mensaje al número de WhatsApp configurado")
    print("3. Mark responderá automáticamente") 