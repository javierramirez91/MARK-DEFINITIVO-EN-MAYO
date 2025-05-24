# Playbooks para Mark - Asistente del Centre de Psicologia Jaume I

Este directorio contiene los playbooks que definen el comportamiento del asistente virtual Mark para el Centre de Psicologia Jaume I. Cada playbook está diseñado para manejar diferentes aspectos de la interacción con los usuarios.

## Estructura de Playbooks

El sistema utiliza un selector de playbooks que analiza el contexto de la conversación para determinar qué playbook debe utilizarse en cada momento. Los playbooks disponibles son:

### Playbook 1: Identidad y Coherencia Lingüística
- **Archivo**: `playbook1.py`
- **Función**: Define la identidad básica de Mark, cómo debe presentarse y mantener coherencia en el idioma utilizado.
- **Características clave**: 
  - Presentación inicial adaptada al idioma del usuario
  - Mantenimiento del idioma inicial durante toda la conversación
  - Tono profesional, cálido y empático

### Playbook 2: Gestión de Crisis y Solicitudes a Dina
- **Archivo**: `playbook2.py`
- **Función**: Maneja situaciones de urgencia o crisis emocionales, así como solicitudes para hablar con Dina.
- **Características clave**:
  - Detección de palabras clave de crisis en múltiples idiomas
  - Respuestas inmediatas y empáticas
  - Protocolos para notificar a Dina en casos urgentes
  - Información de contacto de emergencia

### Playbook 3: Gestión de Citas y Pagos
- **Archivo**: `playbook3.py`
- **Función**: Administra la programación de citas, recordatorios, pagos y preguntas frecuentes.
- **Características clave**:
  - Recopilación de datos para la primera llamada
  - Programación de citas con terapeutas adecuados
  - Gestión de pagos y recordatorios automáticos
  - Seguimiento post-sesión y recopilación de feedback

### Playbook 4: Seguridad, Reportes y Ejemplos
- **Archivo**: `playbook4.py`
- **Función**: Gestiona la seguridad de datos, auditorías, reportes y ejemplos de interacción.
- **Características clave**:
  - Acceso exclusivo para Dina a funciones administrativas
  - Protección de datos confidenciales
  - Generación de reportes y auditorías
  - Ejemplos de interacción en diferentes escenarios

## Selector de Playbooks

El archivo `playbook_selector.py` contiene la lógica para seleccionar el playbook adecuado según el contexto de la conversación:

- **Detección de idioma**: Identifica el idioma utilizado por el usuario
- **Análisis de palabras clave**: Busca términos específicos que indiquen la necesidad de un playbook particular
- **Selección contextual**: Determina el playbook más adecuado basándose en el mensaje actual y el historial de conversación

## Uso

Para utilizar estos playbooks en el asistente Mark:

1. Importar el selector de playbooks:
```python
from ai.claude.prompts.playbook_selector import select_playbook, PlaybookType
```

2. Seleccionar el playbook adecuado según el mensaje del usuario:
```python
playbook_type, system_prompt = select_playbook(user_message, conversation_history)
```

3. Utilizar el prompt de sistema seleccionado para generar la respuesta con Claude:
```python
response = generate_claude_response(user_message, system_prompt=system_prompt)
```

## Mantenimiento

Al actualizar o modificar los playbooks, asegúrese de:

1. Mantener la coherencia entre los diferentes playbooks
2. Actualizar las palabras clave en el selector si se añaden nuevas funcionalidades
3. Probar exhaustivamente los cambios para garantizar que el selector elige el playbook correcto en cada situación
4. Documentar cualquier cambio significativo en este README 