# Customization Guide

This document provides detailed instructions for customizing and extending the Mark Assistant system to meet specific requirements and adapt to changing needs.

## Prompt Engineering for GPT-4

Mark Assistant's intelligence is powered by GPT-4, which can be customized through careful prompt engineering to optimize its behavior for mental health support.

### System Prompt Structure

The system prompt is the foundation of Mark's behavior and is located at `ai/gpt4/system_prompt.txt`. It follows this structure:

```
# Mark Assistant - Mental Health Support System

## Core Identity
You are Mark, a virtual assistant for the Centre de Psicologia Jaume I. Your primary purpose is to...

## Tone and Communication Style
- Maintain a warm, empathetic tone
- Use clear, simple language
- Avoid clinical jargon when possible
- ...

## Responsibilities
1. Patient intake and scheduling
2. Crisis detection and escalation
3. ...

## Limitations and Boundaries
- Never provide diagnosis
- Do not replace professional therapy
- ...

## Response Framework
When responding to patients, follow this structure:
1. Acknowledge their concern
2. Provide supportive information
3. ...
```

### Customizing the System Prompt

When modifying the system prompt, follow these guidelines:

1. **Maintain Core Functionality**: Don't remove critical sections like crisis detection or ethical boundaries
2. **Test Thoroughly**: After changes, test with various scenarios to ensure appropriate responses
3. **Version Control**: Keep backups of previous prompts before making significant changes
4. **Documentation**: Comment changes and reasoning within the prompt file

### Function Calling Configuration

GPT-4 can be configured to use specific functions for structured outputs. These are defined in `ai/gpt4/function_definitions.json`:

```json
{
  "functions": [
    {
      "name": "schedule_appointment",
      "description": "Schedule a new appointment for a patient",
      "parameters": {
        "type": "object",
        "properties": {
          "patient_id": {
            "type": "string",
            "description": "The unique identifier for the patient"
          },
          "appointment_type": {
            "type": "string",
            "enum": ["initial_consultation", "therapy_session", "follow_up"],
            "description": "The type of appointment to schedule"
          },
          "preferred_date": {
            "type": "string",
            "format": "date",
            "description": "The preferred date for the appointment (YYYY-MM-DD)"
          },
          "preferred_time": {
            "type": "string",
            "description": "The preferred time for the appointment (HH:MM)"
          },
          "therapist_preference": {
            "type": "string",
            "description": "Optional preference for a specific therapist"
          }
        },
        "required": ["patient_id", "appointment_type", "preferred_date"]
      }
    },
    // Additional functions...
  ]
}
```

To add a new function:

1. Define the function schema in the JSON file
2. Implement the corresponding handler in `ai/function_handlers/`
3. Register the function in `ai/function_registry.py`
4. Test the function with various inputs

## Conversation Playbooks

Mark uses conversation playbooks to handle specific scenarios with predefined flows. These are located in `ai/playbooks/`.

### Playbook Structure

Each playbook is a YAML file with the following structure:

```yaml
name: "Initial Patient Intake"
description: "Guide for collecting initial information from new patients"
trigger:
  type: "intent"
  value: "new_patient"
  confidence_threshold: 0.85

steps:
  - id: "welcome"
    message: "Welcome to Centre de Psicologia Jaume I. I'm Mark, your virtual assistant. I'll help you get started. Could you please tell me your name?"
    next: "collect_name"
    
  - id: "collect_name"
    input:
      entity: "patient.name"
      validation: "^[A-Za-z\\s]{2,50}$"
      error_message: "I didn't catch your name correctly. Could you please provide your full name?"
    next: "collect_contact"
    
  # Additional steps...
    
  - id: "completion"
    message: "Thank you for providing your information. A therapist will review it shortly and we'll contact you to confirm your appointment."
    action:
      type: "function"
      name: "create_patient_record"
    next: "end"
```

### Creating New Playbooks

To create a new playbook:

1. Identify the conversation flow you want to automate
2. Create a new YAML file in the playbooks directory
3. Define the trigger conditions and steps
4. Test the playbook with sample conversations
5. Refine based on testing results

## Language Customization

Mark supports multiple languages, with customization options for each language.

### Adding a New Language

To add support for a new language:

