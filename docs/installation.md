# Guía de Instalación y Configuración de Mark

Esta guía proporciona instrucciones detalladas para instalar, configurar y ejecutar el asistente Mark para el Centre de Psicologia Jaume I.

## Requisitos previos

Antes de comenzar, asegúrese de tener instalado:

- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git
- Acceso a las APIs necesarias (Claude, Twilio, etc.)
- Cuenta de Cloudflare (para la base de datos D1)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/centrejaume1/mark-assistant.git
cd mark-assistant
```

### 2. Crear y activar un entorno virtual

**En Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configuración

### 1. Configurar variables de entorno

Copie el archivo de ejemplo de variables de entorno y edítelo con sus propias configuraciones:

```bash
cp .env.example .env
```

Abra el archivo `.env` en su editor de texto preferido y configure las siguientes variables:

#### Configuración general
```
ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

#### Información del centro
```
CENTER_NAME=Centre de Psicologia Jaume I
CENTER_ADDRESS=Gran Via Jaume I, 41-43, entresuelo 1a, 17001, Girona, España
CENTER_EMAIL=info@centrejaume1.com
CENTER_WEBSITE=https://centrejaume1.com
```

#### Contacto de emergencia
```
EMERGENCY_CONTACT=+34600000000
EMERGENCY_CONTACT_NAME=Dr. Jaume Psicólogo
```

#### Claves API
```
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_MODEL=claude-3-opus-20240229
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+34600000000
```

#### Base de datos
```
DATABASE_URL=your_database_url
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
```

#### Seguridad
```
ENCRYPTION_KEY=your_encryption_key
SECRET_KEY=your_jwt_secret_key
```

#### Panel de administración
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your_password_hash
ADMIN_PORT=8001
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 2. Generar hash de contraseña para el panel de administración

Para generar un hash seguro para la contraseña del panel de administración, ejecute:

```bash
python -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('your_password'))"
```

Reemplace `your_password` con la contraseña deseada y copie el hash generado en la variable `ADMIN_PASSWORD_HASH` en el archivo `.env`.

### 3. Configurar la base de datos

#### Crear base de datos en Cloudflare D1

1. Inicie sesión en su cuenta de Cloudflare
2. Vaya a Workers & Pages > D1
3. Haga clic en "Create database"
4. Asigne un nombre a la base de datos (por ejemplo, "mark-assistant")
5. Anote el ID de la base de datos y actualice la variable `CLOUDFLARE_DATABASE_ID` en el archivo `.env`

#### Inicializar la base de datos

Ejecute el script de inicialización de la base de datos:

```bash
python database/init_db.py
```

### 4. Configurar Twilio para WhatsApp

1. Inicie sesión en su cuenta de Twilio
2. Configure un número de teléfono para WhatsApp
3. Configure el webhook para apuntar a su servidor:
   - URL: `https://your-server.com/webhook/whatsapp`
   - Método: POST
4. Actualice las variables `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` y `TWILIO_PHONE_NUMBER` en el archivo `.env`

### 5. Configurar Calendly (opcional)

Si desea utilizar Calendly para la gestión de citas:

1. Inicie sesión en su cuenta de Calendly
2. Obtenga su clave API y URI de usuario
3. Configure el webhook para apuntar a su servidor
4. Actualice las variables `CALENDLY_API_KEY`, `CALENDLY_USER` y `CALENDLY_WEBHOOK_URL` en el archivo `.env`

### 6. Configurar Stripe (opcional)

Si desea procesar pagos con Stripe:

1. Inicie sesión en su cuenta de Stripe
2. Obtenga su clave API y secreto de webhook
3. Cree un producto y un precio
4. Actualice las variables `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` y `STRIPE_PRICE_ID` en el archivo `.env`

### 7. Configurar Zoom (opcional)

Si desea integrar videoconferencias con Zoom:

1. Inicie sesión en su cuenta de Zoom Developer
2. Cree una aplicación OAuth
3. Obtenga la clave API, secreto API y ID de usuario
4. Actualice las variables `ZOOM_API_KEY`, `ZOOM_API_SECRET` y `ZOOM_USER_ID` en el archivo `.env`

## Ejecución

### Desarrollo

Para ejecutar el asistente Mark en modo desarrollo:

```bash
python main.py
```

Esto iniciará:
- El servidor API en `http://localhost:8000`
- El panel de administración en `http://localhost:8001`

### Producción

Para entornos de producción, se recomienda utilizar Gunicorn:

```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

También puede utilizar un servicio systemd para mantener el asistente en ejecución:

1. Cree un archivo de servicio systemd:

```bash
sudo nano /etc/systemd/system/mark-assistant.service
```

2. Añada el siguiente contenido:

```
[Unit]
Description=Mark Assistant
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/mark-assistant
ExecStart=/path/to/mark-assistant/venv/bin/gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
Restart=always
Environment="PATH=/path/to/mark-assistant/venv/bin"
EnvironmentFile=/path/to/mark-assistant/.env

[Install]
WantedBy=multi-user.target
```

3. Habilite e inicie el servicio:

```bash
sudo systemctl enable mark-assistant
sudo systemctl start mark-assistant
```

## Verificación

Para verificar que el asistente Mark está funcionando correctamente:

1. Acceda al endpoint de estado de salud:
   ```
   http://localhost:8000/health
   ```

2. Acceda al panel de administración:
   ```
   http://localhost:8001
   ```

3. Envíe un mensaje de prueba:
   ```bash
   curl -X POST "http://localhost:8000/message" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user",
       "message": "Hola, ¿cómo estás?",
       "language": "es",
       "session_id": "test_session"
     }'
   ```

## Solución de problemas

### Problemas comunes

1. **Error de conexión a la base de datos**
   - Verifique las credenciales de Cloudflare
   - Asegúrese de que la base de datos D1 esté creada y accesible

2. **Error de autenticación con servicios externos**
   - Verifique las claves API
   - Asegúrese de que las claves tengan los permisos necesarios

3. **El panel de administración no es accesible**
   - Verifique que el puerto 8001 esté abierto
   - Compruebe los logs para errores específicos

### Logs

Los logs se guardan en el directorio `logs/` y pueden ser útiles para diagnosticar problemas:

```bash
tail -f logs/mark.log
```

## Actualizaciones

Para actualizar el asistente Mark a la última versión:

```bash
cd /path/to/mark-assistant
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mark-assistant  # Si utiliza systemd
```

## Copias de seguridad

Se recomienda realizar copias de seguridad regulares de la base de datos:

```bash
# Exportar datos de Cloudflare D1
wrangler d1 export mark-assistant > backup_$(date +%Y%m%d).sql
```

## Contacto

Para soporte técnico, contacte con:

- **Email**: soporte@centrejaume1.com
- **Teléfono**: +34 600 000 000 