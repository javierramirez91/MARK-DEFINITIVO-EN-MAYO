# Mejoras de Seguridad en Mark

Este documento detalla las mejoras de seguridad implementadas en el asistente Mark para proteger la información sensible de los pacientes y garantizar la confidencialidad de las conversaciones.

## Cifrado de Extremo a Extremo

### Descripción General

El sistema de cifrado de extremo a extremo (E2E) implementado en Mark proporciona una capa adicional de seguridad para todas las conversaciones con pacientes. Este sistema garantiza que solo el paciente y los profesionales autorizados puedan acceder al contenido de las conversaciones, incluso si los servidores o bases de datos fueran comprometidos.

### Arquitectura del Sistema de Cifrado

El sistema utiliza un enfoque híbrido que combina cifrado asimétrico (RSA) y simétrico (AES-GCM):

1. **Cifrado Asimétrico (RSA)**: 
   - Se utiliza para el intercambio seguro de claves simétricas
   - Cada usuario tiene un par de claves (pública/privada)
   - Las claves RSA son de 2048 bits para garantizar seguridad a largo plazo

2. **Cifrado Simétrico (AES-GCM)**:
   - Se utiliza para cifrar el contenido de los mensajes
   - Utiliza AES-256-GCM, que proporciona confidencialidad y autenticación
   - Cada conversación utiliza un nonce único para prevenir ataques de repetición

### Flujo de Cifrado

1. **Registro de Usuario**:
   - Cuando un nuevo paciente se registra, se genera un par de claves RSA
   - La clave pública se almacena en el servidor
   - La clave privada se almacena de forma segura en el dispositivo del paciente

2. **Establecimiento de Sesión**:
   - Se genera una clave simétrica AES única para cada conversación
   - Esta clave se cifra con la clave pública del paciente
   - Solo el paciente, con su clave privada, puede descifrar esta clave simétrica

3. **Intercambio de Mensajes**:
   - Cada mensaje se cifra con la clave simétrica AES
   - Los mensajes cifrados se transmiten y almacenan en este formato
   - Solo las partes con acceso a la clave simétrica pueden descifrar los mensajes

4. **Rotación de Claves**:
   - Las claves simétricas se rotan automáticamente cada 90 días (configurable)
   - La rotación de claves limita el impacto potencial de una clave comprometida
   - El historial de claves se mantiene para acceder a conversaciones antiguas

### Implementación Técnica

El sistema está implementado en el módulo `ai/security/encryption.py` y proporciona las siguientes funcionalidades:

- Generación y gestión de pares de claves RSA
- Cifrado y descifrado de claves simétricas
- Cifrado y descifrado de mensajes individuales
- Cifrado y descifrado de conversaciones completas
- Rotación automática de claves
- Registro y auditoría de operaciones de cifrado

## Sistema de Detección de Amenazas

### Descripción General

El sistema de detección de amenazas está diseñado para identificar situaciones donde un paciente podría representar un peligro para sí mismo o para otros. Este sistema analiza los mensajes en tiempo real y alerta a los profesionales cuando se detectan indicadores de riesgo.

### Características Principales

1. **Detección Multilingüe**:
   - Reconoce indicadores de riesgo en español, catalán, inglés y árabe
   - Utiliza diccionarios específicos para cada idioma
   - Considera expresiones idiomáticas y coloquiales

2. **Análisis de Severidad**:
   - Evalúa el nivel de riesgo en una escala de 1 a 5
   - Considera la inmediatez y especificidad de las amenazas
   - Utiliza Claude para un análisis contextual más profundo

3. **Categorización de Riesgos**:
   - Autolesión y suicidio
   - Daño a terceros
   - Abuso o negligencia
   - Crisis emocional aguda

4. **Protocolos de Respuesta**:
   - Respuestas inmediatas para situaciones de alto riesgo
   - Notificaciones automáticas a profesionales
   - Escalamiento basado en la severidad detectada

### Implementación Técnica

El sistema está implementado en el módulo `ai/security/threat_detection.py` y proporciona:

- Análisis de mensajes en tiempo real
- Evaluación de severidad con Claude
- Determinación de estrategias de respuesta
- Registro de incidentes para seguimiento

## Integración con el Panel de Administración

Las mejoras de seguridad están completamente integradas con el panel de administración, proporcionando a Dina y otros profesionales autorizados las siguientes capacidades:

1. **Gestión de Claves**:
   - Visualización del estado de las claves
   - Rotación manual de claves cuando sea necesario
   - Configuración de políticas de rotación automática

2. **Monitoreo de Seguridad**:
   - Registro de accesos a datos sensibles
   - Alertas de seguridad en tiempo real
   - Estadísticas de incidentes de seguridad

3. **Auditoría y Cumplimiento**:
   - Registros detallados de todas las operaciones de seguridad
   - Informes de cumplimiento normativo
   - Exportación de registros para auditorías externas

## Configuración y Personalización

Las mejoras de seguridad pueden configurarse a través de variables de entorno:

```
# Cifrado
ENCRYPTION_KEY=clave_maestra_muy_segura
KEY_ROTATION_DAYS=90
ENCRYPTION_ALGORITHM=AES-256-GCM

# Detección de amenazas
THREAT_DETECTION_ENABLED=true
THREAT_NOTIFICATION_EMAIL=emergencias@centrepsicologiajaume1.com
THREAT_NOTIFICATION_PHONE=+34637885915
```

## Consideraciones de Privacidad y Cumplimiento

Las mejoras implementadas están diseñadas para cumplir con:

- Reglamento General de Protección de Datos (RGPD)
- Ley Orgánica de Protección de Datos y Garantía de Derechos Digitales (LOPDGDD)
- Estándares de seguridad para información sanitaria

## Limitaciones y Trabajo Futuro

- Implementación de autenticación de múltiples factores (MFA)
- Integración con sistemas de detección de intrusiones (IDS)
- Expansión de la detección de amenazas a más idiomas y dialectos
- Implementación de análisis de comportamiento para detección de anomalías 