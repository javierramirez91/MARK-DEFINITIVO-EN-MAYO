# Guía de Desarrollo en Cursor para Mark

## Introducción

Este documento proporciona instrucciones específicas para desarrollar el asistente virtual Mark utilizando [Cursor](https://cursor.sh/), un IDE potenciado por IA. Cursor facilita el desarrollo con asistencia de IA integrada, lo que resulta especialmente útil para este proyecto que utiliza múltiples tecnologías de IA.

## Configuración del Entorno

### Requisitos Previos

- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- [Cursor](https://cursor.sh/) instalado
- Acceso a las APIs necesarias (Claude, Hume, LangSmith, Serper)

### Configuración Inicial

1. Clona el repositorio:
   ```bash
   git clone https://github.com/centre-psicologia-jaume1/mark.git
   cd mark
   ```

2. Ejecuta el script de configuración para Cursor:
   ```bash
   # En Linux/macOS
   chmod +x cursor_setup.sh
   ./cursor_setup.sh
   
   # En Windows (PowerShell)
   # Primero, habilita la ejecución de scripts si es necesario
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\cursor_setup.sh
   ```

3. Configura tus variables de entorno:
   - Copia `.env.example` a `.env`
   - Edita `.env` con tus propias claves API

## Características de Cursor para este Proyecto

### Atajos de Teclado Útiles

- `Ctrl+K` / `Cmd+K`: Activa la asistencia de IA para responder preguntas o generar código
- `Ctrl+L` / `Cmd+L`: Explica el código seleccionado
- `Ctrl+J` / `Cmd+J`: Genera código basado en un comentario
- `Ctrl+I` / `Cmd+I`: Mejora el código seleccionado

### Flujo de Trabajo Recomendado

1. **Exploración del Código**:
   - Utiliza `Ctrl+K` para preguntar sobre la estructura del proyecto
   - Ejemplo: "¿Cómo funciona el flujo de conversación en langgraph?"

2. **Desarrollo de Nuevas Características**:
   - Escribe un comentario describiendo la funcionalidad
   - Usa `Ctrl+J` para generar el código inicial
   - Refina manualmente según sea necesario

3. **Depuración**:
   - Selecciona código con errores
   - Usa `Ctrl+K` y pregunta: "¿Por qué este código no funciona?"

4. **Documentación**:
   - Selecciona funciones sin documentar
   - Usa `Ctrl+I` y pide: "Añade docstrings a esta función"

## Estructura del Proyecto en Cursor

Para navegar eficientemente por el proyecto en Cursor:

### Componentes Principales

- **core/**: Configuración global y componentes de infraestructura
- **ai/**: Integraciones con servicios de IA (Claude, Hume, LangSmith, etc.)
- **i18n/**: Soporte multilingüe y detección de idiomas
- **backend/**: Servidor API y servicios de integración
- **database/**: Esquema y cliente de base de datos

### Flujos de Trabajo Clave

1. **Procesamiento de Mensajes**:
   - `ai/context_detection.py` → `ai/langgraph/flows/` → `ai/claude/client.py`

2. **Gestión de Citas**:
   - `ai/langgraph/flows/scheduling_flow.py` → `backend/services/calendly.py` → `backend/services/zoom.py`

3. **Integración de Voz**:
   - `backend/services/whatsapp.py` → `ai/hume/voice_handler.py`

## Mejores Prácticas

1. **Uso de la IA de Cursor**:
   - Sé específico en tus preguntas
   - Proporciona contexto cuando sea necesario
   - Revisa siempre el código generado

2. **Convenciones de Código**:
   - Sigue PEP 8 para estilo de código Python
   - Usa docstrings en formato Google para documentación
   - Mantén los archivos enfocados en una sola responsabilidad

3. **Gestión de Dependencias**:
   - Añade nuevas dependencias a `requirements.txt`
   - Especifica versiones exactas para evitar problemas de compatibilidad

4. **Control de Versiones**:
   - Haz commits pequeños y frecuentes
   - Usa mensajes de commit descriptivos
   - Crea ramas para nuevas características

## Solución de Problemas Comunes

### Problemas con las APIs

Si encuentras errores al conectar con las APIs:
1. Verifica que las claves API en `.env` sean correctas
2. Comprueba la conectividad a internet
3. Verifica los límites de uso de la API

### Errores en el Entorno Virtual

Si el entorno virtual no funciona correctamente:
1. Elimina la carpeta `venv`
2. Ejecuta nuevamente `cursor_setup.sh`

### Problemas con la Asistencia de IA en Cursor

Si la IA de Cursor no responde como se espera:
1. Reinicia Cursor
2. Asegúrate de tener la última versión
3. Proporciona más contexto en tus preguntas

## Recursos Adicionales

- [Documentación de Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Documentación de LangGraph](https://langchain-ai.github.io/langgraph/)
- [Documentación de Hume AI](https://dev.hume.ai/docs)
- [Documentación de LangSmith](https://docs.smith.langchain.com/)
- [Documentación de Cloudflare Workers](https://developers.cloudflare.com/workers/)

## Contribución

Para contribuir al proyecto:
1. Crea una rama para tu característica: `git checkout -b feature/nueva-caracteristica`
2. Realiza tus cambios y pruebas
3. Envía un pull request con una descripción detallada

## Soporte

Si necesitas ayuda con el desarrollo en Cursor:
- Usa `Ctrl+K` y pregunta sobre problemas específicos
- Consulta la [documentación oficial de Cursor](https://cursor.sh/docs)
- Contacta al equipo de desarrollo en [correo@example.com] 