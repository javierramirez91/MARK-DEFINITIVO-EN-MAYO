# Voice Integration Guide

This guide provides detailed instructions for integrating voice capabilities into the Mark Assistant using Hume EVI for voice synthesis and Twilio for communication.

## Voice Integration Overview

The voice integration allows Mark to:
- Receive voice messages from patients via WhatsApp
- Transcribe these messages using speech recognition technology
- Generate natural voice responses using Hume EVI
- Send these voice responses through Twilio

## Prerequisites

- Hume AI account with access to the Hume EVI API
- Twilio account configured for WhatsApp Business API
- Voice transcription service (integrated in the `services/voice_processing.py` module)

## Hume EVI Configuration

### Obtaining API Credentials

1. Register for an account at [Hume AI](https://hume.ai/)
2. Navigate to the API section in the dashboard
3. Generate a new API key with permissions for voice synthesis
4. Add this key to your `.env` file:
   ```
   HUME_API_KEY=your_hume_api_key
   ```

### Voice Parameter Configuration

Edit the `config/voice.yaml` file to configure Hume EVI parameters:

```yaml
hume_evi:
  api_key: "${HUME_API_KEY}"
  voice_id: "evi_spanish_female"  # Voice ID to use
  prosody:
    rate: 1.0  # Speech rate (0.5-2.0)
    pitch: 0.0  # Pitch adjustment (-10.0 to 10.0)
    volume: 1.0  # Volume (0.0-2.0)
  emotion:
    empathy: 0.8  # Empathy level (0.0-1.0)
    professional: 0.7  # Professionalism level (0.0-1.0)
  audio:
    format: "mp3"  # Output format (mp3, wav, ogg)
    quality: "high"  # Audio quality (low, medium, high)
    max_duration: 60  # Maximum duration in seconds
```

## Integration with Voice Processing Service

The `services/voice_processing.py` module already contains the basic structure for voice processing. It needs to be expanded to integrate Hume EVI:

```python
# Example implementation in services/voice_processing.py

from hume import HumeClient
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HumeEVIService:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.voice_id = config.get("voice_id")
        self.prosody = config.get("prosody", {})
        self.emotion = config.get("emotion", {})
        self.audio = config.get("audio", {})
        self.client = HumeClient(api_key=self.api_key)
    
    def generate_speech(self, text: str, language: str = "es") -> Optional[bytes]:
        """
        Generates voice audio from text using Hume EVI.
        
        Args:
            text: The text to convert to speech
            language: Language code (es, ca, en, ar)
            
        Returns:
            Audio data in bytes or None if there's an error
        """
        try:
            # Adjust parameters based on language
            voice_id = self._get_voice_for_language(language)
            
            # Call the Hume API
            response = self.client.synthesize_speech(
                text=text,
                voice_id=voice_id,
                prosody=self.prosody,
                emotion=self.emotion,
                audio_format=self.audio.get("format", "mp3")
            )
            
            return response.audio_data
        except Exception as e:
            logger.error(f"Error generating voice with Hume EVI: {str(e)}")
            return None
    
    def _get_voice_for_language(self, language: str) -> str:
        """Selects the appropriate voice based on language."""
        voice_map = {
            "es": "evi_spanish_female",
            "ca": "evi_catalan_female",
            "en": "evi_english_female",
            "ar": "evi_arabic_female"
        }
        return voice_map.get(language, self.voice_id)
```

## Integration with Twilio for Voice Messages

To send voice messages through Twilio, extend the existing WhatsApp service:

```python
# Example implementation in services/whatsapp.py

import os
import uuid
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_voice_message(phone_number: str, audio_data: bytes, mime_type: str = "audio/mp3"):
    """
    Sends a voice message via WhatsApp using Twilio.
    
    Args:
        phone_number: Recipient's phone number
        audio_data: Audio data in bytes
        mime_type: Audio MIME type
    
    Returns:
        bool: True if sending was successful, False otherwise
    """
    try:
        # Temporarily save the audio file
        temp_file_path = f"/tmp/voice_message_{uuid.uuid4()}.mp3"
        with open(temp_file_path, "wb") as f:
            f.write(audio_data)
        
        # Send via Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            media_url=[f"file://{temp_file_path}"],
            from_=f"whatsapp:{WHATSAPP_PHONE_NUMBER}",
            to=f"whatsapp:{phone_number}"
        )
        
        # Delete the temporary file
        os.remove(temp_file_path)
        
        logger.info(f"Voice message sent successfully: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Error sending voice message: {str(e)}")
        return False
```

## Voice Processing Flow

The complete flow for voice processing should include:

1. **Voice Message Reception**:
   - Twilio receives a voice message via WhatsApp
   - The webhook processes the message and extracts the audio URL

2. **Transcription**:
   - The voice processing service downloads the audio
   - It uses a speech recognition service to transcribe the content

3. **Response Processing**:
   - The transcribed text is sent to the AI system (GPT-4)
   - A textual response is generated

4. **Voice Synthesis**:
   - The textual response is sent to Hume EVI
   - An audio file with natural voice is generated

5. **Response Sending**:
   - The audio file is sent to the user via Twilio
   - Optionally, the text response is also sent

## Twilio Webhook Configuration

Configure the Twilio webhook to handle voice messages:

```python
# In backend/routes/webhook.py

from fastapi import APIRouter, Request
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    
    # Determine if it's a voice message
    media_content_type = form_data.get("MediaContentType0", "")
    is_voice_message = media_content_type.startswith("audio/")
    
    if is_voice_message:
        # Get voice message URL
        media_url = form_data.get("MediaUrl0")
        from_number = form_data.get("From").replace("whatsapp:", "")
        
        # Process the voice message
        voice_service = get_voice_processing_service()
        text = await voice_service.transcribe_audio(media_url)
        
        if text:
            # Process the transcribed text
            response_text = await process_message(text, from_number)
            
            # Generate voice response
            hume_service = get_hume_evi_service()
            audio_data = hume_service.generate_speech(response_text)
            
            if audio_data:
                # Send voice response
                whatsapp_service = get_whatsapp_service()
                whatsapp_service.send_voice_message(from_number, audio_data)
            
            # Also send text response
            whatsapp_service.send_text_message(from_number, response_text)
        
        return {"status": "success"}
    else:
        # Process normal text message
        # ...
```

## Voice Integration Testing

To test the voice integration:

1. **Voice Synthesis Test**:
   ```bash
   python -m scripts.test_voice_synthesis --text "Hello, I'm Mark, your virtual assistant. How can I help you today?" --language "en"
   ```

2. **Transcription Test**:
   ```bash
   python -m scripts.test_voice_transcription --audio_file "tests/resources/test_voice_message.mp3"
   ```

3. **Complete Integration Test**:
   ```bash
   python -m scripts.test_voice_integration --phone "+34XXXXXXXXX" --message "Hello, I need to schedule an appointment"
   ```

## Performance Considerations

- **Audio Caching**: Consider implementing a caching system for common responses
- **Asynchronous Processing**: Use background tasks for voice synthesis
- **Size Limits**: Set limits for voice message duration
- **API Usage Monitoring**: Implement a system to monitor Hume API usage

## Troubleshooting

### Common Issues with Hume EVI

1. **Authentication Error**:
   - Verify that the API key is valid
   - Confirm you have permissions for voice synthesis

2. **Voice Quality Issues**:
   - Adjust prosody parameters
   - Experiment with different emotion configurations

3. **Rate Limit Errors**:
   - Implement a queue system for requests
   - Consider upgrading your API plan

### Common Issues with Twilio

1. **Messages Not Delivered**:
   - Check Twilio account status
   - Confirm the phone number is correctly formatted

2. **File Size Errors**:
   - Compress audio files to reduce size
   - Split long messages into multiple files

## Next Steps

After implementing the voice integration:

1. Conduct thorough testing with different languages
2. Adjust voice parameters for each language
3. Implement a feedback system to improve voice quality
4. Consider voice personalization based on conversation context

For additional support, contact the development team at dev@centrepsicologiajaume.com. 