1. Add the language to the supported languages list in `config/language.yaml`
2. Create language-specific response templates in `ai/languages/{language_code}/responses.yaml`
3. Add language detection support in the language detection module
4. Test the language detection and responses

### Response Templates

Language-specific responses are stored in YAML files:

```yaml
greeting:
  formal: "Hello, welcome to Centre de Psicologia Jaume I. How may I assist you today?"
  casual: "Hi there! How can I help you today?"

appointment_confirmation:
  template: "Your appointment has been scheduled for {date} at {time} with {therapist}."

error_messages:
  general: "I'm sorry, but I encountered an issue. Please try again or contact our support team."
  # Additional error messages...
```

## Crisis Detection System

The crisis detection system can be customized to adjust sensitivity and response protocols.

### Crisis Keywords and Patterns

Crisis detection patterns are defined in `ai/security/crisis_detection.yaml`:

```yaml
severity_levels:
  - name: "severe"
    escalation: "immediate"
    notification: ["on_call_therapist", "clinic_director"]
  - name: "moderate"
    escalation: "within_hour"
    notification: ["assigned_therapist"]
  - name: "mild"
    escalation: "follow_up"
    notification: ["patient_notes"]

patterns:
  - pattern: "(?i)(kill|hurt|harm) (myself|me|my)"
    severity: "severe"
  - pattern: "(?i)I (don't|do not) want to (live|be alive|exist)"
    severity: "severe"
  - pattern: "(?i)(feeling|feel) (hopeless|worthless)"
    severity: "moderate"
  # Additional patterns...
```

### Customizing Crisis Detection

To customize the crisis detection system:

1. Modify the patterns in the YAML file
2. Adjust severity levels and escalation protocols
3. Test with sample crisis scenarios
4. Review with mental health professionals
5. Implement feedback and refine

## Integration Customization

Mark integrates with various external services that can be customized.

### Calendly Integration

Configure the Calendly integration in `config/integrations/calendly.yaml`:

```yaml
api_key: "${CALENDLY_API_KEY}"
webhook_url: "${BASE_URL}/api/webhook/calendly"
event_types:
  - name: "Initial Consultation"
    duration: 60
    uri: "https://calendly.com/centrepsicologia/initial"
  - name: "Therapy Session"
    duration: 50
    uri: "https://calendly.com/centrepsicologia/therapy"
  # Additional event types...
```

### WhatsApp Integration

Configure the WhatsApp integration in `config/integrations/whatsapp.yaml`:

```yaml
provider: "twilio"
account_sid: "${TWILIO_ACCOUNT_SID}"
auth_token: "${TWILIO_AUTH_TOKEN}"
phone_number: "${WHATSAPP_PHONE_NUMBER}"
webhook_url: "${BASE_URL}/api/webhook/whatsapp"
template_messages:
  welcome: "Welcome to Centre de Psicologia Jaume I. I'm Mark, your virtual assistant. How can I help you today?"
  appointment_confirmation: "Your appointment has been confirmed for {{1}} at {{2}}."
  # Additional templates...
```

## UI Customization

The admin panel and patient portal UI can be customized to match branding requirements.

### Theme Configuration

The theme is configured in `frontend/src/styles/theme.js`:

```javascript
const theme = {
  colors: {
    primary: '#4A6FA5',
    secondary: '#6B8F71',
    accent: '#F9A826',
    background: '#F5F7FA',
    text: '#333333',
    error: '#D64045',
    success: '#4CAF50',
    warning: '#FF9800',
    info: '#2196F3',
  },
  fonts: {
    body: "'Roboto', sans-serif",
    heading: "'Montserrat', sans-serif",
  },
  fontSizes: {
    small: '0.875rem',
    medium: '1rem',
    large: '1.25rem',
    xlarge: '1.5rem',
    xxlarge: '2rem',
  },
  // Additional theme properties...
};
```

### Logo and Branding

To customize branding elements:

1. Replace logo files in `frontend/public/images/`
2. Update favicon and manifest in `frontend/public/`
3. Modify the theme colors to match brand guidelines
4. Update email templates in `backend/templates/email/`

## Advanced GPT-4 Customization

### Fine-tuning GPT-4 Behavior

