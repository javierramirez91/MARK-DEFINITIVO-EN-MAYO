# API Documentation

This document provides comprehensive documentation for the Mark Assistant API, which allows developers to integrate with and extend the functionality of the Mark system.

## API Overview

The Mark Assistant API is a RESTful API that uses JSON for request and response payloads. The API is secured using JWT (JSON Web Tokens) for authentication.

### Base URL

- **Production**: `https://your-domain.com/api/v1`
- **Development**: `http://localhost:8000/api/v1`

### Authentication

All API requests (except for the authentication endpoints) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To obtain a JWT token, use the authentication endpoint:

```
POST /auth/token
```

With the following payload:

```json
{
  "username": "your_api_username",
  "password": "your_api_password"
}
```

The response will include a JWT token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Tokens expire after 1 hour (3600 seconds) by default.

### Rate Limiting

The API implements rate limiting to prevent abuse. By default, the limits are:

- 60 requests per minute per IP address
- 1000 requests per day per API key

When a rate limit is exceeded, the API will return a 429 Too Many Requests response.

### Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- 200: OK - The request was successful
- 201: Created - A new resource was successfully created
- 400: Bad Request - The request was malformed or invalid
- 401: Unauthorized - Authentication failed or token expired
- 403: Forbidden - The authenticated user does not have permission
- 404: Not Found - The requested resource was not found
- 429: Too Many Requests - Rate limit exceeded
- 500: Internal Server Error - An error occurred on the server

Error responses include a JSON payload with details:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid",
    "details": "The 'patient_id' field is required"
  }
}
```

## API Endpoints

### Patients

#### List Patients

```
GET /patients
```

Query parameters:
- `page`: Page number (default: 1)
- `limit`: Number of results per page (default: 20, max: 100)
- `search`: Search term to filter by name or phone number
- `status`: Filter by status (active, inactive)
- `language`: Filter by preferred language

Response:

```json
{
  "total": 125,
  "page": 1,
  "limit": 20,
  "data": [
    {
      "id": "pat_123456",
      "name": "John Doe",
      "phone_number": "+34612345678",
      "email": "john.doe@example.com",
      "registration_date": "2023-01-15T10:30:00Z",
      "last_activity": "2023-05-20T14:45:00Z",
      "preferred_language": "es",
      "status": "active"
    },
    // More patients...
  ]
}
```

#### Get Patient

```
GET /patients/{patient_id}
```

Response:

```json
{
  "id": "pat_123456",
  "name": "John Doe",
  "phone_number": "+34612345678",
  "email": "john.doe@example.com",
  "registration_date": "2023-01-15T10:30:00Z",
  "last_activity": "2023-05-20T14:45:00Z",
  "preferred_language": "es",
  "status": "active",
  "notes": "Prefers evening appointments",
  "metadata": {
    "source": "website",
    "referral": "google"
  }
}
```

#### Create Patient

```
POST /patients
```

Request:

```json
{
  "name": "Jane Smith",
  "phone_number": "+34698765432",
  "email": "jane.smith@example.com",
  "preferred_language": "en",
  "notes": "New patient referred by Dr. Garcia",
  "metadata": {
    "source": "referral"
  }
}
```

Response:

```json
{
  "id": "pat_789012",
  "name": "Jane Smith",
  "phone_number": "+34698765432",
  "email": "jane.smith@example.com",
  "registration_date": "2023-06-01T09:15:00Z",
  "last_activity": "2023-06-01T09:15:00Z",
  "preferred_language": "en",
  "status": "active",
  "notes": "New patient referred by Dr. Garcia",
  "metadata": {
    "source": "referral"
  }
}
```

#### Update Patient

```
PUT /patients/{patient_id}
```

Request:

```json
{
  "name": "Jane Smith-Johnson",
  "email": "jane.smith.johnson@example.com",
  "preferred_language": "ca",
  "status": "active",
  "notes": "Updated contact information"
}
```

Response:

```json
{
  "id": "pat_789012",
  "name": "Jane Smith-Johnson",
  "phone_number": "+34698765432",
  "email": "jane.smith.johnson@example.com",
  "registration_date": "2023-06-01T09:15:00Z",
  "last_activity": "2023-06-01T10:30:00Z",
  "preferred_language": "ca",
  "status": "active",
  "notes": "Updated contact information",
  "metadata": {
    "source": "referral"
  }
}
```

#### Delete Patient

```
DELETE /patients/{patient_id}
```

Response:

```json
{
  "success": true,
  "message": "Patient deleted successfully"
}
```

### Conversations

#### List Conversations

```
GET /conversations
```

Query parameters:
- `page`: Page number (default: 1)
- `limit`: Number of results per page (default: 20, max: 100)
- `patient_id`: Filter by patient ID
- `start_date`: Filter by start date (ISO 8601 format)
- `end_date`: Filter by end date (ISO 8601 format)
- `language`: Filter by language

Response:

```json
{
  "total": 250,
  "page": 1,
  "limit": 20,
  "data": [
    {
      "id": "conv_123456",
      "patient_id": "pat_123456",
      "patient_name": "John Doe",
      "start_time": "2023-05-20T14:30:00Z",
      "end_time": "2023-05-20T14:45:00Z",
      "language": "es",
      "message_count": 12,
      "summary": "Appointment scheduling and confirmation"
    },
    // More conversations...
  ]
}
```

#### Get Conversation

```
GET /conversations/{conversation_id}
```

Response:

```json
{
  "id": "conv_123456",
  "patient_id": "pat_123456",
  "patient_name": "John Doe",
  "start_time": "2023-05-20T14:30:00Z",
  "end_time": "2023-05-20T14:45:00Z",
  "language": "es",
  "messages": [
    {
      "id": "msg_123",
      "timestamp": "2023-05-20T14:30:00Z",
      "sender": "patient",
      "content": "Hola, quisiera programar una cita para la próxima semana",
      "content_type": "text"
    },
    {
      "id": "msg_124",
      "timestamp": "2023-05-20T14:31:00Z",
      "sender": "assistant",
      "content": "¡Hola! Claro, puedo ayudarte a programar una cita. ¿Qué día y hora te vendría mejor?",
      "content_type": "text"
    },
    // More messages...
  ],
  "metadata": {
    "intent": "appointment_scheduling",
    "sentiment": "positive",
    "escalated": false
  }
}
```

#### Export Conversation

```
GET /conversations/{conversation_id}/export
```

Query parameters:
- `format`: Export format (pdf, csv, json)

Response:
- For PDF: Binary file with Content-Type: application/pdf
- For CSV: Binary file with Content-Type: text/csv
- For JSON: JSON file with Content-Type: application/json

#### Delete Conversation

```
DELETE /conversations/{conversation_id}
```

Response:

```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

