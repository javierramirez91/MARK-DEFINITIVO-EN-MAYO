# Servicios de Integración para Mark

Este módulo proporciona integraciones con servicios externos para el asistente virtual Mark del Centre de Psicologia Jaume I.

## Servicios Disponibles

### Calendly

Integración con Calendly para la gestión de citas y horarios disponibles.

```python
from services import calendly

# Obtener slots disponibles
slots = calendly.get_available_slots(
    start_date="2023-06-01",
    end_date="2023-06-15",
    therapist_id="therapist123"
)

# Programar una cita
appointment = calendly.schedule_appointment(
    slot_id="slot123",
    patient_name="Juan Pérez",
    patient_email="juan@example.com",
    patient_phone="+34612345678",
    appointment_type="initial",
    format="online"
)
```

### Stripe

Integración con Stripe para la gestión de pagos y facturación.

```python
from services import stripe

# Generar enlace de pago
payment_link = stripe.get_payment_link_for_category(
    category="individual",
    patient_id="patient123",
    patient_email="patient@example.com"
)

# Verificar estado de pago
payment_status = stripe.check_payment_status("cs_test_123456789")
```

### Zoom

Integración con Zoom para la gestión de videoconferencias.

```python
from services import zoom

# Crear reunión para terapia
meeting = zoom.create_therapy_meeting(
    patient_name="María García",
    start_datetime="2023-06-10 16:00",
    duration=60,
    therapist_name="Dr. Martínez",
    session_number=1,
    format_online=True
)

# Reprogramar reunión
updated_meeting = zoom.reschedule_therapy_meeting(
    meeting_id="123456789",
    new_start_datetime="2023-06-15 17:00"
)

# Cancelar reunión
cancelled = zoom.cancel_therapy_meeting("123456789")
```

## Configuración

Todas las integraciones utilizan las configuraciones definidas en `core.config.ApiConfig` y `core.config.ServiceConfig`. Asegúrate de que las siguientes variables de entorno estén configuradas:

### Calendly
- `CALENDLY_API_KEY`: API key de Calendly
- `CALENDLY_API_URL`: URL base de la API de Calendly (por defecto: "https://api.calendly.com")

### Stripe
- `STRIPE_API_KEY`: API key de Stripe
- `STRIPE_LINK_SUCCESS`: URL de redirección tras pago exitoso
- `STRIPE_LINK_CANCEL`: URL de redirección tras cancelación de pago
- `STRIPE_LINK_STANDARD`: URL de pago estándar (fallback)
- `STRIPE_LINK_PAREJA`: URL de pago para terapia de pareja (fallback)
- `STRIPE_LINK_REDUCIDA`: URL de pago para tarifa reducida (fallback)

### Zoom
- `ZOOM_CLIENT_ID`: Client ID de Zoom
- `ZOOM_CLIENT_SECRET`: Client Secret de Zoom
- `ZOOM_ACCOUNT_ID`: ID de la cuenta de Zoom
- `ZOOM_SECRET_TOKEN`: Token secreto para verificación de webhooks

## Manejo de Errores

Todas las integraciones incluyen manejo de errores robusto y logging detallado. Los errores se registran en el logger `mark-assistant.[service_name]` y las funciones devuelven valores por defecto o diccionarios con claves de error en caso de fallo.

## Extensibilidad

Para añadir nuevas integraciones, crea un nuevo archivo Python en el directorio `services/` y actualiza el archivo `__init__.py` para incluir el nuevo servicio. 