For more advanced customization of GPT-4's behavior:

1. **Few-shot Examples**: Add examples in the system prompt to guide responses:

```
## Examples
User: "I've been feeling sad lately."
Assistant: "I'm sorry to hear you've been feeling sad. Many people experience periods of sadness. Could you share a bit more about what's been going on? This will help me understand how to best support you."

User: "I need to schedule an appointment."
Assistant: "I'd be happy to help you schedule an appointment. Could you let me know what type of appointment you're looking for (initial consultation or follow-up), and your preferred day and time?"
```

2. **Chain-of-Thought Prompting**: Guide GPT-4's reasoning process:

```
When responding to patient concerns, follow this reasoning process:
1. Identify the primary concern or request
2. Consider if this is within your scope or requires professional intervention
3. Determine the appropriate level of empathy needed
4. Formulate a response that is helpful but does not overstep boundaries
5. Include appropriate next steps or resources
```

3. **Temperature Adjustment**: Configure the temperature parameter in `config/ai.yaml` to control response randomness:
   - Lower values (0.2-0.5): More consistent, deterministic responses
   - Higher values (0.7-1.0): More creative, varied responses

### Custom GPT-4 Configurations for Different Scenarios

Create specialized configurations for different interaction types:

```yaml
# config/ai.yaml
gpt4_configurations:
  default:
    model: "gpt-4-turbo"
    temperature: 0.7
    max_tokens: 4000
    system_prompt_path: "ai/gpt4/system_prompt.txt"
  
  crisis_mode:
    model: "gpt-4-turbo"
    temperature: 0.3  # Lower for more conservative responses
    max_tokens: 2000
    system_prompt_path: "ai/gpt4/crisis_prompt.txt"
  
  appointment_scheduling:
    model: "gpt-4-turbo"
    temperature: 0.4
    max_tokens: 1500
    system_prompt_path: "ai/gpt4/scheduling_prompt.txt"
```

## Performance Optimization

### GPT-4 Token Usage Optimization

To optimize token usage and reduce API costs:

1. **Context Summarization**: Implement conversation summarization to reduce context length:

```python
def summarize_conversation(messages, max_tokens=1000):
    """Summarize a conversation to reduce token count while preserving key information."""
    if token_count(messages) <= max_tokens:
        return messages
        
    # Create a summary request to GPT-4
    summary_prompt = "Summarize the following conversation while preserving all key information, patient concerns, and appointment details:"
    for msg in messages[:len(messages)-3]:  # Exclude the most recent messages
        summary_prompt += f"\n{msg['role']}: {msg['content']}"
    
    summary = get_gpt4_summary(summary_prompt)
    
    # Replace older messages with summary
    summarized_messages = [
        {"role": "system", "content": "Previous conversation summary: " + summary}
    ]
    summarized_messages.extend(messages[len(messages)-3:])  # Keep the most recent messages
    
    return summarized_messages
```

2. **Prompt Compression**: Techniques to reduce prompt size:
   - Use abbreviations in system prompts (internal only)
   - Remove redundant examples
   - Use more concise language
   - Split complex functions into smaller, focused ones

3. **Caching Common Responses**: Implement response caching for frequent queries:

```python
response_cache = {}

def get_cached_response(query, ttl=3600):
    """Get a cached response if available and not expired."""
    normalized_query = normalize_query(query)
    cache_key = hash(normalized_query)
    
    if cache_key in response_cache:
        timestamp, response = response_cache[cache_key]
        if time.time() - timestamp < ttl:
            return response
    
    return None

def cache_response(query, response):
    """Cache a response for future use."""
    normalized_query = normalize_query(query)
    cache_key = hash(normalized_query)
    response_cache[cache_key] = (time.time(), response)
```

## Next Steps

After customizing Mark Assistant, consider these next steps:

1. **User Testing**: Conduct thorough testing with real users to gather feedback
2. **Performance Monitoring**: Set up monitoring for response times, token usage, and error rates
3. **Continuous Improvement**: Establish a process for regular review and refinement
4. **Documentation Updates**: Keep documentation updated with all customizations
5. **Training**: Provide training for staff on how to use and maintain the customized system

For additional support or custom development, contact the development team at dev@centrepsicologiajaume.com.
