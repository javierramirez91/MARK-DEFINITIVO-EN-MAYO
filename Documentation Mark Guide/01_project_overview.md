# Project Overview - Mark Assistant

## Introduction

Mark is a multilingual virtual assistant specifically designed for the Centre de Psicologia Jaume I. This assistant provides patient care through WhatsApp, manages appointments, processes payments, and facilitates video conferences, all with a focus on security, privacy, and user experience.

## Purpose and Objectives

The main purpose of Mark is to improve the patient experience at the center and optimize administrative processes through:

1. **24/7 Assistance**: Providing continuous support to patients, even outside the center's business hours.
2. **Efficient Management**: Automating administrative tasks such as appointment scheduling and reminders.
3. **Multilingualism**: Serving patients in Spanish, Catalan, English, and Arabic.
4. **Security and Privacy**: Ensuring the confidentiality of conversations and sensitive data.
5. **Crisis Detection**: Identifying risk situations and escalating them appropriately.

## General Architecture

Mark is built with a modular architecture that facilitates its maintenance and scalability:

```
mark-assistant/
├── admin/                  # Web administration panel
├── ai/                     # Artificial intelligence components
│   ├── gpt4/               # GPT-4 client and prompts
│   ├── claude/             # Claude client and prompts (alternative)
│   ├── conversation/       # Conversation management
│   ├── security/           # Security components
│   └── language_detection/ # Language detection
├── backend/                # API server and services
├── core/                   # Central configuration
├── database/               # Database access
├── docs/                   # Documentation
├── i18n/                   # Internationalization
├── services/               # External service integrations
└── tests/                  # Automated tests
```

## Main Features

### Multilingualism
- Complete support for Spanish, Catalan, English, and Arabic
- Automatic language detection based on machine learning
- Language maintenance throughout the conversation

### WhatsApp Integration
- Bidirectional communication through Twilio API
- Support for text and voice messages
- Automatic notifications

### Appointment Management
- Integration with Calendly for scheduling
- Automatic reminders
- Rescheduling and cancellation

### Payment Processing
- Integration with Stripe
- Generation of payment links
- Transaction verification

### Video Conferences
- Integration with Zoom
- Automatic meeting creation
- Sending links to patients

### Artificial Intelligence
- Primarily uses GPT-4 from OpenAI for natural language processing
- Alternative support for Claude from Anthropic as a backup option
- Playbook system for different scenarios
- Enhanced contextual memory

### Security
- End-to-end encryption for all conversations
- Automatic key rotation
- Threat detection and risk situations

### Administration Panel
- Web interface for patient management
- Analytical dashboard for monitoring
- System configuration

## Technologies Used

### Backend
- Python 3.10+
- FastAPI
- Uvicorn/Gunicorn
- SQLAlchemy

### Artificial Intelligence
- GPT-4 API (OpenAI) as primary AI model
- Claude API (Anthropic) as alternative option
- LangChain
- FastText and Transformers for language detection

### Database
- Cloudflare D1 (distributed SQLite)

### Frontend (Administration Panel)
- HTML/CSS/JavaScript
- Bootstrap 5
- Plotly/Dash for visualizations

### External Services
- Twilio (WhatsApp)
- Calendly (Appointments)
- Stripe (Payments)
- Zoom (Video Conferences)

### Deployment Options
- Render (primary cloud platform for deployment)
- AWS/Azure/GCP (alternative options)
- Docker containers for consistent deployment

## Current Project Status

The project has completed the initial development phase and the following improvements have been implemented:

1. Machine learning-based language detector
2. Enhanced contextual memory
3. Voice message support
4. End-to-end encryption
5. Threat detection system
6. Analytical dashboard
7. GPT-4 integration for advanced natural language understanding

The next phase consists of production deployment on Render and complete integration with the existing systems of the Centre de Psicologia Jaume I.

## Key Contacts

- **Project Manager**: Dina (Centre de Psicologia Jaume I)
- **Contact Phone**: +34 637885915
- **Email**: info@centrepsicologiajaumeprimer.com 