"""
Servicio de integración con Stripe para gestión de pagos.
Permite generar enlaces de pago, verificar pagos y gestionar recursos.
"""
# logging es importado como logger desde core.config más abajo
# import json # No usado
import asyncio # Importar asyncio
from typing import Dict, List, Optional, Any # Restaurado List, Any
from datetime import datetime

import stripe
# import httpx # No se usa directamente aquí, eliminado

# Usar settings directamente para configuración
from core.config import settings, logger 

# Configurar API key de Stripe
try:
    # Usar settings en lugar de ApiConfig directamente si es Pydantic
    stripe.api_key = settings.STRIPE_API_KEY 
    logger.info("API key de Stripe configurada correctamente")
except Exception as e:
    logger.error(f"Error al configurar API key de Stripe: {e}")
    # Considerar lanzar un error o manejar la ausencia de la key
    stripe.api_key = None # Asegurarse que es None si falla


async def generate_payment_link(
    price_id: str, # Recibe price_id directamente
    customer_email: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    success_url_extra_params: str = "" # Para añadir params a la URL de éxito
) -> Optional[str]: # Puede devolver None en error
    """
    Genera un enlace de pago de Stripe Checkout usando un Price ID existente.
    
    Args:
        price_id: El ID del Price de Stripe a usar.
        customer_email: Email del cliente (opcional, pre-rellena el checkout).
        metadata: Metadatos adicionales para la sesión de checkout.
        success_url_extra_params: Parámetros adicionales para añadir a la URL de éxito (ej: "&order=123").
    
    Returns:
        URL del enlace de pago o None si hay un error.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se puede generar enlace de pago.")
        return None
        
    if not price_id:
         logger.error("Se requiere un price_id para generar el enlace de pago.")
         return None

    try:
        loop = asyncio.get_running_loop() # Usar get_running_loop en Python 3.7+
        
        # Construir URL de éxito con parámetros opcionales
        success_url = f"{settings.STRIPE_LINK_SUCCESS}?session_id={{CHECKOUT_SESSION_ID}}"
        if success_url_extra_params:
             success_url += success_url_extra_params
             
        # Crear sesión de pago usando run_in_executor
        checkout_session = await loop.run_in_executor(
            None, # Usa el executor por defecto (ThreadPoolExecutor)
            stripe.checkout.Session.create,
            payment_method_types=["card", "paypal"], # Añadir más métodos si se desea
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=settings.STRIPE_LINK_CANCEL,
            customer_email=customer_email,
            metadata=metadata or {}, # Asegurar que metadata sea un dict
            # client_reference_id está deprecado, usar metadata
            # client_reference_id=metadata.get("patient_id") if metadata else None 
        )
        
        logger.info(f"Enlace de pago generado para Price ID {price_id}. Session ID: {checkout_session.id}")
        return checkout_session.url
    
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al generar enlace de pago para Price ID {price_id}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error inesperado al generar enlace de pago para Price ID {price_id}: {e}")
        return None

async def check_payment_status(session_id: str) -> Dict[str, Any]:
    """
    Verifica el estado de una sesión de Stripe Checkout de forma asíncrona.
    
    Args:
        session_id: ID de la sesión de pago.
    
    Returns:
        Diccionario con información del estado del pago o un diccionario de error.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se puede verificar el estado del pago.")
        return {"success": False, "error": "Stripe API key no configurada"}
        
    try:
        loop = asyncio.get_running_loop()
        
        # Recuperar la sesión
        session = await loop.run_in_executor(
            None, 
            stripe.checkout.Session.retrieve, 
            session_id, 
            expand=['payment_intent'] # Expandir para obtener info del PaymentIntent
        )
        
        payment_intent = session.payment_intent # Ya está expandido
        
        logger.info(f"Estado de sesión {session_id}: status={session.status}, payment_status={session.payment_status}")
        
        return {
            "success": True,
            "session_id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total / 100 if session.amount_total else None,
            "currency": session.currency,
            "customer_email": session.customer_details.email if session.customer_details else session.customer_email, # Usar customer_details si está disponible
            "payment_intent_id": payment_intent.id if payment_intent else None,
            "payment_intent_status": payment_intent.status if payment_intent else None,
            "created": datetime.fromtimestamp(session.created).isoformat() if session.created else None,
            "metadata": session.metadata
        }
    
    except stripe.error.InvalidRequestError as e:
         logger.warning(f"Error al verificar estado de pago (probablemente sesión inválida {session_id}): {e}")
         return {"success": False, "error": "Sesión de pago no encontrada o inválida", "details": str(e)}
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al verificar estado de pago {session_id}: {e}")
        return {"success": False, "error": "Error de Stripe", "details": str(e)}
    except Exception as e:
        logger.exception(f"Error inesperado al verificar estado de pago {session_id}: {e}")
        return {"success": False, "error": "Error inesperado", "details": str(e)}

