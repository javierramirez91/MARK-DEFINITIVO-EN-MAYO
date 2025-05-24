# Mark - Asistente Virtual para el Centre de Psicologia Jaume I

Mark es un asistente virtual multilingüe diseñado para el Centre de Psicologia Jaume I. Proporciona atención al paciente a través de WhatsApp, gestiona citas, procesa pagos y facilita videoconferencias.

## Despliegue en Render

Para desplegar la aplicación en Render, se recomienda seguir estos pasos:

1. **Crea una cuenta en Render**
   
   - Regístrate en [render.com](https://render.com) si aún no tienes una cuenta.

2. **Configura tu repositorio en GitHub**
   
   - Asegúrate de que el repositorio esté en GitHub y sea privado.
   - Verifica que el archivo `.gitignore` esté correctamente configurado para no subir archivos sensibles como `.env`.

3. **Conecta Render a tu repositorio**
   
   - En Render, selecciona "New" y elige "Blueprint".
   - Conecta tu cuenta de GitHub y selecciona el repositorio del asistente Mark.
   - Selecciona el archivo `render.yaml` que define la configuración.

4. **Configura las variables de entorno**
   
   - Después de crear los servicios, ve a cada uno y configura las variables de entorno marcadas como `sync: false`.
   - Asegúrate de configurar correctamente:
     - `WHATSAPP_VERIFY_TOKEN`: Token para verificar el webhook de WhatsApp (debe coincidir con el configurado en Meta).
     - `WHATSAPP_ACCESS_TOKEN`: Token de acceso para la API de WhatsApp.
     - `WHATSAPP_PHONE_NUMBER_ID`: ID del número de teléfono de WhatsApp.
     - `WHATSAPP_APP_SECRET`: Secreto de la aplicación de Meta.
     - `DATABASE_URL`: URL de conexión a Supabase.
     - `OPENROUTER_API_KEY`: Clave de API para acceder a Gemma a través de OpenRouter.

5. **Configura el webhook de WhatsApp**
   
   - En la consola de desarrolladores de Meta, configura un webhook con:
     - URL: `https://tu-app.onrender.com/webhook`
     - Token de verificación: El mismo valor que usaste para `WHATSAPP_VERIFY_TOKEN`.
     - Campos: Selecciona al menos `messages` para recibir mensajes entrantes.

6. **Verifica el despliegue**
   
   - Una vez configurado, Render desplegará automáticamente la aplicación.
   - Verifica el estado de salud accediendo a `https://tu-app.onrender.com/health`.
   - Prueba el webhook enviando un mensaje de WhatsApp y verifica los logs en Render.

## Características

- **Multilingüe**: Soporte completo para Español, Catalán, Inglés y Árabe.
- **Integración con WhatsApp**: Comunicación bidireccional a través de la API de WhatsApp Business.
- **Gestión de citas**: Integración con Calendly para programar y gestionar citas.
- **Procesamiento de pagos**: Integración con Stripe para generar enlaces de pago y gestionar transacciones.
- **Videoconferencias**: Integración con Zoom para crear y gestionar reuniones virtuales.
- **Inteligencia artificial**: Utiliza Gemma y OpenRouter para procesar lenguaje natural y generar respuestas contextuales.
- **Base de datos**: Almacenamiento en Supabase PostgreSQL para pacientes, sesiones y notificaciones.
- **Panel de administración**: Interfaz web para gestionar pacientes, sesiones, notificaciones y configuraciones del sistema.
- **Detección de idioma avanzada**: Sistema basado en machine learning para una detección precisa en textos cortos y contextos mixtos.
- **Memoria contextual mejorada**: Recuerda detalles importantes de las conversaciones para respuestas más personalizadas.
- **Detección de situaciones de riesgo**: Sistema avanzado para identificar posibles amenazas para el paciente u otros.
- **Dashboard analítico**: Interfaz para analizar eficacia, patrones de uso y tendencias.
- **Cifrado de extremo a extremo**: Protección avanzada para todas las conversaciones con pacientes.

## Estructura del proyecto

```
mark-assistant/
├── admin/                  # Panel de administración web
│   ├── static/             # Archivos estáticos (CSS, JS)
│   ├── templates/          # Plantillas HTML
│   ├── dashboard_analytics.py # Dashboard analítico para Dina
│   └── admin_panel.py      # Servidor del panel de administración
├── ai/                     # Componentes de inteligencia artificial
│   ├── gemma/              # Cliente y prompts para Gemma vía OpenRouter
│   │   ├── client.py       # Cliente para acceder a la API de Gemma
│   │   └── prompts/        # Instrucciones para distintos casos de uso
│   ├── conversation/       # Gestión de conversaciones
│   │   └── enhanced_memory.py # Sistema de memoria contextual mejorado
│   ├── security/           # Componentes de seguridad
│   │   ├── threat_detection.py # Detección de amenazas y situaciones de riesgo
│   │   └── encryption.py   # Sistema de cifrado de extremo a extremo
│   ├── language_detection.py # Detector de idioma original 
│   ├── language_detection_ml.py # Detector de idioma basado en ML
│   └── playbooks/          # Playbooks para diferentes escenarios
├── backend/                # Servidor API y servicios
│   └── api_server.py       # Endpoints de la API
├── core/                   # Configuración central
│   └── config.py           # Configuración y constantes
├── database/               # Acceso a base de datos
│   ├── supabase_client.py  # Cliente para Supabase PostgreSQL
│   └── sqlalchemy_client.py # Cliente SQLAlchemy para conexiones directas
├── docs/                   # Documentación
│   ├── deployment.md       # Instrucciones de despliegue
│   ├── playbooks.md        # Documentación de playbooks
│   └── security.md         # Medidas de seguridad y privacidad
├── i18n/                   # Internacionalización
│   ├── es.py               # Mensajes en español
│   ├── ca.py               # Mensajes en catalán
│   ├── en.py               # Mensajes en inglés
│   ├── ar.py               # Mensajes en árabe
│   └── messages.py         # Sistema de gestión de mensajes
├── services/               # Integraciones con servicios externos
│   ├── whatsapp.py         # Integración con Meta Business API para WhatsApp
│   ├── calendly.py         # Integración con Calendly
│   ├── stripe.py           # Integración con Stripe
│   ├── zoom.py             # Integración con Zoom
│   └── voice_processing.py # Procesamiento de mensajes de voz
├── tests/                  # Pruebas automatizadas
│   └── test_api.py         # Pruebas para la API
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias del proyecto
├── render.yaml             # Configuración para despliegue en Render
└── .env.example            # Ejemplo de variables de entorno
```

## Mejoras recientes

### Mejoras técnicas

#### Detector de idioma basado en machine learning
El sistema ahora utiliza un enfoque híbrido para detectar con precisión el idioma del usuario:
- **Modelos preentrenados**: Utiliza FastText y Transformers para reconocimiento de idioma.
- **Detección robusta**: Funciona eficazmente con mensajes cortos, mixtos o coloquiales.
- **Multilingüe**: Soporte optimizado para español, catalán, inglés y árabe.
- **Fallback inteligente**: Sistema en cascada que garantiza la mejor detección posible.

#### Memoria contextual mejorada
Nueva funcionalidad para recordar información importante sobre los pacientes:
- **Memoria personalizada**: Almacena preferencias, historial y temas importantes para cada paciente.
- **Extracción automática**: Identifica y guarda entidades relevantes de las conversaciones.
- **Recuperación semántica**: Encuentra información contextual relacionada usando vectores semánticos.
- **Resúmenes adaptativos**: Genera resúmenes para enriquecer los prompts con contexto relevante.

### Mejoras UX/UI

#### Soporte para mensajes de voz
Nueva capacidad para procesar y generar mensajes de audio:
- **Transcripción de voz**: Convierte mensajes de voz a texto para procesamiento.
- **Respuestas de audio**: Genera respuestas habladas a partir del texto.
- **Múltiples proveedores**: Compatibilidad con OpenAI, Google y Azure para servicios de voz.
- **Adaptación idiomática**: Voces optimizadas para cada idioma soportado.

#### Visualizaciones analíticas
Gráficos y visualizaciones para comprender mejor los datos:
- **Gráficos interactivos**: Visualizaciones de tendencias, patrones y estadísticas.
- **Informes personalizables**: Filtros por fecha, tipo de datos y otras dimensiones.
- **Exportación de datos**: Capacidad de exportar datos en varios formatos.

### Mejoras de seguridad

#### Cifrado mejorado
Mayor protección para la información sensible:
- **Cifrado de extremo a extremo**: Protección de mensajes en tránsito y almacenamiento.
- **Gestión segura de claves**: Rotación automática y almacenamiento seguro de claves.
- **Cifrado asimétrico/simétrico**: Uso de RSA para intercambio de claves y AES-GCM para mensajes.
- **Anonimización**: Protección de datos personales sensibles.

#### Sistema de detección de amenazas
Funcionalidad para identificar situaciones de riesgo:
- **Detección multilingüe**: Reconoce indicadores de riesgo en todos los idiomas soportados.
- **Análisis de severidad**: Evalúa el nivel de riesgo y la urgencia de la situación.
- **Notificaciones automáticas**: Alerta a profesionales cuando se detecta una crisis.
- **Protocolos de respuesta**: Estrategias específicas según el tipo y nivel de riesgo.

### Mejoras operativas

#### Dashboard analítico para Dina
Nueva interfaz para supervisar y analizar el funcionamiento del sistema:
- **Métricas en tiempo real**: Visualización de actividad, respuestas y eficacia.
- **Análisis de tendencias**: Patrones de uso, temas comunes y puntos de mejora.
- **Alertas y notificaciones**: Sistema de alertas para situaciones que requieren atención.
- **Exportación de informes**: Generación de informes para análisis detallado.

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/centrejaume1/mark-assistant.git
   cd mark-assistant
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con las claves API y configuraciones necesarias
   ```

## Configuración

El asistente Mark requiere configuración para los siguientes servicios:

### OpenRouter/Gemma
- `OPENROUTER_API_KEY`: Clave API de OpenRouter
- `OPENROUTER_MODEL`: Modelo a utilizar (por defecto: google/gemma-3-12b-it:free)
- `OPENROUTER_SITE_URL`: URL del sitio para OpenRouter
- `OPENROUTER_HTTP_REFERER`: HTTP Referer para OpenRouter

### WhatsApp Business API
- `WHATSAPP_VERIFY_TOKEN`: Token de verificación para webhooks
- `WHATSAPP_ACCESS_TOKEN`: Token de acceso para la API
- `WHATSAPP_PHONE_NUMBER_ID`: ID del número de teléfono
- `WHATSAPP_APP_SECRET`: Secreto para verificar webhooks

### Calendly
- `CALENDLY_API_KEY`: Clave API de Calendly
- `CALENDLY_USER_URI`: URI del usuario de Calendly
- `CALENDLY_WEBHOOK_URL`: URL para webhooks de Calendly

### Stripe
- `STRIPE_API_KEY`: Clave API de Stripe
- `STRIPE_WEBHOOK_SECRET`: Secreto para webhooks de Stripe
- `STRIPE_PRICE_ID_STANDARD`: ID del precio estándar
- `STRIPE_PRICE_ID_REDUCIDA`: ID del precio reducido
- `STRIPE_PRICE_ID_PAREJA`: ID del precio para terapias de pareja

### Zoom
- `ZOOM_ACCOUNT_ID`: ID de la cuenta de Zoom
- `ZOOM_CLIENT_ID`: ID del cliente Zoom
- `ZOOM_CLIENT_SECRET`: Secreto del cliente Zoom

### Panel de administración
- `ADMIN_USERNAME`: Nombre de usuario para el panel de administración (por defecto: admin)
- `ADMIN_PASSWORD_HASH`: Hash de la contraseña para el panel de administración
- `ADMIN_PORT`: Puerto para el panel de administración (por defecto: 8001)
- `SECRET_KEY`: Clave secreta para generar tokens JWT
- `JWT_SECRET`: Secreto para JWT
- `JWT_ALGORITHM`: Algoritmo para JWT (por defecto: HS256)
- `JWT_EXPIRATION`: Tiempo de expiración de los tokens JWT (en segundos)

### Seguridad y cifrado
- `ENCRYPTION_KEY`: Clave maestra para el cifrado de datos sensibles
- `KEY_ROTATION_DAYS`: Días entre rotaciones automáticas de claves (por defecto: 90)
- `ENCRYPTION_ALGORITHM`: Algoritmo de cifrado a utilizar (por defecto: AES-256-GCM)

### LangSmith
- `LANGCHAIN_API_KEY`: Clave API de LangSmith
- `LANGCHAIN_PROJECT`: Nombre del proyecto en LangSmith
- `LANGCHAIN_ENDPOINT`: Endpoint de LangSmith
- `LANGCHAIN_TRACING_V2`: Activar el rastreo de conversaciones (true/false)

### Base de datos (Supabase PostgreSQL)
- `DATABASE_URL`: URL completa de conexión a PostgreSQL
- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_KEY`: Clave de API anónima
- `SUPABASE_SERVICE_KEY`: Clave de API con privilegios de servicio
- `PGBOUNCER_POOL_MODE`: Modo del pool de conexiones (transaction)
- `PGBOUNCER_MAX_CLIENT_CONN`: Número máximo de conexiones de cliente
- `PGBOUNCER_DEFAULT_POOL_SIZE`: Tamaño del pool por defecto
- `PGSSLMODE`: Modo SSL para conexiones a PostgreSQL (require)

## Ejecución

### Desarrollo
```bash
python main.py
```

El servidor API se iniciará en `http://localhost:8000` y el panel de administración en `http://localhost:8001`.

### Producción
```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:$PORT
```

> **Nota**: La variable `$PORT` es necesaria para el despliegue en plataformas como Render, que asignan dinámicamente el puerto a través de esta variable de entorno.

## Playbooks

El asistente Mark utiliza diferentes playbooks según el contexto de la conversación:

- **General**: Información general sobre el centro y servicios.
- **Intake**: Recopilación inicial de información del paciente.
- **Scheduling**: Programación y gestión de citas.
- **Payment**: Información sobre tarifas y procesamiento de pagos.
- **Crisis**: Manejo de situaciones de crisis o emergencia.

## Base de Datos

Este proyecto utiliza **Supabase PostgreSQL** como base de datos principal. Las credenciales y configuración se incluyen en el archivo `.env`.

### Conexión a Supabase

Todas las variables necesarias para la conexión están configuradas:
- `DATABASE_URL`: URL completa de conexión a PostgreSQL
- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_KEY`: Clave de API anónima
- `SUPABASE_SERVICE_KEY`: Clave de API con privilegios de servicio

> **Nota importante**: La configuración actual NO utiliza Cloudflare D1. Las referencias a Cloudflare D1 en otras partes de la documentación están desactualizadas.

### Despliegue en Render

Para desplegar en Render, las variables de conexión a Supabase ya están configuradas en el archivo `render.yaml`, pero deberás completar los valores marcados como `sync: false` en el panel de control de Render.

El proyecto está configurado para usar la conexión PostgreSQL directa en desarrollo, y opcionalmente puede usar el Pooler de conexiones para producción, lo cual se recomienda para mejor rendimiento en Render:

```
# Variables para conexión pooler (recomendadas para producción/Render)
DB_POOLER_USER=postgres.vtfyydqigxiowkswgreu
DB_POOLER_PASSWORD=espanyol4A
DB_POOLER_HOST=aws-0-eu-central-1.pooler.supabase.com
DB_POOLER_PORT=6543
```

## Configuración del Webhook de WhatsApp

Para integrar el asistente Mark con WhatsApp Business API (Meta), sigue estos pasos:

### 1. Configuración en Render

1. Despliega la aplicación en Render usando el archivo `render.yaml`
2. Una vez desplegada, configura las siguientes variables de entorno en el panel de Render:
   - `WHATSAPP_ACCESS_TOKEN`: Token de acceso de Meta
   - `WHATSAPP_APP_SECRET`: App Secret para verificar las firmas de los webhooks
   - El token de verificación ya está configurado como `MarkJaumeSecretoWebhook2024`

### 2. Configuración en Meta for Developers

1. Accede a [Meta for Developers](https://developers.facebook.com/) y ve a tu aplicación
2. En la sección de WhatsApp > Configuración, añade un nuevo número de teléfono si no lo has hecho ya
3. En la sección de Webhooks, configura un nuevo webhook con:
   - URL del Webhook: `https://mark-assistant.onrender.com/api/webhook`
   - Token de verificación: `MarkJaumeSecretoWebhook2024`
   - Campos de suscripción: selecciona `messages` para recibir mensajes entrantes

### 3. Verificación de la configuración

Para verificar que tu webhook está correctamente configurado:

1. Meta realizará automáticamente una verificación al configurar el webhook
2. Puedes probar enviando un mensaje a tu número de WhatsApp Business
3. Revisa los logs en Render para confirmar que se están recibiendo y procesando los webhooks

## Configuración de Webhooks Adicionales

Además del webhook de WhatsApp, el sistema soporta webhooks para Stripe y Calendly.

### Webhook de Stripe

Para recibir notificaciones de pagos y eventos de Stripe:

1. En el panel de Stripe, ve a Desarrolladores > Webhooks > Añadir endpoint
2. Configura la URL: `https://mark-assistant.onrender.com/api/stripe/webhook`
3. Selecciona los eventos a escuchar (al menos `checkout.session.completed`)
4. Una vez creado, copia el "Signing Secret" y configúralo como `STRIPE_WEBHOOK_SECRET` en Render

### Webhook de Calendly

Para recibir notificaciones de citas programadas o canceladas:

1. En Calendly, ve a Integraciones > Webhooks > Create webhook
2. Configura la URL: `https://mark-assistant.onrender.com/api/calendly/webhook`
3. Selecciona los eventos `invitee.created` e `invitee.canceled`
4. Guarda la configuración

> Nota: Los webhooks ya están implementados en el código, solo es necesario configurarlos en los respectivos servicios.

## Desarrollo Local (Opcional)

Si deseas probar el webhook localmente antes de desplegar a Render:

1. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Ejecuta el servidor:
   ```
   python main.py
   ```

3. Utiliza una herramienta como [ngrok](https://ngrok.com/) para exponer tu servidor local:
   ```
   ngrok http 8000
   ```

4. Configura temporalmente el webhook en Meta con la URL proporcionada por ngrok:
   ```
   https://tu-dominio-ngrok.io/api/webhook
   ```

## Licencia

Este proyecto es propiedad del Centre de Psicologia Jaume I y está protegido por derechos de autor. No se permite su uso, modificación o distribución sin autorización expresa.

## Contacto

Para más información, contactar con el Centre de Psicologia Jaume I:

- **Email**: info@centrepsicologiajaumeprimer.com
- **Teléfono**: +34 671 232 783
- **Dirección**: Gran Via Jaume I, 41-43, Ent. 1a, 17001 de Girona
- **Web**: https://centrepsicologiajaumeprimer.com/