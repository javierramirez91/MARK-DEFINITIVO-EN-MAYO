'use client';

import { useEffect, useState } from 'react';
import { createClient } from '../utils/supabase/client';

/**
 * Componente de cliente que usa Supabase para añadir tareas nuevas
 */
export default function AddTodo() {
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  
  // Crear cliente de Supabase para el navegador
  const supabase = createClient();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('El título de la tarea no puede estar vacío');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccessMessage('');
    
    try {
      // Insertar nueva tarea en Supabase
      const { data, error } = await supabase
        .from('todos')
        .insert([
          { title, is_complete: false },
        ])
        .select();
      
      if (error) throw error;
      
      setTitle('');
      setSuccessMessage('¡Tarea añadida correctamente!');
      
      // Mostrar mensaje de éxito durante 3 segundos
      setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
      
    } catch (err) {
      setError(err.message || 'Error al añadir la tarea');
      console.error('Error al añadir tarea:', err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="max-w-md mx-auto p-4 bg-white shadow-md rounded-lg">
      <h2 className="text-xl font-bold mb-4">Añadir Nueva Tarea</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Título de la tarea
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Escribe una nueva tarea..."
            disabled={loading}
          />
        </div>
        
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-md text-white font-medium ${
            loading ? 'bg-blue-300' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Añadiendo...' : 'Añadir Tarea'}
        </button>
      </form>
      
      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="mt-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {successMessage}
        </div>
      )}
    </div>
  );
} 