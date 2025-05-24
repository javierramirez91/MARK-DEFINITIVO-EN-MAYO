import { createClient } from '../utils/supabase/server';
import { cookies } from 'next/headers';

/**
 * Página de ejemplo que muestra las tareas desde Supabase
 */
export default async function TodosPage() {
  const cookieStore = cookies();
  const supabase = createClient(cookieStore);

  // Obtener tareas desde Supabase
  const { data: todos, error } = await supabase.from('todos').select('*');

  if (error) {
    console.error('Error al cargar tareas:', error);
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Tareas</h1>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>Error al cargar las tareas: {error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Tareas</h1>
      
      {todos && todos.length > 0 ? (
        <ul className="bg-white shadow-md rounded-lg divide-y">
          {todos.map((todo) => (
            <li key={todo.id} className="px-4 py-3 flex items-center">
              <input 
                type="checkbox" 
                checked={todo.is_complete} 
                readOnly 
                className="mr-3"
              />
              <span className={todo.is_complete ? "line-through text-gray-500" : ""}>
                {todo.title}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500">No hay tareas disponibles.</p>
      )}
      
      <div className="mt-6">
        <p className="text-sm text-gray-500">
          Nota: Para que este ejemplo funcione, debes crear una tabla 'todos' en tu base de datos Supabase
          con las columnas 'id', 'title', 'is_complete', y 'user_id'.
        </p>
      </div>
    </div>
  );
} 