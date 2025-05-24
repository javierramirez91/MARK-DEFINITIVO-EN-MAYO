# Installation and Setup Guide

This document provides detailed instructions for setting up the Mark Assistant system from scratch, including all dependencies, configuration, and deployment steps.

## System Requirements

### Hardware Requirements
- **Server**: Virtual or physical server with at least 4 CPU cores and 8GB RAM
- **Storage**: Minimum 50GB SSD storage
- **Network**: Stable internet connection with at least 10Mbps upload/download

### Software Requirements
- **Operating System**: Ubuntu 20.04 LTS or newer
- **Python**: Version 3.10 or newer
- **Database**: SQLite (for development) / Cloudflare D1 (for production)
- **Web Server**: Nginx (for production)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/centrepsicologiajaume/mark-assistant.git
cd mark-assistant
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
# Core Configuration
ENVIRONMENT=development  # or production
DEBUG=True  # set to False in production
LOG_LEVEL=INFO

# API Keys
OPENAI_API_KEY=your_openai_api_key  # Required for GPT-4
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional backup for Claude
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
CALENDLY_API_KEY=your_calendly_api_key
STRIPE_API_KEY=your_stripe_api_key
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret

# Database Configuration
DATABASE_URL=sqlite:///mark_assistant.db  # for development
# For production with Cloudflare D1:
# DATABASE_URL=cloudflare:///mark_assistant

# Security
SECRET_KEY=generate_a_secure_random_key
ENCRYPTION_KEY_PATH=/path/to/encryption/keys
ALLOWED_HOSTS=localhost,127.0.0.1  # add your domain in production

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER=+34XXXXXXXXX
WHATSAPP_WEBHOOK_URL=https://your-domain.com/api/webhook/whatsapp

# Admin Panel
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password  # change in production
ADMIN_EMAIL=admin@example.com
```

### 4. Initialize the Database

```bash
# Run database migrations
python -m scripts.init_database

# Create initial admin user
python -m scripts.create_admin
```

### 5. Generate Encryption Keys

```bash
# Generate RSA keys for end-to-end encryption
python -m scripts.generate_encryption_keys
```

### 6. Test the Installation

```bash
# Run the test suite
python -m pytest

# Start the development server
python -m uvicorn backend.main:app --reload
```

## Production Deployment

### Option 1: Traditional Server Deployment

#### 1. Set Up Nginx

Install Nginx:

```bash
sudo apt update
sudo apt install nginx
```

Create a configuration file for Mark Assistant:

```bash
sudo nano /etc/nginx/sites-available/mark-assistant
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/mark-assistant/static;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/mark-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 2. Set Up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 3. Configure Systemd Service

Create a service file:

```bash
sudo nano /etc/systemd/system/mark-assistant.service
```

Add the following configuration:

```ini
[Unit]
Description=Mark Assistant
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/mark-assistant
ExecStart=/path/to/mark-assistant/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app -b 127.0.0.1:8000
Restart=always
Environment="PATH=/path/to/mark-assistant/venv/bin"
EnvironmentFile=/path/to/mark-assistant/.env

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable mark-assistant
sudo systemctl start mark-assistant
```

### Option 2: Render Deployment (Recommended)

Render provides a simpler deployment process with automatic SSL, scaling, and CI/CD integration.

#### 1. Prepare for Render Deployment

Create a `render.yaml` file in the root of your project:

```yaml
services:
  - type: web
    name: mark-assistant
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -k uvicorn.workers.UvicornWorker backend.main:app
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: CALENDLY_API_KEY
        sync: false
      - key: STRIPE_API_KEY
        sync: false
      - key: ZOOM_API_KEY
        sync: false
      - key: ZOOM_API_SECRET
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        value: cloudflare:///mark_assistant
      - key: ALLOWED_HOSTS
        value: mark-assistant.onrender.com,your-custom-domain.com
    autoDeploy: true
    healthCheckPath: /api/health
```

#### 2. Create a Render Account and Connect Repository

1. Sign up for a Render account at https://render.com
2. Connect your GitHub/GitLab repository to Render
3. Create a new Web Service and select your repository
4. Use the "Blueprint" option and select your `render.yaml` file
5. Configure environment variables for sensitive information (API keys)
6. Deploy the service

#### 3. Set Up Custom Domain (Optional)

1. In the Render dashboard, go to your service settings
2. Navigate to the "Custom Domain" section
3. Add your domain and follow the DNS configuration instructions
4. Render will automatically provision and renew SSL certificates

#### 4. Configure Twilio Webhook

Update your Twilio webhook URL to point to your Render deployment:

```
https://mark-assistant.onrender.com/api/webhook/whatsapp
```

or your custom domain if configured.

### 4. Configure Twilio Webhook

1. Log in to your Twilio account
2. Navigate to the WhatsApp sandbox or phone number settings
3. Set the webhook URL to your deployment URL with the webhook path:
   - For traditional deployment: `https://your-domain.com/api/webhook/whatsapp`
   - For Render deployment: `https://mark-assistant.onrender.com/api/webhook/whatsapp`