### Appointments

#### List Appointments

```
GET /appointments
```

Query parameters:
- `page`: Page number (default: 1)
- `limit`: Number of results per page (default: 20, max: 100)
- `patient_id`: Filter by patient ID
- `start_date`: Filter by start date (ISO 8601 format)
- `end_date`: Filter by end date (ISO 8601 format)
- `status`: Filter by status (scheduled, completed, canceled)

Response:

```json
{
  "total": 75,
  "page": 1,
  "limit": 20,
  "data": [
    {
      "id": "apt_123456",
      "patient_id": "pat_123456",
      "patient_name": "John Doe",
      "start_time": "2023-06-15T10:00:00Z",
      "end_time": "2023-06-15T11:00:00Z",
      "duration": 60,
      "type": "initial_consultation",
      "status": "scheduled",
      "notes": "First appointment"
    },
    // More appointments...
  ]
}
```

#### Get Appointment

```
GET /appointments/{appointment_id}
```

Response:

```json
{
  "id": "apt_123456",
  "patient_id": "pat_123456",
  "patient_name": "John Doe",
  "start_time": "2023-06-15T10:00:00Z",
  "end_time": "2023-06-15T11:00:00Z",
  "duration": 60,
  "type": "initial_consultation",
  "status": "scheduled",
  "notes": "First appointment",
  "location": "Online (Zoom)",
  "zoom_link": "https://zoom.us/j/123456789",
  "calendly_link": "https://calendly.com/event/123456789",
  "reminders": [
    {
      "type": "whatsapp",
      "time": "2023-06-14T10:00:00Z",
      "status": "sent"
    },
    {
      "type": "whatsapp",
      "time": "2023-06-15T09:30:00Z",
      "status": "pending"
    }
  ]
}
```

