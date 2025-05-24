# Script para instalar las dependencias necesarias para Supabase en Windows

# Colores para output
$Green = [ConsoleColor]::Green
$Yellow = [ConsoleColor]::Yellow
$Red = [ConsoleColor]::Red

Write-Host "=== Instalando dependencias para Supabase ===" -ForegroundColor $Green

# Instalación para Python (SQLAlchemy y Supabase)
Write-Host "`nInstalando dependencias de Python..." -ForegroundColor $Yellow
try {
    pip install python-dotenv sqlalchemy psycopg2-binary supabase uuid
    Write-Host "✓ Dependencias de Python instaladas correctamente" -ForegroundColor $Green
} catch {
    Write-Host "✗ Error al instalar dependencias de Python" -ForegroundColor $Red
    Write-Host "Intenta instalar manualmente con: pip install python-dotenv sqlalchemy psycopg2-binary supabase uuid" -ForegroundColor $Yellow
}

# Instalación para Next.js (si está presente)
if (Test-Path "package.json") {
    Write-Host "`nDetectado proyecto Next.js. Instalando dependencias..." -ForegroundColor $Yellow
    try {
        npm install @supabase/ssr @supabase/supabase-js
        Write-Host "✓ Dependencias de Next.js instaladas correctamente" -ForegroundColor $Green
    } catch {
        Write-Host "✗ Error al instalar dependencias de Next.js" -ForegroundColor $Red
        Write-Host "Intenta instalar manualmente con: npm install @supabase/ssr @supabase/supabase-js" -ForegroundColor $Yellow
    }
} else {
    Write-Host "`nNo se detectó package.json. Omitiendo instalación de dependencias de Next.js" -ForegroundColor $Yellow
}

Write-Host "`n=== Instalación completada ===" -ForegroundColor $Green
Write-Host "Recuerda verificar tu archivo .env con las credenciales correctas de Supabase." -ForegroundColor $Yellow
Write-Host "Para probar la conexión, ejecuta: python database/sqlalchemy_client.py" -ForegroundColor $Yellow
Write-Host "Para ver ejemplos de uso, ejecuta: python examples/supabase_integration.py" -ForegroundColor $Yellow 