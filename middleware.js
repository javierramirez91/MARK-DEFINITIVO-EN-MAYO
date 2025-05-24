import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs';
import { NextResponse } from 'next/server';

// Rutas que requieren autenticación
const PROTECTED_ROUTES = [
  '/dashboard',
  '/api/protected',
  '/profile',
];

// Rutas públicas (no requieren autenticación)
const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/register',
  '/api/webhook',
  '/public',
];

// Rutas API que deberían verificar un token de API
const API_ROUTES = [
  '/api/data',
  '/api/integration',
];

/**
 * Middleware que se ejecuta en cada solicitud
 * @param {import("next/server").NextRequest} req - Solicitud entrante
 * @returns {Promise<NextResponse>} Respuesta del middleware
 */
export async function middleware(req) {
  const res = NextResponse.next();
  
  // Crear cliente de Supabase específico para este middleware
  const supabase = createMiddlewareClient({ req, res });
  
  // Obtener la ruta actual
  const path = req.nextUrl.pathname;
  
  // Verificar si la ruta es una API que requiere token
  if (API_ROUTES.some(route => path.startsWith(route))) {
    const apiKey = req.headers.get('x-api-key');
    
    // Si no hay API key, devolver error 401
    if (!apiKey) {
      return new NextResponse(
        JSON.stringify({ error: 'Se requiere API key' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    // Aquí se podría validar la API key contra una tabla en Supabase
    // Por ahora, solo comprobamos que exista
  }
  
  // Para rutas públicas, no verificamos autenticación
  if (PUBLIC_ROUTES.some(route => path === route || path.startsWith(route))) {
    return res;
  }
  
  // Para webhook, permitir sin autenticación (ya tiene su propio sistema de verificación)
  if (path === '/api/webhook' || path.startsWith('/api/webhook')) {
    return res;
  }
  
  // Verificar la sesión actual
  const {
    data: { session },
  } = await supabase.auth.getSession();
  
  // Si la ruta está protegida y no hay sesión, redirigir a login
  if (PROTECTED_ROUTES.some(route => path === route || path.startsWith(route)) && !session) {
    // Construir URL de redirección
    const redirectUrl = new URL('/login', req.nextUrl.origin);
    redirectUrl.searchParams.set('redirect', req.nextUrl.pathname);
    
    return NextResponse.redirect(redirectUrl);
  }
  
  return res;
}

// Configurar para que el middleware se ejecute en las rutas especificadas
export const config = {
  matcher: [
    /*
     * Excluir archivos estáticos y favicon
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}; 