async def get_payment_link_for_category(category: str, patient_id: Optional[str] = None, patient_email: Optional[str] = None) -> Optional[str]:
    """
    Obtiene el enlace de pago para una categoría específica usando Price IDs predefinidos.
    
    Args:
        category: Categoría del paciente ('standard', 'pareja', 'reducida').
        patient_id: ID del paciente (para metadata).
        patient_email: Email del paciente (para pre-rellenar checkout).
    
    Returns:
        URL del enlace de pago o None si hay error o categoría inválida.
    """
    logger.info(f"Obteniendo enlace de pago para categoría: {category}, Paciente: {patient_id}")
    
    # Determinar Price ID según la categoría
    price_id = None
    if category == "standard":
        price_id = settings.STRIPE_PRICE_ID_STANDARD
    elif category == "pareja":
        price_id = settings.STRIPE_PRICE_ID_PAREJA
    elif category == "reducida":
        price_id = settings.STRIPE_PRICE_ID_REDUCIDA
    else:
        logger.error(f"Categoría de pago desconocida: {category}")
        return None # O manejar como error
        
    if not price_id:
         logger.error(f"No se encontró Price ID en la configuración para la categoría: {category}")
         return None

    # Crear metadata
    metadata = {
        "payment_type": "session",
        "category": category,
        "patient_id": str(patient_id) if patient_id else "unknown"
    }
    
    # Generar enlace de pago (ahora async)
    payment_link_url = await generate_payment_link(
        price_id=price_id,
        customer_email=patient_email,
        metadata=metadata
        # Puedes añadir parámetros extra a la URL de éxito si es necesario
        # success_url_extra_params=f"&patient={patient_id}"
    )
    
    return payment_link_url

async def get_payment_link_for_cancellation(patient_id: Optional[str] = None, patient_email: Optional[str] = None) -> Optional[str]:
    """
    Obtiene el enlace de pago para el cargo por cancelación.
    
    Returns:
        URL del enlace de pago o None si hay error.
    """
    logger.info(f"Obteniendo enlace de pago por cancelación. Paciente: {patient_id}")
    
    price_id = settings.STRIPE_PRICE_ID_CANCELLATION
    if not price_id:
        logger.error("STRIPE_PRICE_ID_CANCELLATION no está configurado.")
        return None

    # Crear metadata
    metadata = {
        "payment_type": "cancellation_fee",
        "patient_id": str(patient_id) if patient_id else "unknown"
    }

    payment_link_url = await generate_payment_link(
        price_id=price_id,
        customer_email=patient_email,
        metadata=metadata
    )
    
    return payment_link_url

