import { createServerClient } from "@supabase/ssr";
import { NextResponse } from "next/server";

/**
 * Crea un cliente Supabase para middleware
 * @param {import("next/server").NextRequest} request - La solicitud entrante
 * @returns {NextResponse} Respuesta con cliente Supabase configurado
 */
export const createClient = (request) => {
  // Crear una respuesta no modificada
  let supabaseResponse = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => 
            request.cookies.set(name, value)
          );
          
          supabaseResponse = NextResponse.next({
            request,
          });
          
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  return { supabase, supabaseResponse };
}; 