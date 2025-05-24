# Guía de Despliegue del Asistente Mark

Esta guía proporciona instrucciones detalladas para desplegar el asistente Mark en diferentes entornos, desde desarrollo local hasta producción.

## Requisitos Previos

Antes de comenzar, asegúrate de tener:

- Python 3.9+ instalado
- Cuenta en Cloudflare (para la base de datos D1)
- Cuenta en Twilio (para WhatsApp)
- Cuenta en Anthropic (para Claude)
- Cuenta en Calendly (opcional, para gestión de citas)
- Cuenta en Stripe (opcional, para pagos)
- Cuenta en Zoom (opcional, para videoconferencias)

## Despliegue Local (Desarrollo)

### 1. Preparar el Entorno

```bash
# Clonar el repositorio
git clone https://github.com/centrejaume1/mark-assistant.git
cd mark-assistant

# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env  # o usa cualquier editor de texto
```

### 3. Iniciar el Servidor

```bash
# Iniciar en modo desarrollo
python main.py
```

El servidor estará disponible en `http://localhost:8000`.

## Despliegue en Cloudflare Workers

El asistente Mark está diseñado para funcionar en Cloudflare Workers, aprovechando Cloudflare D1 para la base de datos.

### 1. Configurar Wrangler

```bash
# Instalar Wrangler CLI
npm install -g wrangler

# Autenticarse en Cloudflare
wrangler login
```

### 2. Crear archivo wrangler.toml

Crea un archivo `wrangler.toml` en la raíz del proyecto:

```toml
name = "mark-assistant"
main = "worker.js"
compatibility_date = "2023-10-30"

[vars]
ENVIRONMENT = "production"
VIRTUAL_ASSISTANT_NAME = "Mark"
EMERGENCY_CONTACT = "+34600000000"

[[d1_databases]]
binding = "DB"
database_name = "mark-database"
database_id = "tu-database-id"

[triggers]
crons = ["*/5 * * * *"]  # Ejecutar cada 5 minutos para procesar notificaciones

[site]
bucket = "./static"
```

### 3. Crear Base de Datos D1

```bash
# Crear base de datos D1
wrangler d1 create mark-database

# Actualizar wrangler.toml con el ID generado
```

### 4. Ejecutar Migraciones

```bash
# Crear archivo de migración
wrangler d1 migrations create mark-database initial-schema

# Editar el archivo de migración generado con el esquema SQL

# Aplicar migración
wrangler d1 migrations apply mark-database
```

### 5. Desplegar

```bash
# Desplegar a Cloudflare Workers
wrangler deploy
```

## Despliegue en Servidor Tradicional

### 1. Preparar el Servidor

```bash
# Actualizar paquetes
sudo apt update
sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv nginx

# Clonar el repositorio
git clone https://github.com/centrejaume1/mark-assistant.git /opt/mark-assistant
cd /opt/mark-assistant

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 2. Configurar Variables de Entorno

```bash
# Copiar y editar .env
cp .env.example .env
nano .env
```

### 3. Configurar Systemd

Crea un archivo de servicio systemd en `/etc/systemd/system/mark.service`:

```ini
[Unit]
Description=Mark Assistant
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/mark-assistant
Environment="PATH=/opt/mark-assistant/venv/bin"
ExecStart=/opt/mark-assistant/venv/bin/gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Activa el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mark
sudo systemctl start mark
```

### 4. Configurar Nginx

Crea un archivo de configuración en `/etc/nginx/sites-available/mark`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activa la configuración:

```bash
sudo ln -s /etc/nginx/sites-available/mark /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Configurar HTTPS con Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## Configuración de la Base de Datos D1

### 1. Esquema de la Base de Datos

El esquema de la base de datos D1 debe incluir las siguientes tablas:

```sql
-- Tabla de pacientes
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE,
    email TEXT,
    language TEXT DEFAULT 'es',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT
);

-- Tabla de sesiones
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    session_type TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled',
    scheduled_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients (id)
);

-- Tabla de notificaciones
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    message TEXT NOT NULL,
    channel TEXT DEFAULT 'whatsapp',
    status TEXT DEFAULT 'pending',
    scheduled_at TEXT,
    sent_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients (id)
);

-- Tabla de configuración del sistema
CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### 2. Índices Recomendados

```sql
-- Índices para mejorar el rendimiento
CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_sessions_patient_id ON sessions(patient_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_patient_id ON notifications(patient_id);
```

### 3. Datos Iniciales

```sql
-- Configuración inicial del sistema
INSERT INTO system_config (key, value) VALUES ('version', '1.0.0');
INSERT INTO system_config (key, value) VALUES ('last_maintenance', datetime('now'));
INSERT INTO system_config (key, value) VALUES ('emergency_contact', '+34600000000');
```

## Configuración de Webhooks

### 1. Webhook de Twilio para WhatsApp

En tu cuenta de Twilio:

1. Ve a la consola de Twilio > Messaging > Settings > WhatsApp Sandbox
2. Configura la URL del webhook: `https://tu-dominio.com/api/whatsapp/webhook`
3. Selecciona el método HTTP: `POST`

### 2. Webhook de Calendly

En tu cuenta de Calendly:

1. Ve a Integraciones > Webhooks
2. Añade un nuevo webhook: `https://tu-dominio.com/api/calendly/webhook`
3. Selecciona los eventos: `invitee.created`, `invitee.canceled`

### 3. Webhook de Stripe

En tu cuenta de Stripe:

1. Ve a Desarrolladores > Webhooks
2. Añade un endpoint: `https://tu-dominio.com/api/stripe/webhook`
3. Selecciona los eventos: `payment_intent.succeeded`, `payment_intent.failed`

## Monitoreo y Mantenimiento

### 1. Logs

Los logs se almacenan en:
- Desarrollo local: `logs/mark.log`
- Cloudflare Workers: Cloudflare Dashboard > Workers > mark-assistant > Logs
- Servidor tradicional: `/var/log/mark.log` y a través de `journalctl -u mark`

### 2. Respaldos de Base de Datos

Para D1, configura respaldos automáticos:

```bash
# Programar respaldo diario con wrangler
wrangler d1 backup create mark-database --output ./backups/mark-$(date +%Y%m%d).sql
```

### 3. Actualización

```bash
# Actualizar el código
cd /opt/mark-assistant
git pull

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar el servicio
sudo systemctl restart mark
```

## Solución de Problemas

### Problemas Comunes

1. **Error de conexión a D1**:
   - Verifica las credenciales de Cloudflare
   - Asegúrate de que el Worker tenga permisos para acceder a D1

2. **Errores en Webhooks**:
   - Verifica las firmas de seguridad
   - Comprueba los logs para ver la respuesta completa

3. **Problemas con Claude**:
   - Verifica la cuota de API
   - Asegúrate de que el modelo solicitado esté disponible

### Comandos Útiles

```bash
# Ver logs en tiempo real
sudo journalctl -u mark -f

# Verificar estado del servicio
sudo systemctl status mark

# Probar la API localmente
curl -X POST http://localhost:8000/api/health
``` 