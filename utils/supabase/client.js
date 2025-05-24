import { createBrowserClient } from "@supabase/ssr";

/**
 * Crea un cliente Supabase para componentes del cliente (navegador)
 * @returns {ReturnType<typeof createBrowserClient>} Cliente Supabase
 */
export const createClient = () => {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
}; 