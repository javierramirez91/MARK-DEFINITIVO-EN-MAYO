# Estructura del Proyecto Mark

Este documento detalla la estructura de directorios y archivos del asistente virtual Mark, explicando el propósito de cada componente.

## Visión General

```
VirtualPsychologyCenter/
│
├── .env                               # Variables de entorno (API keys)
├── .env.example                       # Ejemplo de variables de entorno (para compartir)
├── .gitignore                         # Archivos a ignorar en Git
├── README.md                          # Documentación principal
├── CURSOR_DEVELOPMENT.md              # Guía de desarrollo en Cursor
├── requirements.txt                   # Dependencias Python
├── Dockerfile                         # Contenedor para Docker
├── main.py                            # Punto de entrada principal
├── cursor_setup.sh                    # Script de configuración para Cursor
│
├── core/                              # Componentes principales
│   ├── __init__.py
│   ├── config.py                      # Configuración global
│   └── cloudflare/                    # Infraestructura Cloudflare
│       ├── __init__.py
│       ├── worker.js                  # Worker principal
│       └── config.js                  # Configuración de Cloudflare
│
├── ai/                                # Componentes de IA
│   ├── __init__.py
│   ├── context_detection.py           # Detección de contexto en mensajes
│   ├── claude/                        # Integración con Claude 3.7
│   │   ├── __init__.py
│   │   ├── client.py                  # Cliente API para Claude
│   │   └── prompts/                   # Prompts para Claude
│   │       ├── __init__.py
│   │       ├── playbook1.py           # Identidad e idioma
│   │       ├── playbook2.py           # Crisis y solicitudes a Dina
│   │       ├── playbook3.py           # Citas y pagos
│   │       └── playbook4.py           # Seguridad y reportes
│   │
│   ├── hume/                          # Integración con Hume EVI 2
│   │   ├── __init__.py
│   │   ├── client.py                  # Cliente API para Hume
│   │   ├── voice_handler.py           # Manejo de llamadas de voz
│   │   └── config.py                  # Configuración de Hume
│   │
│   ├── langsmith/                     # Integración con LangSmith
│   │   ├── __init__.py
│   │   ├── client.py                  # Cliente para LangSmith
│   │   ├── traces.py                  # Trazas y monitoreo
│   │   └── evaluators/                # Evaluadores
│   │       ├── __init__.py
│   │       ├── language_adherence.py  # Evaluador de adherencia al idioma
│   │       └── response_quality.py    # Evaluador de calidad de respuesta
│   │
│   ├── langgraph/                     # Flujos conversacionales
│   │   ├── __init__.py
│   │   ├── engine.py                  # Motor de ejecución
│   │   └── flows/                     # Definición de flujos
│   │       ├── __init__.py
│   │       ├── intake_flow.py         # Flujo de entrada de pacientes
│   │       ├── therapy_flow.py        # Flujo de sesión terapéutica
│   │       └── scheduling_flow.py     # Flujo de programación de citas
│   │
│   ├── llamaindex/                    # Integración con LlamaIndex
│   │   ├── __init__.py
│   │   ├── indexer.py                 # Indexador de documentos
│   │   └── retriever.py               # Recuperador de información
│   │
│   └── serper/                        # Integración con Serper para búsqueda
│       ├── __init__.py
│       └── client.py                  # Cliente para búsquedas web
│
├── i18n/                              # Internacionalización
│   ├── __init__.py
│   ├── language_detection.py          # Detección de idioma
│   ├── messages.py                    # Gestor de mensajes multilingüe
│   ├── es.py                          # Mensajes en español
│   ├── ca.py                          # Mensajes en catalán
│   ├── en.py                          # Mensajes en inglés
│   └── ar.py                          # Mensajes en árabe
│
├── backend/                           # Lógica del servidor
│   ├── __init__.py
│   ├── api_server.py                  # Servidor API principal
│   └── services/                      # Servicios de integración
│       ├── __init__.py
│       ├── whatsapp.py                # Integración con Twilio WhatsApp
│       ├── calendly.py                # Integración con Calendly
│       ├── stripe.py                  # Integración con pagos Stripe
│       └── zoom.py                    # Integración con Zoom
│
└── database/                          # Esquema y funciones de base de datos
    ├── __init__.py
    ├── schema.sql                     # Esquema de Cloudflare D1
    └── d1_client.py                   # Cliente para Cloudflare D1
```

## Descripción de Componentes

### Archivos Raíz

- **main.py**: Punto de entrada principal de la aplicación. Inicializa el servidor API y configura los componentes principales.
- **cursor_setup.sh**: Script para configurar el entorno de desarrollo en Cursor IDE.
- **requirements.txt**: Lista de dependencias Python necesarias para el proyecto.
- **Dockerfile**: Configuración para crear un contenedor Docker de la aplicación.
- **.env**: Variables de entorno con claves API y configuraciones (no incluido en el repositorio).
- **.env.example**: Plantilla para crear el archivo .env con valores de ejemplo.

### Directorio `core/`

Contiene los componentes centrales y la configuración global del sistema.

