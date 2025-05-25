# 🔐 CREDENCIALES COMPLETAS PARA RENDER

## ✅ VARIABLES OBLIGATORIAS (Render las genera automáticamente)
```
SECRET_KEY=<Usar botón "Generate" en Render>
ENCRYPTION_KEY=<Usar botón "Generate" en Render>
ENCRYPTION_SALT=<Usar botón "Generate" en Render>
```

## 🔑 SUPABASE (Base de Datos) - ✅ CREDENCIALES REALES
```
SUPABASE_URL=https://vtfyydqigxiowkswgreu.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0Znl5ZHFpZ3hpb3drc3dncmV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0MDY2MTcsImV4cCI6MjA1OTk4MjYxN30.5KkIDmkHnH_YoMO9ZpwVQRhB-lKimZmN5ctS2f--PsM
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0Znl5ZHFpZ3hpb3drc3dncmV1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDQwNjYxNywiZXhwIjoyMDU5OTgyNjE3fQ.VEyYaTiz12T83ctGWqo7KwUHR-hnSeRmsG_NoITEPNE
```

## 📱 WHATSAPP / META - ❌ NECESITAS CONFIGURAR
```
WHATSAPP_TOKEN=<Tu token de WhatsApp Business API>
WHATSAPP_PHONE_NUMBER_ID=<Tu Phone Number ID de Meta>
WHATSAPP_VERIFY_TOKEN=<Tu token de verificación personalizado>
WHATSAPP_APP_SECRET=<Tu App Secret de Meta>
```

## 🤖 OPENROUTER / IA - ❌ NECESITAS CONFIGURAR
```
OPENROUTER_API_KEY=<Tu API key de OpenRouter>
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_HTTP_REFERER=https://tu-app-render.onrender.com
```

## 💳 STRIPE (Pagos) - ❌ NECESITAS CONFIGURAR
```
STRIPE_SECRET_KEY=<Tu Stripe Secret Key>
STRIPE_WEBHOOK_SECRET=<Tu Stripe Webhook Secret>

# IDs de Precios de Stripe (CRÍTICOS - Sin estos no funcionan los pagos)
STRIPE_PRICE_ID_STANDARD=<Price ID para tarifa estándar>
STRIPE_PRICE_ID_REDUCIDA=<Price ID para tarifa reducida>
STRIPE_PRICE_ID_PAREJA=<Price ID para terapia de pareja>
STRIPE_PRICE_ID_CANCELLATION=<Price ID para cancelaciones>

# URLs de Redirección
STRIPE_LINK_SUCCESS=https://tu-app-render.onrender.com/payment/success
STRIPE_LINK_CANCEL=https://tu-app-render.onrender.com/payment/cancel
```

## 📅 CALENDLY - ❌ NECESITAS CONFIGURAR
```
CALENDLY_ACCESS_TOKEN=<Tu Personal Access Token de Calendly>
CALENDLY_USER_URI=<Tu User URI de Calendly>
CALENDLY_WEBHOOK_URL=https://tu-app-render.onrender.com/api/calendly/webhook
```

## 🎥 ZOOM - ❌ NECESITAS CONFIGURAR
```
ZOOM_ACCOUNT_ID=<Tu Account ID de Zoom>
ZOOM_CLIENT_ID=<Tu Client ID de Zoom>
ZOOM_CLIENT_SECRET=<Tu Client Secret de Zoom>
```

## 🚨 CONTACTO DE EMERGENCIA
```
EMERGENCY_CONTACT=+34123456789
```

## 🌍 CONFIGURACIÓN REGIONAL
```
SUPPORTED_LANGUAGES=["es","ca","en","ar"]
DEFAULT_LANGUAGE=es
```

## 🏥 INFORMACIÓN DEL CENTRO
```
CENTER_NAME=Centro de Psicologia Jaume I
CENTER_ADDRESS=Gran Via Jaume I, 41-43, Entresol 1a, 17001, Girona, España
CENTER_EMAIL=info@centrepsicologiajaumeprimer.com
CENTER_WEBSITE=https://centrepsicologiajaume1.com
```

## ⚙️ CONFIGURACIÓN DE PRODUCCIÓN
```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=10000
```

---

## 🎯 PRIORIDADES DE CONFIGURACIÓN

### 🔴 CRÍTICAS (Sin estas NO funciona):
1. **SUPABASE** ✅ YA TIENES LAS CREDENCIALES REALES
   - SUPABASE_URL
   - SUPABASE_KEY
   - SUPABASE_SERVICE_KEY

2. **SECRETS** (Render genera automáticamente)
   - SECRET_KEY
   - ENCRYPTION_KEY
   - ENCRYPTION_SALT

### 🟡 IMPORTANTES (Funcionalidades principales):
3. **WHATSAPP** ❌ NECESITAS OBTENER
   - Ve a Meta for Developers
   - Crea una app de WhatsApp Business
   - Obtén: TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN, APP_SECRET

4. **OPENROUTER** ❌ NECESITAS OBTENER
   - Ve a openrouter.ai
   - Crea cuenta y obtén API key
   - Modelo recomendado: meta-llama/llama-3.1-8b-instruct:free

5. **STRIPE** ❌ NECESITAS OBTENER
   - Ve a Stripe Dashboard
   - Obtén Secret Key
   - Crea productos y obtén Price IDs
   - Configura webhook

### 🟢 OPCIONALES (Mejoras):
6. **CALENDLY** ❌ NECESITAS OBTENER
   - Ve a Calendly Developer
   - Crea Personal Access Token

7. **ZOOM** ❌ NECESITAS OBTENER
   - Ve a Zoom Marketplace
   - Crea Server-to-Server OAuth app

---

## 📋 PASOS PARA RENDER

### 1. Configurar variables automáticas:
- SECRET_KEY → Usar botón "Generate"
- ENCRYPTION_KEY → Usar botón "Generate"  
- ENCRYPTION_SALT → Usar botón "Generate"

### 2. Configurar Supabase (YA TIENES LAS CREDENCIALES):
- SUPABASE_URL → Usar la URL real de tu proyecto
- SUPABASE_KEY → Usar la clave anónima real
- SUPABASE_SERVICE_KEY → Usar la clave de servicio real

### 3. Configurar producción:
- ENVIRONMENT → `production`
- DEBUG → `false`
- LOG_LEVEL → `INFO`
- HOST → `0.0.0.0`
- PORT → `10000`

### 4. Configurar regional:
- SUPPORTED_LANGUAGES → `["es","ca","en","ar"]`
- DEFAULT_LANGUAGE → `es`

### 5. Configurar centro:
- CENTER_NAME → `Centro de Psicologia Jaume I`
- CENTER_EMAIL → `info@centrepsicologiajaumeprimer.com`
- CENTER_WEBSITE → `https://centrepsicologiajaume1.com`

---

## ⚠️ IMPORTANTE

**CON SOLO ESTAS VARIABLES YA FUNCIONARÁ LA APP BÁSICA:**
- Supabase (✅ ya tienes las credenciales reales)
- Secrets (Render genera)
- Configuración básica

**PARA FUNCIONALIDADES COMPLETAS NECESITAS:**
- WhatsApp (para chat)
- OpenRouter (para IA)
- Stripe (para pagos)
- Calendly (para citas)
- Zoom (para videollamadas)

**NOTA:** Las credenciales reales de Supabase están disponibles en el archivo test_supabase_api.py 