import os
# from dotenv import load_dotenv # ELIMINADO
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Cargar variables de entorno
# load_dotenv() # ELIMINADO

# Obtener credenciales de conexión
db_host = os.getenv("DB_HOST", "db.vtfyydqigxiowkswgreu.supabase.co")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "postgres")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD") # ELIMINADA CONTRASEÑA HARDCODEADA

# SQL para la creación del esquema básico
sql_create_schema = """
-- Extensión para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de Usuarios (extendiendo la tabla auth.users de Supabase)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabla de Clientes (pacientes)
CREATE TABLE IF NOT EXISTS public.clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    address VARCHAR(200),
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabla de Sesiones/Citas
CREATE TABLE IF NOT EXISTS public.appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES public.clients(id) ON DELETE CASCADE,
    therapist_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    scheduled_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    session_type VARCHAR(50),
    notes TEXT,
    zoom_link VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabla de Notas Clínicas
CREATE TABLE IF NOT EXISTS public.clinical_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID REFERENCES public.appointments(id) ON DELETE SET NULL,
    client_id UUID REFERENCES public.clients(id) ON DELETE CASCADE,
    therapist_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    content TEXT,
    is_draft BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabla de Configuración del Sistema
CREATE TABLE IF NOT EXISTS public.system_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Función para actualizar el timestamp 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar el campo updated_at
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON public.user_profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
BEFORE UPDATE ON public.clients
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at
BEFORE UPDATE ON public.appointments
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinical_notes_updated_at
BEFORE UPDATE ON public.clinical_notes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at
BEFORE UPDATE ON public.system_settings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Configuración básica de RLS (Row Level Security)
-- Habilitar RLS en todas las tablas
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinical_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;

-- Políticas de RLS
-- Ejemplo: Los administradores pueden ver todos los perfiles, los usuarios solo el suyo
CREATE POLICY admin_all_profiles ON public.user_profiles
    FOR ALL
    TO authenticated
    USING (role = 'admin' OR auth_id = auth.uid());

-- Ejemplo: Los terapeutas pueden ver sus clientes asignados
CREATE POLICY therapist_clients ON public.clients
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.appointments a
            JOIN public.user_profiles u ON a.therapist_id = u.id
            WHERE a.client_id = clients.id AND u.auth_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM public.user_profiles u
            WHERE u.auth_id = auth.uid() AND u.role = 'admin'
        )
    );

-- Insertar configuraciones iniciales
INSERT INTO public.system_settings (setting_name, setting_value, description)
VALUES
    ('clinic_name', 'Centre de Psicologia Jaume I', 'Nombre del centro clínico'),
    ('clinic_address', 'Gran Via Jaume I, 41-43, Entresol 1a, 17001, Girona', 'Dirección del centro'),
    ('clinic_phone', '+34671232783', 'Teléfono principal del centro'),
    ('clinic_email', 'info@centrepsicologiajaumeprimer.com', 'Email principal del centro'),
    ('clinic_website', 'https://centrepsicologiajaume1.com', 'Sitio web del centro')
ON CONFLICT (setting_name) DO UPDATE
SET setting_value = EXCLUDED.setting_value,
    description = EXCLUDED.description,
    updated_at = NOW();
"""

def create_schema():
    try:
        if not db_password:
            print("Error: La variable de entorno DB_PASSWORD no está configurada.")
            return False
            
        print(f"Conectando a Supabase en {db_host}:{db_port} como {db_user}...")
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        # Necesario para crear extensiones
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        print("Ejecutando script de creación de schema...")
        cursor.execute(sql_create_schema)
        
        cursor.close()
        conn.close()
        
        print("¡Schema creado exitosamente!")
        return True
    
    except Exception as e:
        print(f"Error al crear schema: {e}")
        return False

if __name__ == "__main__":
    create_schema() 