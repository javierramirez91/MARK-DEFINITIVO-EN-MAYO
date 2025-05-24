-- Crear la tabla 'todos' para gestionar tareas
CREATE TABLE IF NOT EXISTS public.todos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    is_complete BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_todos_user_id ON public.todos(user_id);
CREATE INDEX IF NOT EXISTS idx_todos_is_complete ON public.todos(is_complete);

-- Activar Row Level Security (RLS)
ALTER TABLE public.todos ENABLE ROW LEVEL SECURITY;

-- Crear políticas de seguridad para diferentes operaciones
-- Política para que los usuarios solo puedan ver sus propias tareas
CREATE POLICY "Usuarios pueden ver sus propias tareas" ON public.todos
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Política para que los usuarios solo puedan crear tareas para sí mismos
CREATE POLICY "Usuarios pueden crear sus propias tareas" ON public.todos
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Política para que los usuarios solo puedan actualizar sus propias tareas
CREATE POLICY "Usuarios pueden actualizar sus propias tareas" ON public.todos
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

-- Política para que los usuarios solo puedan eliminar sus propias tareas
CREATE POLICY "Usuarios pueden eliminar sus propias tareas" ON public.todos
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Función para actualizar automáticamente el campo 'updated_at'
CREATE OR REPLACE FUNCTION update_todo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar automáticamente el campo 'updated_at'
CREATE TRIGGER trigger_update_todo_timestamp
BEFORE UPDATE ON public.todos
FOR EACH ROW
EXECUTE FUNCTION update_todo_updated_at();

-- Insertar algunos datos de ejemplo (opcional)
INSERT INTO public.todos (title, description, is_complete, user_id)
VALUES 
    ('Completar la configuración de Supabase', 'Configurar la conexión con Next.js', FALSE, NULL),
    ('Crear la tabla de usuarios', 'Configurar RLS y políticas de seguridad', FALSE, NULL),
    ('Diseñar la interfaz de usuario', 'Utilizar TailwindCSS para el diseño', TRUE, NULL)
ON CONFLICT (id) DO NOTHING; 