#### Create Appointment

```
POST /appointments
```

Request:

```json
{
  "patient_id": "pat_789012",
  "start_time": "2023-06-20T15:00:00Z",
  "duration": 60,
  "type": "initial_consultation",
  "notes": "New patient consultation",
  "location": "Online (Zoom)"
}
```

Response:

```json
{
  "id": "apt_789012",
  "patient_id": "pat_789012",
  "patient_name": "Jane Smith",
  "start_time": "2023-06-20T15:00:00Z",
  "end_time": "2023-06-20T16:00:00Z",
  "duration": 60,
  "type": "initial_consultation",
  "status": "scheduled",
  "notes": "New patient consultation",
  "location": "Online (Zoom)",
  "zoom_link": "https://zoom.us/j/987654321",
  "calendly_link": "https://calendly.com/event/987654321",
  "reminders": [
    {
      "type": "whatsapp",
      "time": "2023-06-19T15:00:00Z",
      "status": "pending"
    },
    {
      "type": "whatsapp",
      "time": "2023-06-20T14:30:00Z",
      "status": "pending"
    }
  ]
}
```

#### Update Appointment

```
PUT /appointments/{appointment_id}
```

Request:

```json
{
  "start_time": "2023-06-21T16:00:00Z",
  "duration": 45,
  "status": "rescheduled",
  "notes": "Rescheduled at patient's request"
}
```

Response:

```json
{
  "id": "apt_789012",
  "patient_id": "pat_789012",
  "patient_name": "Jane Smith",
  "start_time": "2023-06-21T16:00:00Z",
  "end_time": "2023-06-21T16:45:00Z",
  "duration": 45,
  "type": "initial_consultation",
  "status": "rescheduled",
  "notes": "Rescheduled at patient's request",
  "location": "Online (Zoom)",
  "zoom_link": "https://zoom.us/j/987654321",
  "calendly_link": "https://calendly.com/event/987654321",
  "reminders": [
    {
      "type": "whatsapp",
      "time": "2023-06-20T16:00:00Z",
      "status": "pending"
    },
    {
      "type": "whatsapp",
      "time": "2023-06-21T15:30:00Z",
      "status": "pending"
    }
  ]
}
```

#### Cancel Appointment

```
POST /appointments/{appointment_id}/cancel
```

Request:

```json
{
  "reason": "Patient unavailable",
  "notify_patient": true
}
```

Response:

```json
{
  "id": "apt_789012",
  "status": "canceled",
  "cancellation_time": "2023-06-18T09:30:00Z",
  "cancellation_reason": "Patient unavailable",
  "notification_sent": true
}
```

### Messages

#### Send Message

```
POST /messages
```

Request:

```json
{
  "patient_id": "pat_123456",
  "content": "Hello, this is a test message from the API",
  "content_type": "text"
}
```

Response:

```json
{
  "id": "msg_456789",
  "patient_id": "pat_123456",
  "timestamp": "2023-06-01T14:30:00Z",
  "sender": "system",
  "content": "Hello, this is a test message from the API",
  "content_type": "text",
  "status": "sent",
  "conversation_id": "conv_789012"
}
```

#### Send Voice Message

```
POST /messages/voice
```

Request (multipart/form-data):
- `patient_id`: Patient ID
- `audio_file`: Audio file (MP3, WAV, or OGG format)
- `language`: Language code (optional)

Response:

```json
{
  "id": "msg_567890",
  "patient_id": "pat_123456",
  "timestamp": "2023-06-01T14:35:00Z",
  "sender": "system",
  "content": "https://storage.example.com/voice-messages/msg_567890.mp3",
  "content_type": "voice",
  "status": "sent",
  "conversation_id": "conv_789012",
  "metadata": {
    "duration": 15,
    "format": "mp3",
    "transcription": "Hello, this is a test voice message from the API"
  }
}
```

### Analytics

#### Get Conversation Statistics

```
GET /analytics/conversations
```

Query parameters:
- `start_date`: Start date (ISO 8601 format)
- `end_date`: End date (ISO 8601 format)
- `interval`: Grouping interval (day, week, month)
- `language`: Filter by language (optional)

