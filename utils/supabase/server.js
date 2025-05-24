import { createServerClient } from "@supabase/ssr";

/**
 * Crea un cliente Supabase para componentes del servidor
 * @param {import("next/headers").ReadonlyRequestCookies} cookieStore - El almacén de cookies
 * @returns {ReturnType<typeof createServerClient>} Cliente Supabase
 */
export const createClient = (cookieStore) => {
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => 
              cookieStore.set(name, value, options)
            );
          } catch {
            // La función `setAll` fue llamada desde un Componente de Servidor.
            // Esto puede ignorarse si tienes middleware que refresca
            // las sesiones de usuario.
          }
        },
      },
    }
  );
}; 