4. Ensure the webhook is configured to handle both incoming messages and status callbacks

## Configuration Options

### AI Model Configuration

Edit the `config/ai.yaml` file to adjust GPT-4 and Claude API settings:

```yaml
gpt4:
  model: "gpt-4-turbo"  # or gpt-4, gpt-4-32k
  temperature: 0.7
  max_tokens: 4000
  top_p: 0.9
  frequency_penalty: 0.0
  presence_penalty: 0.0
  system_prompt_path: "ai/gpt4/system_prompt.txt"

claude:
  enabled: false  # Set to true to use as fallback
  model: "claude-3-opus-20240229"  # or claude-3-sonnet, claude-3-haiku
  temperature: 0.7
  max_tokens: 4000
  top_p: 0.9
  top_k: 40
  system_prompt_path: "ai/claude/system_prompt.txt"
  
memory:
  max_conversation_length: 20
  summary_threshold: 10
  
playbooks_path: "ai/playbooks/"
```

### Language Settings

Edit the `config/language.yaml` file to adjust language detection thresholds and supported languages:

```yaml
supported_languages:
  - code: "es"
    name: "Spanish"
    threshold: 0.6
  - code: "ca"
    name: "Catalan"
    threshold: 0.7
  - code: "en"
    name: "English"
    threshold: 0.6
  - code: "ar"
    name: "Arabic"
    threshold: 0.8

default_language: "es"
detection_model: "fasttext"  # options: fasttext, transformers
```

### Security Settings

Edit the `config/security.yaml` file to adjust security settings:

```yaml
encryption:
  enabled: true
  key_rotation_days: 30
  min_key_length: 4096
  
threat_detection:
  enabled: true
  sensitivity: "medium"  # options: low, medium, high
  escalation_email: "security@example.com"
  
rate_limiting:
  max_requests_per_minute: 60
  max_messages_per_user_per_day: 100
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

If you encounter database connection errors:

1. Check that the `DATABASE_URL` in your `.env` file is correct
2. Ensure the database file exists and has proper permissions
3. For Cloudflare D1, verify your API token and account ID

#### WhatsApp Integration Issues

If WhatsApp messages are not being received:

1. Verify your Twilio credentials in the `.env` file
2. Check that the webhook URL is correctly configured in Twilio
3. Ensure your server is accessible from the internet
4. Check the Nginx and application logs for errors

#### Encryption Key Issues

If encryption errors occur:

1. Verify that the encryption keys have been generated
2. Check that the `ENCRYPTION_KEY_PATH` in your `.env` file is correct
3. Ensure the application has read/write permissions to the key directory

#### GPT-4 API Issues

If you encounter issues with the GPT-4 API:

1. Verify your OpenAI API key in the `.env` file
2. Check your OpenAI account for rate limits or billing issues
3. Verify the model name in `config/ai.yaml` is correct and available to your account
4. Consider enabling Claude as a fallback option

### Logs

Application logs are stored in the following locations:

- **Development**: Console output and `logs/mark-assistant.log`
- **Production (Traditional)**: `/var/log/mark-assistant/app.log` and systemd logs
- **Production (Render)**: Available in the Render dashboard under "Logs"

To view systemd logs (traditional deployment):

```bash
sudo journalctl -u mark-assistant
```

## Backup and Restore

### Database Backup

```bash
# For SQLite
python -m scripts.backup_database

# For Cloudflare D1
python -m scripts.backup_cloudflare_d1
```

Backups are stored in the `backups/` directory with timestamps.

### Encryption Keys Backup

```bash
python -m scripts.backup_encryption_keys
```

**IMPORTANT**: Store encryption key backups securely. Loss of encryption keys will result in inability to decrypt past conversations.

### Restore from Backup

```bash
# Restore database
python -m scripts.restore_database --backup-file backups/database_2023-10-15.bak

# Restore encryption keys
python -m scripts.restore_encryption_keys --backup-file backups/encryption_keys_2023-10-15.zip
```

## Updating the System

### Traditional Deployment

```bash
# Pull the latest changes
git pull origin main

# Activate the virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run database migrations
python -m scripts.migrate_database

# Restart the service
sudo systemctl restart mark-assistant
```

### Render Deployment

Updates to the Render deployment can be done in two ways:

1. **Automatic Deployment**: If you've enabled auto-deploy in your Render configuration, simply push changes to your repository's main branch.

2. **Manual Deployment**: In the Render dashboard, navigate to your service and click "Manual Deploy" > "Deploy latest commit".

## Next Steps

After installation, refer to the following documentation:

1. [Admin Panel Guide](03_admin_panel_guide.md)
2. [API Documentation](04_api_documentation.md)
3. [Security Guide](05_security_guide.md)
4. [Customization Guide](06_customization_guide.md)
5. [Troubleshooting Guide](07_troubleshooting_guide.md) 