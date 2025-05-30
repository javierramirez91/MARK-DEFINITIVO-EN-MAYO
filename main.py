"""
Punto de entrada principal para el asistente Mark.
Configura la aplicación FastAPI y carga todos los componentes necesarios.
"""

# --- Carga de variables de entorno --- PRIMERO --- #
import os # Necesario para que dotenv funcione correctamente en algunos casos
from dotenv import load_dotenv
load_dotenv() # Carga las variables desde .env al entorno del proceso
# ---------------------------------------------- #

import json
from datetime import datetime
# import os # No usado
# import logging # No usado
import asyncio
# import threading # ELIMINADO
# from typing import Dict, List, Any, Optional # No usados directamente
from pathlib import Path
# from datetime import timedelta # No usado

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Query # , Depends, BackgroundTasks # No usados directamente
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse # Añadido PlainTextResponse
# from fastapi.responses import JSONResponse # No usado

from core.config import settings, logger, verify_config
from database.d1_client import get_pending_notifications, update_notification_status
from services.whatsapp import send_whatsapp_message
from backend.api_server import apirouter
# from admin.admin_panel import run_admin_panel # ELIMINADO

# Configurar la aplicación FastAPI
app = FastAPI(
    title="Mark - Asistente Virtual",
    description="API para el asistente virtual Mark del Centre de Psicologia Jaume I",
    version="1.0.0"
)

# Montar el router de la API
app.include_router(apirouter, prefix="/api")

