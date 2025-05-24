# Seguridad y Privacidad en el Asistente Mark

Este documento describe las medidas de seguridad y privacidad implementadas en el asistente Mark para proteger los datos de los pacientes y cumplir con las regulaciones aplicables.

## Cumplimiento Normativo

El asistente Mark está diseñado para cumplir con las siguientes regulaciones:

### RGPD (Reglamento General de Protección de Datos)

- **Consentimiento informado**: Se obtiene consentimiento explícito de los pacientes antes de procesar sus datos.
- **Minimización de datos**: Solo se recopilan los datos estrictamente necesarios para proporcionar el servicio.
- **Derechos ARCO**: Se implementan mecanismos para que los pacientes puedan ejercer sus derechos de Acceso, Rectificación, Cancelación y Oposición.
- **Registro de actividades**: Se mantiene un registro de todas las actividades de procesamiento de datos.

### LOPDGDD (Ley Orgánica de Protección de Datos y Garantía de Derechos Digitales)

- **Adaptación al marco español**: Cumplimiento específico con la legislación española sobre protección de datos.
- **Medidas de seguridad**: Implementación de medidas técnicas y organizativas adecuadas según el nivel de sensibilidad de los datos.

### Código Deontológico de Psicología

- **Confidencialidad profesional**: Respeto estricto a la confidencialidad de la información proporcionada por los pacientes.
- **Secreto profesional**: Protección de la información obtenida en el contexto terapéutico.

## Medidas de Seguridad Técnicas

### Encriptación de Datos

#### Datos en Tránsito
- **TLS/SSL**: Todas las comunicaciones entre el cliente y el servidor utilizan TLS 1.3.
- **HTTPS**: Todas las API y webhooks requieren conexiones HTTPS.
- **Certificados**: Se utilizan certificados SSL válidos y actualizados.

#### Datos en Reposo
- **Encriptación de base de datos**: Los datos almacenados en Cloudflare D1 están encriptados.
- **Encriptación de campos sensibles**: Información personal identificable (PII) adicional se encripta a nivel de campo usando AES-256.

```python
# Ejemplo de encriptación de datos sensibles
def encrypt_sensitive_data(data: str, key: bytes) -> str:
    """
    Encripta datos sensibles usando AES-256-GCM
    
    Args:
        data: Datos a encriptar
        key: Clave de encriptación
        
    Returns:
        Datos encriptados en formato base64
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import os
    import base64
    
    # Generar nonce aleatorio
    nonce = os.urandom(12)
    
    # Crear cifrador
    aesgcm = AESGCM(key)
    
    # Encriptar datos
    ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    
    # Combinar nonce y texto cifrado y codificar en base64
    encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')
    
    return encrypted
```

### Autenticación y Autorización

- **JWT**: Se utilizan tokens JWT para autenticar solicitudes a la API.
- **Expiración de sesiones**: Las sesiones tienen un tiempo de vida limitado.
- **Control de acceso basado en roles**: Diferentes niveles de acceso según el rol del usuario.

### Auditoría y Logging

Se implementa un sistema completo de auditoría que registra:

- **Accesos a datos**: Quién accedió a qué datos y cuándo.
- **Modificaciones**: Cambios realizados en los datos de pacientes.
- **Intentos fallidos**: Intentos fallidos de autenticación o acceso no autorizado.

```python
# Ejemplo de función de auditoría
async def log_data_access(
    user_id: str,
    patient_id: str,
    action: str,
    details: str,
    success: bool
) -> None:
    """
    Registra un acceso a datos en el log de auditoría
    
    Args:
        user_id: ID del usuario que realiza la acción
        patient_id: ID del paciente cuyos datos se acceden
        action: Tipo de acción (read, write, delete)
        details: Detalles adicionales
        success: Si la acción fue exitosa
    """
    from datetime import datetime
    
    audit_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "patient_id": patient_id,
        "action": action,
        "details": details,
        "success": success,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent", "")
    }
    
    # Guardar en la base de datos
    await database.execute_query(
        "INSERT INTO audit_logs (id, timestamp, user_id, patient_id, action, details, success, ip_address, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [audit_entry["id"], audit_entry["timestamp"], audit_entry["user_id"], audit_entry["patient_id"], 
         audit_entry["action"], audit_entry["details"], audit_entry["success"], 
         audit_entry["ip_address"], audit_entry["user_agent"]]
    )
    
    # Registrar en el log del sistema
    logger.info(f"AUDIT: {action} on patient {patient_id} by user {user_id}: {'SUCCESS' if success else 'FAILURE'}")
```

