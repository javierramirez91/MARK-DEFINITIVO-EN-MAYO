from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declared_attr
from contextlib import contextmanager
from dotenv import load_dotenv
import os
import logging
import time
import socket
from urllib.parse import quote_plus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqlalchemy_client")

# Cargar variables de entorno
load_dotenv()

# Base declarativa para modelos
Base = declarative_base()

class SupabaseAlchemyClient:
    """
    Cliente para interactuar con Supabase mediante SQLAlchemy.
    
    Esta clase proporciona métodos para conectar y operar con Supabase
    usando SQLAlchemy como ORM. Está optimizada para funcionar en entornos
    de producción como Render.
    """
    
    _instance = None
    _retry_count = 3
    _retry_delay = 2  # segundos
    
    def __new__(cls, use_pooler=False, pooler_type='transaction', connection_source='env'):
        """Implementación del patrón Singleton para asegurar una única instancia."""
        if cls._instance is None:
            cls._instance = super(SupabaseAlchemyClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, use_pooler=False, pooler_type='transaction', connection_source='env'):
        """
        Inicializa el cliente SQLAlchemy si aún no está inicializado.
        
        Args:
            use_pooler (bool): Si es True, usa el connection pooler de Supabase
            pooler_type (str): Tipo de pooler ('transaction' o 'session')
            connection_source (str): Fuente de la conexión ('env', 'render', 'url')
        """
        if not self._initialized:
            # Detectar automáticamente si estamos en Render
            is_render = 'RENDER' in os.environ
            
            # Si estamos en Render y no se especificó lo contrario, usar pooler
            if is_render and connection_source != 'url':
                use_pooler = True
                logger.info("Detectado entorno Render, usando Connection Pooler por defecto")
            
            # Determinar qué configuración usar basado en los parámetros
            if connection_source == 'url':
                # Usar la URL de conexión directamente
                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    database_url = os.getenv("RENDER_DATABASE_URL")
                
                if not database_url:
                    raise ValueError("No se encontró DATABASE_URL en las variables de entorno")
                
                self.database_url = database_url
                logger.info(f"Usando URL de conexión proporcionada: {self._mask_password(database_url)}")
                
            else:
                # Construir la URL de conexión desde los componentes
                if use_pooler:
                    if pooler_type == 'transaction':
                        # Transaction Pooler (puerto 6543)
                        user = os.getenv("DB_POOLER_USER", f"postgres.{os.getenv('SUPABASE_PROJECT_ID', 'vtfyydqigxiowkswgreu')}")
                        password = os.getenv("DB_POOLER_PASSWORD", os.getenv("DB_PASSWORD", "espanyol4A"))
                        host = os.getenv("DB_POOLER_HOST", "aws-0-eu-central-1.pooler.supabase.com")
                        port = os.getenv("DB_POOLER_PORT", "6543")
                        dbname = os.getenv("DB_NAME", "postgres")
                        logger.info("Usando Transaction Pooler de Supabase")
                    else:
                        # Session Pooler (puerto 5432 en pooler subdomain)
                        user = os.getenv("DB_POOLER_USER", f"postgres.{os.getenv('SUPABASE_PROJECT_ID', 'vtfyydqigxiowkswgreu')}")
                        password = os.getenv("DB_POOLER_PASSWORD", os.getenv("DB_PASSWORD", "espanyol4A"))
                        host = os.getenv("DB_POOLER_HOST", "aws-0-eu-central-1.pooler.supabase.com")
                        port = "5432"
                        dbname = os.getenv("DB_NAME", "postgres")
                        logger.info("Usando Session Pooler de Supabase")
                else:
                    # Conexión directa (no pooler)
                    user = os.getenv("DB_USER", "postgres")
                    password = os.getenv("DB_PASSWORD", "espanyol4A")
                    host = os.getenv("DB_HOST", f"db.{os.getenv('SUPABASE_PROJECT_ID', 'vtfyydqigxiowkswgreu')}.supabase.co")
                    port = os.getenv("DB_PORT", "5432")
                    dbname = os.getenv("DB_NAME", "postgres")
                    logger.info("Usando conexión directa a Supabase")
                
                # Escapar cualquier carácter especial en la contraseña
                escaped_password = quote_plus(password)
                
                # Construir la URL de conexión
                self.database_url = f"postgresql+psycopg2://{user}:{escaped_password}@{host}:{port}/{dbname}"
            
            # Añadir parámetros SSL si es necesario
            ssl_mode = os.getenv("PGSSLMODE", "require")
            if ssl_mode:
                self.database_url += f"?sslmode={ssl_mode}"
            
            # Determinar opciones de pool según el entorno
            pool_options = {}
            
            # En Render, es recomendable ajustar el tamaño del pool
            if is_render:
                pool_options.update({
                    'pool_size': int(os.getenv("PGBOUNCER_DEFAULT_POOL_SIZE", 20)),
                    'max_overflow': int(os.getenv("PGBOUNCER_MAX_OVERFLOW", 10)),
                    'pool_timeout': 30,
                    'pool_recycle': 1800,  # Reciclar conexiones cada 30 minutos
                })
                logger.info(f"Configuración de pool para Render: {pool_options}")
            
            # Crear el motor SQLAlchemy con manejo de error
            try:
                # Si usamos connection pooler, deshabilitamos el pooling de SQLAlchemy
                if use_pooler:
                    self.engine = create_engine(self.database_url, poolclass=NullPool)
                    logger.info("Pooling de SQLAlchemy desactivado por usar Connection Pooler de Supabase")
                else:
                    self.engine = create_engine(self.database_url, **pool_options)
                    logger.info("Pooling de SQLAlchemy configurado con éxito")
                
                # Crear fábrica de sesiones
                self.Session = sessionmaker(bind=self.engine)
                
                # Metadata para introspección de esquema
                self.metadata = MetaData()
                
                self._initialized = True
                logger.info(f"Cliente SQLAlchemy inicializado para: {self._mask_connection_info(host, port)}")
                
                # Verificar la conexión
                self._test_connection()
                
            except Exception as e:
                logger.error(f"Error al inicializar SQLAlchemy: {e}")
                raise
    
    def _mask_password(self, url_string):
        """Enmascara la contraseña en una URL para el registro seguro."""
        try:
            url = make_url(url_string)
            masked = f"{url.drivername}://{url.username}:****@{url.host}:{url.port}/{url.database}"
            return masked
        except:
            # Si hay un error al parsear, devolver una versión segura
            return "postgresql://<username>:****@<host>:<port>/<database>"
    
    def _mask_connection_info(self, host, port):
        """Enmascara la información de conexión para el registro seguro."""
        return f"{host}:{port}"
    
    def _test_connection(self):
        """Prueba la conexión a la base de datos."""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Conexión a Supabase verificada con éxito")
        except Exception as e:
            logger.error(f"Error al verificar la conexión: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Proporciona un contexto para trabajar con una sesión de SQLAlchemy.
        Implementa reintentos automáticos para mayor robustez.
        
        Yields:
            Session: Una sesión de SQLAlchemy.
        """
        session = None
        retry_count = 0
        last_error = None
        
        while retry_count < self._retry_count:
            try:
                session = self.Session()
                yield session
                session.commit()
                break  # Salir del bucle si todo está bien
            except Exception as e:
                if session:
                    session.rollback()
                
                # Determinar si es un error recuperable
                if isinstance(e, (socket.timeout, ConnectionError)) or "connection" in str(e).lower():
                    retry_count += 1
                    last_error = e
                    wait_time = self._retry_delay * (2 ** (retry_count - 1))  # Backoff exponencial
                    logger.warning(f"Error de conexión, reintentando ({retry_count}/{self._retry_count}) en {wait_time} segundos: {e}")
                    time.sleep(wait_time)
                else:
                    # Error no recuperable
                    logger.error(f"Error en la transacción (no recuperable): {e}")
                    raise
            finally:
                if session:
                    session.close()
        
        # Si llegamos aquí y retry_count alcanza el máximo, relanzar el último error
        if retry_count == self._retry_count and last_error:
            logger.error(f"Error en la transacción después de {self._retry_count} intentos: {last_error}")
            raise last_error
    
    def create_tables(self):
        """Crea todas las tablas definidas en el modelo Base."""
        retry_count = 0
        last_error = None
        
        while retry_count < self._retry_count:
            try:
                Base.metadata.create_all(self.engine)
                logger.info("Tablas creadas correctamente")
                return
            except Exception as e:
                retry_count += 1
                last_error = e
                wait_time = self._retry_delay * (2 ** (retry_count - 1))
                logger.warning(f"Error al crear tablas, reintentando ({retry_count}/{self._retry_count}) en {wait_time} segundos: {e}")
                time.sleep(wait_time)
        
        if last_error:
            logger.error(f"Error al crear tablas después de {self._retry_count} intentos: {last_error}")
            raise last_error
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL directa.
        
        Args:
            query (str): Consulta SQL a ejecutar
            params (dict, optional): Parámetros para la consulta
            
        Returns:
            list: Resultados de la consulta
        """
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()
    
    def get_table_names(self):
        """
        Obtiene los nombres de todas las tablas en el esquema public.
        
        Returns:
            list: Lista de nombres de tablas
        """
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
            """))
            return [row[0] for row in result.fetchall()]
    
    @staticmethod
    def get_optimal_client(env="auto"):
        """
        Devuelve el cliente óptimo para el entorno especificado.
        
        Args:
            env (str): Entorno ('development', 'production', 'render', 'auto')
            
        Returns:
            SupabaseAlchemyClient: Cliente configurado para el entorno
        """
        # Detectar automáticamente el entorno si es 'auto'
        if env == "auto":
            if 'RENDER' in os.environ:
                env = "render"
            elif os.getenv("ENVIRONMENT") == "production":
                env = "production"
            else:
                env = "development"
        
        if env in ("render", "production"):
            # Para entornos de producción, usar transaction pooler
            return SupabaseAlchemyClient(use_pooler=True, pooler_type='transaction')
        else:
            # Para desarrollo, usar conexión directa
            return SupabaseAlchemyClient(use_pooler=False)

# Modelos de ejemplo
class Todo(Base):
    """Modelo para la tabla todos."""
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    is_complete = Column(Boolean, default=False)
    user_id = Column(String)
    created_at = Column(DateTime, server_default=text('NOW()'))
    updated_at = Column(DateTime, server_default=text('NOW()'))

# Ejemplo de uso
if __name__ == "__main__":
    # Probar las diferentes configuraciones
    
    # 1. Conexión directa (ideal para desarrollo)
    print("\n===== PROBANDO CONEXIÓN DIRECTA =====")
    try:
        direct_client = SupabaseAlchemyClient(use_pooler=False)
        tables = direct_client.get_table_names()
        print(f"Tablas disponibles: {tables}")
        
        # Consulta de ejemplo
        result = direct_client.execute_query("SELECT NOW()")
        print(f"Hora del servidor: {result[0][0]}")
        
        print("¡Conexión directa exitosa!")
    except Exception as e:
        print(f"Error en conexión directa: {e}")
    
    # 2. Transaction Pooler (recomendado para producción/Render)
    print("\n===== PROBANDO TRANSACTION POOLER =====")
    try:
        transaction_client = SupabaseAlchemyClient(use_pooler=True, pooler_type='transaction')
        result = transaction_client.execute_query("SELECT NOW()")
        print(f"Hora del servidor (Transaction Pooler): {result[0][0]}")
        print("¡Conexión con Transaction Pooler exitosa!")
    except Exception as e:
        print(f"Error en Transaction Pooler: {e}")
    
    # 3. Cliente óptimo para el entorno actual
    print("\n===== PROBANDO CLIENTE ÓPTIMO AUTOMÁTICO =====")
    try:
        optimal_client = SupabaseAlchemyClient.get_optimal_client()
        result = optimal_client.execute_query("SELECT version()")
        print(f"Versión de PostgreSQL: {result[0][0]}")
        print("¡Conexión óptima exitosa!")
    except Exception as e:
        print(f"Error en conexión óptima: {e}") 