Response:

```json
{
  "total_conversations": 1250,
  "average_length": 8.5,
  "by_interval": [
    {
      "interval": "2023-05-01",
      "count": 42,
      "average_length": 7.8
    },
    {
      "interval": "2023-05-02",
      "count": 38,
      "average_length": 9.2
    },
    // More intervals...
  ],
  "by_language": [
    {
      "language": "es",
      "count": 850,
      "percentage": 68
    },
    {
      "language": "ca",
      "count": 200,
      "percentage": 16
    },
    {
      "language": "en",
      "count": 150,
      "percentage": 12
    },
    {
      "language": "ar",
      "count": 50,
      "percentage": 4
    }
  ],
  "by_hour": [
    {
      "hour": 0,
      "count": 15
    },
    // Hours 1-23...
  ]
}
```

#### Get Appointment Statistics

```
GET /analytics/appointments
```

Query parameters:
- `start_date`: Start date (ISO 8601 format)
- `end_date`: End date (ISO 8601 format)
- `interval`: Grouping interval (day, week, month)

Response:

```json
{
  "total_appointments": 450,
  "by_status": [
    {
      "status": "scheduled",
      "count": 150,
      "percentage": 33.3
    },
    {
      "status": "completed",
      "count": 250,
      "percentage": 55.6
    },
    {
      "status": "canceled",
      "count": 50,
      "percentage": 11.1
    }
  ],
  "by_type": [
    {
      "type": "initial_consultation",
      "count": 120,
      "percentage": 26.7
    },
    {
      "type": "follow_up",
      "count": 280,
      "percentage": 62.2
    },
    {
      "type": "emergency",
      "count": 50,
      "percentage": 11.1
    }
  ],
  "by_interval": [
    {
      "interval": "2023-05-01",
      "scheduled": 5,
      "completed": 8,
      "canceled": 2
    },
    // More intervals...
  ],
  "cancellation_reasons": [
    {
      "reason": "Patient unavailable",
      "count": 25,
      "percentage": 50
    },
    {
      "reason": "Therapist unavailable",
      "count": 15,
      "percentage": 30
    },
    {
      "reason": "Other",
      "count": 10,
      "percentage": 20
    }
  ]
}
```

#### Get Patient Statistics

```
GET /analytics/patients
```

Query parameters:
- `start_date`: Start date (ISO 8601 format)
- `end_date`: End date (ISO 8601 format)
- `interval`: Grouping interval (day, week, month)

Response:

```json
{
  "total_patients": 350,
  "active_patients": 280,
  "by_language": [
    {
      "language": "es",
      "count": 220,
      "percentage": 62.9
    },
    {
      "language": "ca",
      "count": 60,
      "percentage": 17.1
    },
    {
      "language": "en",
      "count": 50,
      "percentage": 14.3
    },
    {
      "language": "ar",
      "count": 20,
      "percentage": 5.7
    }
  ],
  "new_patients_by_interval": [
    {
      "interval": "2023-05-01",
      "count": 3
    },
    // More intervals...
  ],
  "engagement": {
    "highly_engaged": 120,
    "moderately_engaged": 100,
    "low_engagement": 60,
    "inactive": 70
  }
}
```

### System

#### Get System Status

```
GET /system/status
```

Response:

```json
{
  "status": "operational",
  "version": "1.5.2",
  "uptime": 1209600,
  "last_restart": "2023-05-15T00:00:00Z",
  "components": [
    {
      "name": "api",
      "status": "operational"
    },
    {
      "name": "database",
      "status": "operational"
    },
    {
      "name": "whatsapp_integration",
      "status": "operational"
    },
    {
      "name": "calendly_integration",
      "status": "operational"
    },
    {
      "name": "stripe_integration",
      "status": "operational"
    },
    {
      "name": "zoom_integration",
      "status": "operational"
    },
    {
      "name": "claude_api",
      "status": "operational"
    }
  ],
  "metrics": {
    "requests_per_minute": 42,
    "average_response_time": 120,
    "error_rate": 0.2
  }
}
```

#### Get Encryption Status

```
GET /system/encryption/status
```

Response:

