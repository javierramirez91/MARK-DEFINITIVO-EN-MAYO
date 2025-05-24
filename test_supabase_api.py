import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

print("=== PROBANDO CONEXIÓN A SUPABASE USANDO LA API OFICIAL ===")

# Usar credenciales proporcionadas directamente
supabase_url = "https://vtfyydqigxiowkswgreu.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0Znl5ZHFpZ3hpb3drc3dncmV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0MDY2MTcsImV4cCI6MjA1OTk4MjYxN30.5KkIDmkHnH_YoMO9ZpwVQRhB-lKimZmN5ctS2f--PsM"
supabase_service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0Znl5ZHFpZ3hpb3drc3dncmV1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDQwNjYxNywiZXhwIjoyMDU5OTgyNjE3fQ.VEyYaTiz12T83ctGWqo7KwUHR-hnSeRmsG_NoITEPNE"
supabase_jwt_secret = "hLYZ5Zh3xcrgNRwNZ1CAxJ0cJTZ/brkB+Fy8XclHtyGXoFbhfgdwr4TPKW94w9n4zhi4jeQct06hEiWgbM8RKQ=="

print(f"URL de Supabase: {supabase_url}")
print(f"Clave anónima: [Disponible]")
print(f"Clave de servicio: [Disponible]")
print(f"JWT Secret: [Disponible]")

# Función para probar las tablas disponibles
def list_tables(client, prefix=""):
    try:
        # Intentar leer las tablas existentes con una consulta SQL
        response = client.rpc('list_tables').execute()
        print(f"{prefix} Tablas disponibles: {response}")
        return response
    except Exception as e:
        print(f"{prefix} Error al listar tablas: {e}")
        return None

try:
    # Intentar conectar con la clave anónima
    print("\n[1] Intentando conectar con la clave anónima...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Conexión básica exitosa con clave anónima")
    
    # Intentar listar las tablas disponibles
    list_tables(supabase, "[Anon]")
    
    # Intentar obtener datos de algunas tablas comunes
    for table in ["users", "clients", "patients", "appointments", "profiles"]:
        try:
            print(f"\nProbando acceso a tabla '{table}'...")
            response = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ Acceso exitoso a la tabla '{table}': {response}")
        except Exception as e:
            print(f"❌ Error accediendo a tabla '{table}': {e}")
    
except Exception as e:
    print(f"❌ Error general con clave anónima: {e}")
    
try:
    # Intentar conectar con la clave de servicio (tiene más permisos)
    print("\n\n[2] Intentando conectar con la clave de servicio...")
    supabase_admin: Client = create_client(supabase_url, supabase_service_key)
    print("✅ Conexión básica exitosa con clave de servicio")
    
    # Intentar listar las tablas disponibles
    list_tables(supabase_admin, "[Service]")
    
    # Intentar crear una tabla de prueba
    try:
        print("\nIntentando crear una tabla de prueba 'mark_test'...")
        supabase_admin.rpc(
            'create_test_table', 
            {'table_name': 'mark_test'}
        ).execute()
        print("✅ Tabla de prueba creada correctamente")
    except Exception as e:
        print(f"❌ Error al crear tabla de prueba: {e}")
    
except Exception as e:
    print(f"❌ Error general con clave de servicio: {e}")

print("\n\n=== RESUMEN DE DIAGNÓSTICO ===")
print("1. Si la conexión básica fue exitosa pero no puedes acceder a tablas:")
print("   - Verifica que existan las tablas que intentas consultar")
print("   - Revisa los permisos Row Level Security (RLS) en Supabase")
print("2. Si hay errores de conexión:")
print("   - Asegúrate de que tu IP esté en la lista blanca de Supabase")
print("   - Verifica que el proyecto esté activo")
print("3. Siguientes pasos:")
print("   - Crea tablas necesarias en Supabase (puedes usar el SQL Editor)")
print("   - Configura políticas RLS adecuadas para tus necesidades")
print("   - Actualiza el archivo .env con las credenciales verificadas")
print("   - Intenta ejecutar tu aplicación principal") 