async def create_customer(
    email: str,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Crea un cliente en Stripe de forma asíncrona.
    
    Args:
        email: Email del cliente.
        name: Nombre del cliente (opcional).
        phone: Teléfono del cliente (opcional).
        metadata: Metadatos adicionales.
    
    Returns:
        Diccionario con información del cliente creado o un diccionario de error.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se puede crear cliente.")
        return {"success": False, "error": "Stripe API key no configurada"}

    try:
        loop = asyncio.get_running_loop()
        customer = await loop.run_in_executor(
            None,
            stripe.Customer.create,
            email=email,
            name=name,
            phone=phone,
            metadata=metadata or {}
        )
        
        logger.info(f"Cliente creado en Stripe con ID: {customer.id} para email {email}")
        return {
            "success": True,
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "phone": customer.phone,
            "created": datetime.fromtimestamp(customer.created).isoformat() if customer.created else None,
            "metadata": customer.metadata
        }
    
    except stripe.error.InvalidRequestError as e:
         # Podría ser un email duplicado si ya existe
         logger.warning(f"Error de Stripe al crear cliente (posible duplicado para {email}?): {e}")
         # Podrías intentar buscar el cliente existente aquí si es necesario
         return {"success": False, "error": "Error de solicitud Stripe", "details": str(e)}
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al crear cliente para {email}: {e}")
        return {"success": False, "error": "Error de Stripe", "details": str(e)}
    except Exception as e:
        logger.exception(f"Error inesperado al crear cliente para {email}: {e}")
        return {"success": False, "error": "Error inesperado", "details": str(e)}

async def create_subscription(
    customer_id: str,
    price_id: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Crea una suscripción para un cliente de forma asíncrona.
    
    Args:
        customer_id: ID del cliente de Stripe.
        price_id: ID del precio de Stripe.
        metadata: Metadatos adicionales para la suscripción.
    
    Returns:
        Diccionario con información de la suscripción creada o un diccionario de error.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se puede crear suscripción.")
        return {"success": False, "error": "Stripe API key no configurada"}

    try:
        loop = asyncio.get_running_loop()
        subscription = await loop.run_in_executor(
            None,
            stripe.Subscription.create,
            customer=customer_id,
            items=[{"price": price_id}],
            metadata=metadata or {},
            # Considerar añadir: payment_behavior='default_incomplete' si se requiere acción del usuario
            # expand=['latest_invoice.payment_intent'] # Si necesitas el estado del primer pago
        )
        
        logger.info(f"Suscripción creada en Stripe con ID: {subscription.id} para cliente {customer_id}")
        return {
            "success": True,
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "metadata": subscription.metadata
            # "latest_invoice_id": subscription.latest_invoice.id if hasattr(subscription.latest_invoice, 'id') else None,
            # "payment_intent_status": subscription.latest_invoice.payment_intent.status if ... else None
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al crear suscripción para cliente {customer_id} y precio {price_id}: {e}")
        return {"success": False, "error": "Error de Stripe", "details": str(e)}
    except Exception as e:
        logger.exception(f"Error inesperado al crear suscripción para cliente {customer_id}: {e}")
        return {"success": False, "error": "Error inesperado", "details": str(e)}

async def get_product_prices(product_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene los precios asociados a un producto de forma asíncrona.
    
    Args:
        product_id: ID del producto de Stripe.
    
    Returns:
        Lista de diccionarios con información de precios o lista vacía en caso de error.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se pueden obtener precios.")
        return []
        
    try:
        loop = asyncio.get_running_loop()
        prices = await loop.run_in_executor(
            None,
            stripe.Price.list,
            product=product_id,
            active=True # Solo obtener precios activos por defecto?
        )
        
        result = []
        for price in prices.data:
            result.append({
                "id": price.id,
                "product": price.product,
                "currency": price.currency,
                "unit_amount": price.unit_amount / 100 if price.unit_amount else None,
                "nickname": price.nickname,
                "active": price.active,
                "type": price.type,
                "recurring": price.recurring.interval if price.recurring else None, # Extraer intervalo
                "interval_count": price.recurring.interval_count if price.recurring else None
            })
        
        logger.info(f"Obtenidos {len(result)} precios para producto {product_id}")
        return result
    
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al obtener precios para producto {product_id}: {e}")
        return []
    except Exception as e:
        logger.exception(f"Error inesperado al obtener precios para producto {product_id}: {e}")
        return []

async def handle_stripe_webhook(payload: bytes, signature: str) -> Dict[str, Any]: # Recibe payload y signature
    """
    Procesa un webhook de Stripe de forma asíncrona.
    Verifica la firma y maneja eventos específicos.
    
    Args:
        payload: El cuerpo raw de la solicitud del webhook (bytes).
        signature: El valor de la cabecera 'Stripe-Signature'.
        
    Returns:
        Diccionario indicando éxito o error en el procesamiento.
    """
    if not stripe.api_key:
        logger.error("Stripe API key no está configurada. No se puede procesar webhook.")
        return {"success": False, "error": "Stripe API key no configurada"}
        
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET no está configurado. No se puede verificar webhook.")
        return {"success": False, "error": "Webhook secret no configurado"}
        
    if not payload or not signature:
        logger.warning("Webhook de Stripe recibido sin payload o signature.")
        return {"success": False, "error": "Payload o signature faltante"}

    try:
        loop = asyncio.get_running_loop()
        # La verificación de firma es bloqueante
        event = await loop.run_in_executor(
            None,
            stripe.Webhook.construct_event,
            payload, signature, webhook_secret
        )
        
    except ValueError as e:
        # Payload inválido
        logger.error(f"Error en payload de webhook Stripe: {e}")
        return {"success": False, "error": "Payload inválido"}
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        logger.error(f"Error en firma de webhook Stripe: {e}")
        return {"success": False, "error": "Firma inválida"}
    except Exception as e:
         logger.exception(f"Error inesperado durante construct_event de Stripe: {e}")
         return {"success": False, "error": "Error al construir evento"}
        
    # Procesar el evento según su tipo
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    event_id = event.get("id")

    logger.info(f"Webhook de Stripe recibido y verificado. Event ID: {event_id}, Type: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            session_id = event_data.get("id")
            customer_email = event_data.get("customer_details", {}).get("email")
            amount_total = event_data.get("amount_total")
            payment_status = event_data.get("payment_status")
            metadata = event_data.get("metadata", {})
            patient_id = metadata.get("patient_id")
            category = metadata.get("category")
            payment_type = metadata.get("payment_type", "unknown")
            
            logger.info(f"Checkout Session {session_id} completada por {customer_email}. Total: {amount_total/100 if amount_total else 'N/A'} {event_data.get('currency')}. Status: {payment_status}. Tipo: {payment_type}, Paciente: {patient_id}, Cat: {category}")
            
            # Aquí lógica de negocio: registrar pago, actualizar estado paciente, etc.
            # Ejemplo: await mark_payment_completed_in_db(session_id, patient_id, amount_total, metadata)
            
            # Enviar notificación (asíncrona, no bloquear el webhook)
            if payment_status == "paid" and settings.EMERGENCY_CONTACT:
                 try:
                     # Importar aquí para evitar dependencia circular global
                     from services.whatsapp import send_whatsapp_message 
                     notification_message = f"Pago '{payment_type}' recibido: {amount_total/100 if amount_total else 'N/A'} EUR de {customer_email} (Paciente: {patient_id}, Cat: {category}). Sesión Stripe: {session_id}"
                     # Ejecutar en segundo plano para no esperar la respuesta de WhatsApp
                     asyncio.create_task(send_whatsapp_message(to=settings.EMERGENCY_CONTACT, message=notification_message))
                     logger.info(f"Notificación de pago para {session_id} enviada (en background).")
                 except Exception as notify_err:
                     logger.error(f"Error al intentar enviar notificación de pago para {session_id}: {notify_err}")
                     
        elif event_type == "payment_intent.succeeded":
            payment_intent = event_data
            logger.info(f"PaymentIntent {payment_intent.get('id')} exitoso.")
            # Lógica si necesitas manejar esto además de checkout.session.completed
        
        elif event_type == "payment_intent.payment_failed":
            payment_intent = event_data
            logger.warning(f"PaymentIntent {payment_intent.get('id')} fallido. Razón: {payment_intent.get('last_payment_error', {}).get('message')}")
            # Lógica para pagos fallidos
            
        # Añadir más manejadores de eventos aquí (ej. customer.subscription.*)
        
        else:
             logger.info(f"Evento Stripe no manejado específicamente: {event_type}")

        # Devolver éxito si el webhook fue procesado (incluso si el evento no se manejó)
        return {"success": True, "event_processed": event_type}

    except Exception as processing_error:
         # Error durante la lógica de negocio del evento
         logger.exception(f"Error al procesar lógica para evento Stripe {event_id} ({event_type}): {processing_error}")
         # Aún así, devolvemos éxito a Stripe para que no reintente el webhook,
         # pero registramos el error internamente.
         return {"success": True, "processing_error": str(processing_error), "event_processed": event_type} 