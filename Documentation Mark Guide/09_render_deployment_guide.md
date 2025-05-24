# Render Deployment Guide

This guide provides detailed instructions for deploying the Mark Assistant on Render, including the configuration of Twilio for WhatsApp integration and Hume EVI for voice capabilities.

## Prerequisites

Before starting the deployment process, ensure you have:

1. A GitHub or GitLab repository with the Mark Assistant codebase
2. A Render account (sign up at [render.com](https://render.com))
3. A Twilio account with WhatsApp Business API access
4. A Hume AI account with access to the Hume EVI API
5. All necessary API keys and credentials

## Preparing the Repository for Deployment

### 1. Create a `render.yaml` File

Create a `render.yaml` file in the root of your repository to define the deployment configuration:

```yaml
services:
  - type: web
    name: mark-assistant
    env: python
    region: frankfurt  # Choose the region closest to your users
    plan: standard  # Choose an appropriate plan based on your needs
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT --workers 4
    healthCheckPath: /api/health
    autoDeploy: true
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: LOG_LEVEL
        value: INFO
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: mark-assistant.onrender.com,your-custom-domain.com
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: WHATSAPP_PHONE_NUMBER
        sync: false
      - key: HUME_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
    disk:
      name: mark-data
      mountPath: /data
      sizeGB: 10
```

### 2. Create a `.env.sample` File

Create a `.env.sample` file to document all required environment variables:

```
# Core Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your_secure_random_key
ALLOWED_HOSTS=mark-assistant.onrender.com,your-custom-domain.com

# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
HUME_API_KEY=your_hume_api_key

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER=+34XXXXXXXXX
WHATSAPP_WEBHOOK_URL=https://mark-assistant.onrender.com/api/webhook/whatsapp

# Database Configuration
DATABASE_URL=your_database_connection_string

# Security
ENCRYPTION_KEY_PATH=/data/encryption_keys
```

### 3. Update `requirements.txt`

Ensure your `requirements.txt` file includes all necessary dependencies, including those for Hume EVI:

```
# Core dependencies
fastapi>=0.95.0
uvicorn>=0.21.1
gunicorn>=20.1.0
pydantic>=1.10.7
python-dotenv>=1.0.0
httpx>=0.24.0

# Database
sqlalchemy>=2.0.9
alembic>=1.10.3

# AI and NLP
openai>=0.27.4
anthropic>=0.2.8
langchain>=0.0.200
fasttext>=0.9.2
transformers>=4.28.1

# Security
cryptography>=40.0.1
pyjwt>=2.6.0
bcrypt>=4.0.1

# WhatsApp Integration
twilio>=8.0.0

# Voice Processing
hume>=0.3.0
whisper>=1.0.0

# Utilities
pyyaml>=6.0
python-multipart>=0.0.6
```

## Deploying to Render

### 1. Connect Your Repository

1. Log in to your Render account
2. Click on "New" and select "Blueprint"
3. Connect your GitHub or GitLab account if you haven't already
4. Select the repository containing the Mark Assistant code
5. Render will detect the `render.yaml` file and show the services to be created
6. Click "Apply" to start the deployment process

### 2. Configure Environment Variables

After creating the service, you need to set up the environment variables:

1. Navigate to your web service in the Render dashboard
2. Go to the "Environment" tab
3. Add all the required environment variables from your `.env.sample` file
4. For sensitive values (API keys, tokens), ensure they are marked as "Secret"
5. Click "Save Changes"

### 3. Set Up Persistent Storage

For encryption keys and other persistent data:

1. In the Render dashboard, go to your web service
2. Navigate to the "Disks" tab
3. Verify that the disk is mounted at `/data` as specified in `render.yaml`
4. If needed, you can create additional disks for backups or other data

### 4. Deploy the Application

1. Go to the "Manual Deploy" tab
2. Select "Clear build cache & deploy" to ensure a clean deployment
3. Monitor the build logs for any errors
4. Once deployed, verify the application is running by checking the health endpoint

## Configuring Twilio for WhatsApp Integration

### 1. Set Up Twilio WhatsApp Sandbox

1. Log in to your Twilio account
2. Navigate to "Messaging" > "Try it out" > "Send a WhatsApp message"
3. Follow the instructions to set up the WhatsApp sandbox

### 2. Configure Webhook URL

1. In the Twilio console, go to "Messaging" > "Settings" > "WhatsApp Sandbox Settings"
2. Set the "When a message comes in" webhook URL to:
   ```
   https://mark-assistant.onrender.com/api/webhook/whatsapp
   ```
3. Set the HTTP method to POST
4. Save the changes

### 3. Test the WhatsApp Integration

1. Send a test message to your WhatsApp sandbox number
2. Check the Render logs to verify the webhook is receiving messages
3. Verify that Mark Assistant is responding correctly

## Configuring Hume EVI for Voice Integration

### 1. Set Up Hume API Access

1. Log in to your Hume AI account
2. Navigate to the API section
3. Generate a new API key with permissions for voice synthesis
4. Add this key to your Render environment variables as `HUME_API_KEY`

### 2. Test Voice Synthesis

1. SSH into your Render instance or use the Render shell
2. Run the voice synthesis test script:
   ```bash
   python -m scripts.test_voice_integration synthesis --text "Hello, this is a test" --language "en"
   ```
3. Verify that the audio file is generated correctly

### 3. Test Voice Message Sending

1. Run the complete integration test:
   ```bash
   python -m scripts.test_voice_integration integration --phone "+34XXXXXXXXX" --message "Hello, this is a test message" --language "en"
   ```
2. Verify that the voice message is received on the specified WhatsApp number

## Setting Up a Custom Domain (Optional)

### 1. Add Your Domain in Render

1. In the Render dashboard, go to your web service
2. Navigate to the "Settings" tab
3. Scroll down to the "Custom Domain" section
4. Click "Add Custom Domain"
5. Enter your domain name (e.g., `mark.centrepsicologiajaume.com`)
6. Click "Save"

### 2. Configure DNS Settings

1. In your DNS provider's dashboard, add a CNAME record:
   - Name: `mark` (or subdomain of your choice)
   - Value: The Render URL provided (e.g., `mark-assistant.onrender.com`)
   - TTL: 3600 (or as recommended by your DNS provider)

2. Wait for DNS propagation (can take up to 48 hours, but usually much faster)

3. Verify the custom domain is working by visiting your domain in a browser

### 3. Update Twilio Webhook URL

1. Update the Twilio webhook URL to use your custom domain:
   ```
   https://mark.centrepsicologiajaume.com/api/webhook/whatsapp
   ```

## Monitoring and Maintenance

### 1. Set Up Monitoring

1. In the Render dashboard, go to your web service
2. Navigate to the "Metrics" tab to view performance metrics
3. Set up alerts for high CPU usage, memory usage, or error rates

### 2. Configure Logging

1. Ensure your application is logging to stdout/stderr
2. View logs in the Render dashboard under the "Logs" tab
3. Consider setting up log forwarding to a service like Datadog or Logtail for more advanced log management

### 3. Set Up Regular Backups

1. Create a backup script that exports important data:
   ```bash
   #!/bin/bash
   # Backup script for Mark Assistant
   
   # Set backup directory
   BACKUP_DIR="/data/backups"
   TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
   
   # Create backup directory if it doesn't exist
   mkdir -p $BACKUP_DIR
   
   # Backup database
   python -m scripts.backup_database --output $BACKUP_DIR/database_$TIMESTAMP.bak
   
   # Backup encryption keys
   python -m scripts.backup_encryption_keys --output $BACKUP_DIR/encryption_keys_$TIMESTAMP.zip
   
   # Backup configuration
   cp -r /app/config $BACKUP_DIR/config_$TIMESTAMP
   
   # Clean up old backups (keep last 7 days)
   find $BACKUP_DIR -name "database_*" -type f -mtime +7 -delete
   find $BACKUP_DIR -name "encryption_keys_*" -type f -mtime +7 -delete
   find $BACKUP_DIR -name "config_*" -type d -mtime +7 -exec rm -rf {} \;
   ```

2. Set up a cron job to run the backup script daily:
   ```
   0 2 * * * /app/scripts/backup.sh >> /data/logs/backup.log 2>&1
   ```

## Scaling the Application

### 1. Vertical Scaling

If you need more resources:

1. In the Render dashboard, go to your web service
2. Navigate to the "Settings" tab
3. Under "Instance Type", select a larger instance type
4. Save the changes

### 2. Horizontal Scaling

For handling more traffic:

1. In the Render dashboard, go to your web service
2. Navigate to the "Settings" tab
3. Under "Scaling", increase the number of instances
4. Save the changes

## Troubleshooting Common Issues

### 1. Deployment Failures

If the deployment fails:

1. Check the build logs for errors
2. Verify that all dependencies are correctly specified in `requirements.txt`
3. Ensure that the start command in `render.yaml` is correct
4. Check that all required environment variables are set

### 2. WhatsApp Integration Issues

If WhatsApp messages are not being received:

1. Verify the Twilio webhook URL is correctly configured
2. Check the Render logs for webhook requests
3. Ensure the Twilio credentials are correct
4. Verify that the WhatsApp sandbox is set up correctly

### 3. Voice Integration Issues

If voice synthesis or sending fails:

1. Check that the Hume API key is correct
2. Verify that the voice configuration in `config/voice.yaml` is correct
3. Check the logs for any errors related to voice processing
4. Ensure that the Twilio media sending capabilities are working

## Security Considerations

### 1. API Key Rotation

Regularly rotate API keys for enhanced security:

1. Generate new API keys in the respective service dashboards
2. Update the environment variables in Render
3. Verify that the application works with the new keys
4. Revoke the old keys

### 2. SSL/TLS Configuration

Render automatically provides SSL/TLS certificates for all domains. Verify:

1. Your application is accessible via HTTPS
2. All webhook URLs use HTTPS
3. The application redirects HTTP to HTTPS

### 3. Regular Security Audits

Perform regular security audits:

1. Run the security verification script:
   ```bash
   python -m scripts.verify_security
   ```
2. Address any issues identified by the script
3. Keep all dependencies updated to patch security vulnerabilities

## Next Steps After Deployment

After successfully deploying Mark Assistant:

1. Conduct thorough testing of all features
2. Set up monitoring and alerting
3. Create a disaster recovery plan
4. Document the deployment process for future reference
5. Train staff on how to use and maintain the system

For additional support or questions about the deployment process, contact the development team at dev@centrepsicologiajaume.com. 