```json
{
  "enabled": true,
  "key_rotation_days": 30,
  "last_rotation": "2023-05-15T00:00:00Z",
  "next_rotation": "2023-06-14T00:00:00Z",
  "encrypted_conversations": 1250,
  "encrypted_patients": 350
}
```

## Webhooks

Mark Assistant can send webhook notifications to your system when certain events occur. To configure webhooks, use the admin panel or the API.

### Configure Webhook

```
POST /webhooks
```

Request:

```json
{
  "url": "https://your-system.com/webhooks/mark",
  "secret": "your_webhook_secret",
  "events": [
    "conversation.created",
    "conversation.updated",
    "appointment.created",
    "appointment.updated",
    "appointment.canceled",
    "patient.created",
    "patient.updated"
  ]
}
```

Response:

```json
{
  "id": "wh_123456",
  "url": "https://your-system.com/webhooks/mark",
  "events": [
    "conversation.created",
    "conversation.updated",
    "appointment.created",
    "appointment.updated",
    "appointment.canceled",
    "patient.created",
    "patient.updated"
  ],
  "created_at": "2023-06-01T10:00:00Z",
  "status": "active"
}
```

### Webhook Payload

Webhook payloads are signed using HMAC-SHA256 with your webhook secret. The signature is included in the `X-Mark-Signature` header.

Example payload for `conversation.created`:

```json
{
  "id": "evt_123456",
  "type": "conversation.created",
  "created": "2023-06-01T14:30:00Z",
  "data": {
    "conversation_id": "conv_789012",
    "patient_id": "pat_123456",
    "start_time": "2023-06-01T14:30:00Z",
    "language": "es"
  }
}
```

## SDK Libraries

We provide official SDK libraries for easy integration with the Mark Assistant API:

- [Python SDK](https://github.com/centrepsicologiajaume/mark-assistant-python)
- [JavaScript SDK](https://github.com/centrepsicologiajaume/mark-assistant-js)
- [PHP SDK](https://github.com/centrepsicologiajaume/mark-assistant-php)

### Python Example

```python
from mark_assistant import MarkClient

# Initialize the client
client = MarkClient(api_key="your_api_key")

# Get a list of patients
patients = client.patients.list(limit=10)

# Send a message
message = client.messages.send(
    patient_id="pat_123456",
    content="Hello from the Python SDK!",
    content_type="text"
)

# Get appointment statistics
stats = client.analytics.appointments(
    start_date="2023-05-01",
    end_date="2023-05-31",
    interval="day"
)
```

### JavaScript Example

```javascript
import { MarkClient } from '@centrepsicologiajaume/mark-assistant';

// Initialize the client
const client = new MarkClient({ apiKey: 'your_api_key' });

// Get a list of patients
client.patients.list({ limit: 10 })
  .then(patients => console.log(patients))
  .catch(error => console.error(error));

// Send a message
client.messages.send({
  patient_id: 'pat_123456',
  content: 'Hello from the JavaScript SDK!',
  content_type: 'text'
})
  .then(message => console.log(message))
  .catch(error => console.error(error));

// Get appointment statistics
client.analytics.appointments({
  start_date: '2023-05-01',
  end_date: '2023-05-31',
  interval: 'day'
})
  .then(stats => console.log(stats))
  .catch(error => console.error(error));
```

## Best Practices

### Security

- Keep your API keys secure and never expose them in client-side code
- Rotate your API keys periodically
- Use HTTPS for all API requests
- Validate webhook signatures to ensure they come from Mark Assistant
- Implement proper error handling for API responses

### Performance

- Implement caching for frequently accessed data
- Use pagination for large result sets
- Minimize the number of API requests by batching operations when possible
- Set appropriate timeouts for API requests

### Rate Limiting

- Implement exponential backoff for rate limit errors
- Distribute API requests evenly over time
- Monitor your API usage to avoid hitting rate limits

## Support and Feedback

For API support or to provide feedback:

- Email: api-support@centrepsicologiajaumeprimer.com
- API Status Page: https://status.mark-assistant.com
- Developer Forum: https://developers.mark-assistant.com/forum

## Next Steps

After familiarizing yourself with the API, refer to the following documentation:

1. [Security Guide](05_security_guide.md)
2. [Customization Guide](06_customization_guide.md)
3. [Troubleshooting Guide](07_troubleshooting_guide.md) 