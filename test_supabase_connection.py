import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Opción 1: Configuración directa del entorno
print("=== PROBANDO CONEXIÓN USANDO LOS DATOS DEL ARCHIVO .env ===")
# Datos proporcionados por el usuario
user = os.getenv("DB_USER", "postgres.vtfyydqigxiowkswgreu")
password = os.getenv("DB_PASSWORD", "espanyol4A") 
host = os.getenv("DB_HOST", "aws-0-eu-central-1.pooler.supabase.com")
port = os.getenv("DB_PORT", "6543")
dbname = os.getenv("DB_NAME", "postgres")

# Intentar la conexión
try:
    print(f"Intentando conectar a: {host}:{port} como {user}")
    connection = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        dbname=dbname
    )
    
    print("¡Conexión exitosa!")
    
    # Crear un cursor para ejecutar consultas SQL
    cursor = connection.cursor()
    
    # Consulta de ejemplo
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Hora actual del servidor:", result)

    # Cerrar cursor y conexión
    cursor.close()
    connection.close()
    print("Conexión cerrada.")

except Exception as e:
    print(f"Falló la conexión: {e}")
    print("\nProbando con puerto alternativo (5432)...")
    
    try:
        # Intentar con puerto 5432
        connection = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port="5432",  # Puerto alternativo
            dbname=dbname
        )
        
        print("¡Conexión exitosa con puerto 5432!")
        
        # Crear un cursor para ejecutar consultas SQL
        cursor = connection.cursor()
        
        # Consulta de ejemplo
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Hora actual del servidor:", result)

        # Cerrar cursor y conexión
        cursor.close()
        connection.close()
        print("Conexión cerrada.")
    
    except Exception as e2:
        print(f"También falló con puerto 5432: {e2}")

# Opción 2: Usando la URL directa a Supabase
print("\n\n=== PROBANDO CONEXIÓN DIRECTA A SUPABASE ===")
try:
    direct_host = "db.vtfyydqigxiowkswgreu.supabase.co"
    direct_user = "postgres"
    direct_password = "espanyol4A"
    direct_port = "5432"
    direct_dbname = "postgres"
    
    print(f"Intentando conexión directa a: {direct_host}:{direct_port} como {direct_user}")
    connection = psycopg2.connect(
        user=direct_user,
        password=direct_password,
        host=direct_host,
        port=direct_port,
        dbname=direct_dbname
    )
    
    print("¡Conexión directa exitosa!")
    
    # Crear un cursor para ejecutar consultas SQL
    cursor = connection.cursor()
    
    # Consulta de ejemplo
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Hora actual del servidor:", result)

    # Cerrar cursor y conexión
    cursor.close()
    connection.close()
    print("Conexión cerrada.")
except Exception as e:
    print(f"Falló la conexión directa: {e}")

# Opción 3: Usando la URL de conexión del archivo .env
print("\n\n=== PROBANDO CONEXIÓN USANDO DATABASE_URL DEL ARCHIVO .env ===")
db_url = os.getenv("DATABASE_URL")

if db_url:
    try:
        print(f"Intentando conectar usando DATABASE_URL: {db_url}")
        connection = psycopg2.connect(db_url)
        
        print("¡Conexión exitosa usando DATABASE_URL!")
        
        # Crear un cursor para ejecutar consultas SQL
        cursor = connection.cursor()
        
        # Consulta de ejemplo
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Hora actual del servidor:", result)

        # Cerrar cursor y conexión
        cursor.close()
        connection.close()
        print("Conexión cerrada.")
    
    except Exception as e:
        print(f"Falló la conexión usando DATABASE_URL: {e}")
else:
    print("No se encontró DATABASE_URL en el archivo .env")

print("\n\nSi ninguna conexión funcionó, verifica los siguientes puntos:")
print("1. Asegúrate de que la contraseña sea correcta")
print("2. Verifica que tu IP esté en la lista blanca de Supabase")
print("3. Confirma que el usuario tenga permisos para conectarse")
print("4. Revisa la configuración del host y puerto en el panel de Supabase")
print("5. Intenta iniciar sesión directamente en el panel de Supabase con tu usuario javierramirez91") 