## Gestión de Datos de Pacientes

### Ciclo de Vida de los Datos

1. **Recopilación**: Solo se recopilan datos necesarios para el servicio.
2. **Procesamiento**: Los datos se procesan de acuerdo con finalidades específicas y legítimas.
3. **Almacenamiento**: Los datos se almacenan de forma segura y encriptada.
4. **Eliminación**: Los datos se eliminan cuando ya no son necesarios o a petición del paciente.

### Retención de Datos

- **Política de retención**: Los datos de pacientes se conservan durante el tiempo legalmente requerido para historias clínicas (5 años desde la última atención).
- **Anonimización**: Después del período de retención, los datos se anonimizan para fines estadísticos.

## Seguridad en Integraciones

### Twilio (WhatsApp)

- **Verificación de firmas**: Se verifican las firmas de los webhooks de Twilio.
- **Tokens seguros**: Las credenciales de API se almacenan de forma segura.
- **Mensajes encriptados**: Los mensajes se transmiten a través de canales encriptados.

### Claude (Anthropic)

- **Minimización de datos**: Se envía la mínima información necesaria a la API de Claude.
- **Sin almacenamiento persistente**: No se permite a Claude almacenar conversaciones.
- **Anonimización**: Se anonimizan datos identificables antes de enviarlos a Claude.

## Plan de Respuesta a Incidentes

### Detección

- **Monitoreo continuo**: Sistemas automatizados para detectar actividades sospechosas.
- **Alertas**: Notificaciones inmediatas sobre posibles brechas de seguridad.

### Contención y Mitigación

- **Aislamiento**: Procedimientos para aislar sistemas comprometidos.
- **Revocación de accesos**: Capacidad para revocar tokens y credenciales comprometidas.

### Notificación

- **A autoridades**: Procedimiento para notificar a la AEPD dentro de las 72 horas.
- **A afectados**: Protocolo para informar a los pacientes afectados.

## Evaluación de Impacto (EIPD)

Se ha realizado una Evaluación de Impacto en la Protección de Datos que incluye:

1. **Descripción sistemática** de las operaciones de tratamiento.
2. **Evaluación de la necesidad y proporcionalidad** de las operaciones.
3. **Evaluación de los riesgos** para los derechos y libertades de los pacientes.
4. **Medidas previstas** para afrontar los riesgos.

## Recomendaciones para Usuarios

### Para Pacientes

- Utilizar contraseñas seguras y únicas.
- No compartir información sensible a través de canales no seguros.
- Cerrar sesión después de usar dispositivos compartidos.
- Verificar la autenticidad de los mensajes recibidos.

### Para Terapeutas

- Mantener actualizados los sistemas operativos y aplicaciones.
- Utilizar autenticación de dos factores.
- No acceder a datos de pacientes desde redes públicas no seguras.
- Reportar inmediatamente cualquier actividad sospechosa.

## Contacto para Asuntos de Privacidad

Para cualquier consulta relacionada con la privacidad y protección de datos:

- **Email**: privacidad@centrejaume1.com
- **Teléfono**: +34 600 000 000
- **Dirección**: Gran Via Jaume I, 41-43, entresuelo 1a, 17001, Girona, España

## Actualizaciones de la Política

Esta política se revisa y actualiza regularmente. Los cambios significativos se notificarán a los pacientes a través de los canales de comunicación habituales. 