- **config.py**: Gestiona la configuración global, cargando variables de entorno y estableciendo valores predeterminados.
- **cloudflare/**: Contiene la configuración y código para desplegar en Cloudflare Workers.
  - **worker.js**: Implementación del Worker de Cloudflare que maneja las solicitudes.
  - **config.js**: Configuración específica para el entorno de Cloudflare.

### Directorio `ai/`

Contiene todas las integraciones con servicios de IA y la lógica de procesamiento.

- **context_detection.py**: Analiza los mensajes para detectar el contexto y determinar el flujo adecuado.
- **claude/**: Integración con la API de Claude 3.7 de Anthropic.
  - **client.py**: Cliente para comunicarse con la API de Claude.
  - **prompts/**: Definiciones de prompts para diferentes escenarios.
    - **playbook1.py**: Prompts para identidad e idioma.
    - **playbook2.py**: Prompts para manejo de crisis y solicitudes a Dina.
    - **playbook3.py**: Prompts para gestión de citas y pagos.
    - **playbook4.py**: Prompts para seguridad y reportes.
- **hume/**: Integración con Hume EVI 2 para síntesis de voz.
  - **client.py**: Cliente para la API de Hume.
  - **voice_handler.py**: Manejo de conversiones de texto a voz.
  - **config.py**: Configuración específica para Hume.
- **langsmith/**: Integración con LangSmith para monitoreo y evaluación.
  - **client.py**: Cliente para la API de LangSmith.
  - **traces.py**: Gestión de trazas para monitoreo.
  - **evaluators/**: Evaluadores para diferentes aspectos de las respuestas.
    - **language_adherence.py**: Evalúa la adherencia al idioma seleccionado.
    - **response_quality.py**: Evalúa la calidad general de las respuestas.
- **langgraph/**: Implementación de flujos conversacionales con LangGraph.
  - **engine.py**: Motor central para la ejecución de grafos.
  - **flows/**: Definición de flujos específicos.
    - **intake_flow.py**: Flujo para la entrada inicial de pacientes.
    - **therapy_flow.py**: Flujo para sesiones de apoyo terapéutico.
    - **scheduling_flow.py**: Flujo para programación de citas.
- **llamaindex/**: Integración con LlamaIndex para indexación y recuperación de documentos.
  - **indexer.py**: Funcionalidad para indexar documentos.
  - **retriever.py**: Funcionalidad para recuperar información relevante.
- **serper/**: Integración con Serper para búsquedas web.
  - **client.py**: Cliente para la API de Serper.

### Directorio `i18n/`

Contiene la lógica de internacionalización y soporte multilingüe.

- **language_detection.py**: Detecta automáticamente el idioma de los mensajes entrantes.
- **messages.py**: Gestor central de mensajes en múltiples idiomas.
- **es.py**: Mensajes en español.
- **ca.py**: Mensajes en catalán.
- **en.py**: Mensajes en inglés.
- **ar.py**: Mensajes en árabe.

### Directorio `backend/`

Contiene la lógica del servidor y las integraciones con servicios externos.

- **api_server.py**: Implementación del servidor API con FastAPI.
- **services/**: Integraciones con servicios externos.
  - **whatsapp.py**: Integración con Twilio para WhatsApp.
  - **calendly.py**: Integración con Calendly para gestión de citas.
  - **stripe.py**: Integración con Stripe para pagos.
  - **zoom.py**: Integración con Zoom para videollamadas.

### Directorio `database/`

Contiene el esquema de la base de datos y funciones de acceso.

- **schema.sql**: Definición del esquema para Cloudflare D1.
- **d1_client.py**: Cliente para interactuar con la base de datos Cloudflare D1.

## Flujos de Datos Principales

### Procesamiento de Mensajes

1. El mensaje llega a través de la API o WhatsApp
2. Se detecta el idioma en `i18n/language_detection.py`
3. Se analiza el contexto en `ai/context_detection.py`
4. Se selecciona el flujo adecuado en `ai/langgraph/engine.py`
5. Se procesa a través del flujo correspondiente en `ai/langgraph/flows/`
6. Se genera una respuesta utilizando Claude en `ai/claude/client.py`
7. Se evalúa la respuesta con LangSmith en `ai/langsmith/evaluators/`
8. Se envía la respuesta al usuario

### Gestión de Citas

1. Se detecta una solicitud de cita en `ai/context_detection.py`
2. Se activa el flujo de programación en `ai/langgraph/flows/scheduling_flow.py`
3. Se verifica la disponibilidad a través de `backend/services/calendly.py`
4. Se confirma la cita y se crea en Calendly
5. Se genera un enlace de Zoom a través de `backend/services/zoom.py`
6. Se envía la confirmación al usuario

## Extensibilidad

La arquitectura está diseñada para ser extensible:

- **Nuevos Idiomas**: Añadir un nuevo archivo en `i18n/` y actualizar `language_detection.py`
- **Nuevos Flujos**: Crear un nuevo archivo en `ai/langgraph/flows/` y registrarlo en `engine.py`
- **Nuevas Integraciones**: Añadir un nuevo directorio en `ai/` o un nuevo servicio en `backend/services/` 