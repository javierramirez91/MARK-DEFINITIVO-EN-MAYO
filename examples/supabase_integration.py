"""
Ejemplos de integración con Supabase usando diferentes enfoques:
1. Cliente API de Supabase
2. SQLAlchemy ORM

Este script demuestra cómo usar ambos métodos para interactuar con Supabase.
"""
import os
from dotenv import load_dotenv
from database import SupabaseClient, SupabaseAlchemyClient, Base
from sqlalchemy import Column, String, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Cargar variables de entorno
load_dotenv()

# Modelo para SQLAlchemy
class Task(Base):
    """Modelo para la tabla tasks (tareas)."""
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String)
    is_complete = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, server_default=text('NOW()'))
    updated_at = Column(DateTime, server_default=text('NOW()'))

def ejemplo_supabase_api():
    """Ejemplo usando el cliente API de Supabase."""
    print("\n===== USANDO CLIENTE API DE SUPABASE =====")
    
    # Crear cliente
    supabase = SupabaseClient()
    client = supabase.connect(use_service_key=True)
    
    # Consultar tablas
    try:
        # Intentar obtener datos de la tabla 'todos'
        response = supabase.query_table(
            "todos",
            lambda table: table.select("*").limit(5),
            use_service_key=True
        )
        
        print("Resultados de la tabla 'todos':")
        if response and response.data:
            for todo in response.data:
                print(f"- {todo.get('title', 'Sin título')}: {todo.get('is_complete', False)}")
        else:
            print("No se encontraron datos en la tabla 'todos'")
        
    except Exception as e:
        print(f"Error al consultar la tabla 'todos': {e}")
    
    # Crear una nueva tarea si la tabla existe
    try:
        response = supabase.query_table(
            "todos",
            lambda table: table.insert({
                "title": "Nueva tarea creada por el cliente API",
                "description": "Esta tarea fue creada usando el cliente API de Supabase",
                "is_complete": False
            }).select(),
            use_service_key=True
        )
        
        print("\nNueva tarea creada:")
        if response and response.data:
            for item in response.data:
                print(f"ID: {item.get('id')}, Título: {item.get('title')}")
        
    except Exception as e:
        print(f"Error al insertar nueva tarea: {e}")

def ejemplo_sqlalchemy():
    """Ejemplo usando SQLAlchemy ORM."""
    print("\n===== USANDO SQLALCHEMY ORM =====")
    
    # Crear cliente
    client = SupabaseAlchemyClient(use_pooler=False)
    
    # Listar tablas disponibles
    try:
        tables = client.get_table_names()
        print(f"Tablas disponibles: {tables}")
    except Exception as e:
        print(f"Error al listar tablas: {e}")
    
    # Crear tabla tasks si no existe
    try:
        Base.metadata.create_all(client.engine)
        print("Tablas creadas/verificadas")
    except Exception as e:
        print(f"Error al crear tablas: {e}")
    
    # Insertar una nueva tarea
    try:
        with client.get_session() as session:
            # Crear una nueva tarea
            nueva_tarea = Task(
                title="Nueva tarea creada por SQLAlchemy",
                description="Esta tarea fue creada usando SQLAlchemy ORM",
                is_complete=False
            )
            
            # Agregar a la sesión y guardar
            session.add(nueva_tarea)
            session.commit()
            
            print(f"Nueva tarea creada con ID: {nueva_tarea.id}")
            
            # Consultar tareas
            tareas = session.query(Task).limit(5).all()
            
            print("\nTareas disponibles:")
            for tarea in tareas:
                print(f"- {tarea.title}: {'Completada' if tarea.is_complete else 'Pendiente'}")
            
    except Exception as e:
        print(f"Error en operaciones de SQLAlchemy: {e}")

def ejecutar_consulta_sql_directa():
    """Ejemplo de ejecución de SQL directa con SQLAlchemy."""
    print("\n===== EJECUTANDO SQL DIRECTO =====")
    
    # Crear cliente
    client = SupabaseAlchemyClient()
    
    try:
        # Ejecutar una consulta SQL directa
        result = client.execute_query("""
            SELECT 
                table_name, 
                column_name, 
                data_type 
            FROM 
                information_schema.columns 
            WHERE 
                table_schema = 'public' 
            ORDER BY 
                table_name, 
                ordinal_position
            LIMIT 10
        """)
        
        print("Estructura de las tablas:")
        for row in result:
            table_name, column_name, data_type = row
            print(f"Tabla: {table_name}, Columna: {column_name}, Tipo: {data_type}")
            
    except Exception as e:
        print(f"Error al ejecutar SQL directo: {e}")

if __name__ == "__main__":
    print("=== EJEMPLOS DE INTEGRACIÓN CON SUPABASE ===")
    
    # Ejecutar ejemplos
    ejemplo_supabase_api()
    ejemplo_sqlalchemy()
    ejecutar_consulta_sql_directa()
    
    print("\n=== FIN DE LOS EJEMPLOS ===") 