# Nuevo endpoint para la verificación del webhook de WhatsApp
@app.get("/webhook")
async def verify_whatsapp_webhook_direct(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Verifica el webhook de WhatsApp directamente para la configuración inicial de Meta.
    """
    logger.info(f"Llamada GET a /webhook recibida. Query params: hub.mode='{hub_mode}', hub.challenge='{hub_challenge}', hub.verify_token='{hub_verify_token}'")

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info(f"Webhook verificado correctamente (ruta /webhook). Challenge: {hub_challenge}")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        logger.warning(f"Fallo en la verificación del webhook (ruta /webhook). Token recibido: '{hub_verify_token}', Modo: '{hub_mode}'. Token esperado: '{settings.WHATSAPP_VERIFY_TOKEN}'")
        raise HTTPException(status_code=403, detail="Invalid verification token or mode")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos si existe el directorio
static_dir = Path("static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Tarea en segundo plano para procesar notificaciones pendientes
async def process_pending_notifications() -> None:
    """
    Procesa las notificaciones pendientes y envía mensajes de WhatsApp
    """
    try:
        # Obtener notificaciones pendientes
        result = await get_pending_notifications(limit=10)
        
        if not result.get("success", False):
            logger.error(f"Error al obtener notificaciones pendientes: {result.get('error')}")
            return
        
        notifications = result.get("results", [])
        
        if not notifications:
            return
        
        logger.info(f"Procesando {len(notifications)} notificaciones pendientes")
        
        # Procesar cada notificación
        for notification in notifications:
            notification_id = notification.get("id")
            # patient_id = notification.get("patient_id") # ELIMINADO (no usado)
            message = notification.get("message")
            channel = notification.get("channel")
            
            # Solo procesar notificaciones de WhatsApp por ahora
            if channel != "whatsapp":
                continue
            
            # Obtener el número de teléfono del paciente
            # Aquí se debería implementar la lógica para obtener el número del paciente
            # Por ahora, asumimos que está en los metadatos
            try:
                metadata = json.loads(notification.get("metadata", "{}"))
                phone = metadata.get("phone")
                
                if not phone:
                    logger.error(f"No se encontró número de teléfono para la notificación {notification_id}")
                    await update_notification_status(
                        notification_id, 
                        "failed", 
                        {"error": "No se encontró número de teléfono"}
                    )
                    continue
                
                # Enviar mensaje de WhatsApp
                result = send_whatsapp_message(phone, message)
                
                if result.get("success", False):
                    # Actualizar estado de la notificación a enviado
                    await update_notification_status(
                        notification_id, 
                        "sent", 
                        {
                            "message_sid": result.get("message_sid"),
                            "sent_at": datetime.utcnow().isoformat()
                        }
                    )
                    logger.info(f"Notificación {notification_id} enviada a {phone}")
                else:
                    # Actualizar estado de la notificación a fallido
                    await update_notification_status(
                        notification_id, 
                        "failed", 
                        {"error": result.get("error")}
                    )
                    logger.error(f"Error al enviar notificación {notification_id}: {result.get('error')}")
            
            except Exception as e:
                logger.error(f"Error al procesar notificación {notification_id}: {e}")
                await update_notification_status(
                    notification_id, 
                    "failed", 
                    {"error": str(e)}
                )
    
    except Exception as e:
        logger.error(f"Error al procesar notificaciones pendientes: {e}")

# Eventos de inicio y cierre de la aplicación
@app.on_event("startup")
async def startup_event() -> None:
    """
    Evento de inicio de la aplicación
    """
    # Verificar configuración
    config_status = verify_config()
    
    # if config_status["errors"]:  <-- Eliminar este bloque
    #     for error in config_status["errors"]:
    #         logger.error(f"Error de configuración: {error}")
    
    if "warnings" in config_status and config_status["warnings"]:
        for warning in config_status["warnings"]:
            logger.warning(f"Advertencia de configuración: {warning}")
    
    # Iniciar tarea periódica para procesar notificaciones
    asyncio.create_task(periodic_notification_processor())
    
    # # Iniciar panel de administración en un hilo separado <--- COMENTADO/ELIMINADO
    # admin_thread = threading.Thread(target=start_admin_panel)
    # admin_thread.daemon = True
    # admin_thread.start()
    
    logger.info("Asistente Mark iniciado correctamente")

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Evento de cierre de la aplicación
    """
    logger.info("Asistente Mark detenido")

# Tarea periódica para procesar notificaciones
async def periodic_notification_processor() -> None:
    """
    Ejecuta el procesador de notificaciones periódicamente
    """
    while True:
        try:
            await process_pending_notifications()
        except Exception as e:
            logger.error(f"Error en el procesador periódico de notificaciones: {e}")
        
        # Esperar 1 minuto antes de la próxima ejecución
        await asyncio.sleep(60)

# Endpoint de salud
@app.get("/health")
async def health_check() -> dict:
    """
    Endpoint para verificar el estado de la aplicación
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }

# Página de bienvenida
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Página de bienvenida con información sobre la API
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mark - Asistente Virtual</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                text-align: center;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                max-width: 600px;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .subtitle {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                opacity: 0.9;
            }
            .links {
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
                margin-top: 2rem;
            }
            .link {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                padding: 0.8rem 1.5rem;
                border-radius: 10px;
                transition: all 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .link:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            .status {
                margin-top: 2rem;
                padding: 1rem;
                background: rgba(0, 255, 0, 0.2);
                border-radius: 10px;
                font-size: 0.9rem;
            }
            .version {
                margin-top: 1rem;
                opacity: 0.7;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Mark</h1>
            <p class="subtitle">Asistente Virtual del Centre de Psicologia Jaume I</p>
            
            <div class="status">
                ✅ API funcionando correctamente
            </div>
            
            <div class="links">
                <a href="/docs" class="link">📚 Documentación Interactiva</a>
                <a href="/redoc" class="link">📖 Documentación ReDoc</a>
                <a href="/health" class="link">🏥 Estado del Sistema</a>
            </div>
            
            <p class="version">Versión 1.0.0</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    # Obtener configuración del servidor
    host = settings.HOST
    # Usar PORT de Render si está disponible, sino usar el configurado
    port = int(os.environ.get("PORT", settings.PORT))
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=settings.ENVIRONMENT == "development"
    ) 