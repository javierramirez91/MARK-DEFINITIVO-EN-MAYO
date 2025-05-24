# Documentación de la API de Mark

Este documento proporciona información detallada sobre la API del asistente Mark, diseñado para el Centre de Psicologia Jaume I.

## Descripción general

La API de Mark proporciona endpoints para procesar mensajes, gestionar citas, manejar notificaciones y responder a situaciones de emergencia. Está construida con FastAPI y sigue los principios RESTful.

## Base URL

```
http://[host]:8000
```

## Autenticación

Actualmente, la API no requiere autenticación para los endpoints de webhook, ya que se validan mediante firmas o tokens específicos de cada servicio. Los endpoints internos están protegidos mediante restricciones de IP.

## Endpoints

### Procesamiento de mensajes

#### POST `/message`

Procesa un mensaje de texto y devuelve una respuesta generada.

**Solicitud:**

```json
{
  "user_id": "string",
  "message": "string",
  "language": "es",
  "session_id": "string"
}
```

**Respuesta:**

```json
{
  "response": "string",
  "session_id": "string",
  "playbook": "string"
}
```

**Códigos de estado:**
- `200 OK`: Mensaje procesado correctamente
- `400 Bad Request`: Parámetros inválidos
- `500 Internal Server Error`: Error en el procesamiento

### Webhook de WhatsApp

#### POST `/webhook/whatsapp`

Recibe y procesa webhooks de Twilio para mensajes de WhatsApp.

**Solicitud:**

Formato de formulario de Twilio con los siguientes campos principales:
- `From`: Número de teléfono del remitente
- `Body`: Contenido del mensaje
- `ProfileName`: Nombre del perfil del remitente
- `WaId`: ID de WhatsApp del remitente

**Respuesta:**

```xml
<Response></Response>
```

**Códigos de estado:**
- `200 OK`: Webhook procesado correctamente
- `400 Bad Request`: Parámetros inválidos
- `500 Internal Server Error`: Error en el procesamiento

### Gestión de citas

#### GET `/appointments/available`

Obtiene las franjas horarias disponibles para citas.

**Parámetros de consulta:**
- `start_date`: Fecha de inicio (YYYY-MM-DD)
- `end_date`: Fecha de fin (YYYY-MM-DD)
- `therapist_id`: ID del terapeuta (opcional)

**Respuesta:**

```json
{
  "slots": [
    {
      "start_time": "2023-06-01T10:00:00Z",
      "end_time": "2023-06-01T11:00:00Z",
      "therapist_id": "string",
      "therapist_name": "string"
    }
  ]
}
```

**Códigos de estado:**
- `200 OK`: Slots obtenidos correctamente
- `400 Bad Request`: Parámetros inválidos
- `500 Internal Server Error`: Error en la obtención de slots

#### POST `/appointments/schedule`

Programa una nueva cita.

**Solicitud:**

```json
{
  "user_id": "string",
  "slot_id": "string",
  "therapist_id": "string",
  "notes": "string",
  "service_type": "string"
}
```

**Respuesta:**

```json
{
  "appointment_id": "string",
  "start_time": "2023-06-01T10:00:00Z",
  "end_time": "2023-06-01T11:00:00Z",
  "therapist_name": "string",
  "confirmation_sent": true
}
```

**Códigos de estado:**
- `201 Created`: Cita programada correctamente
- `400 Bad Request`: Parámetros inválidos
- `409 Conflict`: La franja horaria ya no está disponible
- `500 Internal Server Error`: Error en la programación

### Notificaciones de emergencia

#### POST `/emergency`

Envía una notificación de emergencia.

**Solicitud:**

```json
{
  "user_id": "string",
  "message": "string",
  "severity": "high",
  "location": "string"
}
```

**Respuesta:**

```json
{
  "emergency_id": "string",
  "status": "notified",
  "timestamp": "2023-06-01T10:00:00Z",
  "contact_notified": true
}
```

**Códigos de estado:**
- `200 OK`: Emergencia notificada correctamente
- `400 Bad Request`: Parámetros inválidos
- `500 Internal Server Error`: Error en la notificación

### Estado del sistema

#### GET `/health`

Verifica el estado del sistema.

**Respuesta:**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "connected",
    "claude": "connected",
    "twilio": "connected"
  }
}
```

**Códigos de estado:**
- `200 OK`: Sistema funcionando correctamente
- `500 Internal Server Error`: Problemas en el sistema

## Modelos de datos

### Mensaje

```json
{
  "user_id": "string",
  "message": "string",
  "language": "string",
  "session_id": "string",
  "timestamp": "string",
  "metadata": {}
}
```

### Mensaje de WhatsApp

```json
{
  "from": "string",
  "body": "string",
  "profile_name": "string",
  "wa_id": "string",
  "media_url": "string",
  "media_type": "string"
}
```

### Solicitud de cita

```json
{
  "user_id": "string",
  "slot_id": "string",
  "therapist_id": "string",
  "notes": "string",
  "service_type": "string",
  "language": "string"
}
```

### Notificación de emergencia

```json
{
  "user_id": "string",
  "message": "string",
  "severity": "string",
  "location": "string",
  "timestamp": "string"
}
```

## Ejemplos de uso

### Enviar un mensaje

```bash
curl -X POST "http://localhost:8000/message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "12345",
    "message": "Hola, quisiera programar una cita",
    "language": "es",
    "session_id": "session_12345"
  }'
```

### Obtener franjas horarias disponibles

```bash
curl -X GET "http://localhost:8000/appointments/available?start_date=2023-06-01&end_date=2023-06-07"
```

### Programar una cita

```bash
curl -X POST "http://localhost:8000/appointments/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "12345",
    "slot_id": "slot_67890",
    "therapist_id": "therapist_123",
    "notes": "Primera visita",
    "service_type": "terapia_individual"
  }'
```

### Enviar una notificación de emergencia

```bash
curl -X POST "http://localhost:8000/emergency" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "12345",
    "message": "Necesito ayuda urgente",
    "severity": "high",
    "location": "Girona"
  }'
```

## Manejo de errores

La API devuelve errores en el siguiente formato:

```json
{
  "error": "string",
  "detail": "string",
  "timestamp": "string",
  "code": "string"
}
```

## Límites de tasa

Actualmente, la API no implementa límites de tasa estrictos, pero se recomienda no exceder las 100 solicitudes por minuto para evitar degradación del servicio.

## Contacto

Para problemas técnicos con la API, contactar con el equipo de desarrollo:

- **Email**: soporte@centrejaume1.com
- **Teléfono**: +34 600 000 000 