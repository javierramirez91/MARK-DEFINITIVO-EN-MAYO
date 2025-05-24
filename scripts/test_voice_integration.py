#!/usr/bin/env python
"""
Voice Integration Test Script

This script tests the integration between voice processing, Hume EVI, and Twilio.
It allows testing of voice synthesis, transcription, and the complete voice message flow.
"""

import argparse
import os
import sys
import logging
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required modules
try:
    from services.voice_processing import VoiceProcessingService, HumeEVIService
    from services.whatsapp import send_voice_message, send_text_message
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_integration_test")

def load_config():
    """Load voice configuration from config file."""
    try:
        config_path = Path(__file__).parent.parent / "config" / "voice.yaml"
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Replace environment variables
        for key, value in os.environ.items():
            if isinstance(config, dict):
                _replace_env_vars(config, f"${{{key}}}", value)
        
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

def _replace_env_vars(obj, placeholder, value):
    """Recursively replace environment variables in the config."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                _replace_env_vars(v, placeholder, value)
            elif isinstance(v, str) and placeholder in v:
                obj[k] = v.replace(placeholder, value)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                _replace_env_vars(v, placeholder, value)
            elif isinstance(v, str) and placeholder in v:
                obj[i] = v.replace(placeholder, value)

def test_voice_synthesis(text, language="en"):
    """Test voice synthesis using Hume EVI."""
    logger.info(f"Testing voice synthesis for text: '{text}' in language: {language}")
    
    config = load_config()
    hume_config = config.get("hume_evi", {})
    
    # Initialize Hume EVI service
    hume_service = HumeEVIService(hume_config)
    
    # Generate speech
    audio_data = hume_service.generate_speech(text, language)
    
    if audio_data:
        # Save to file for testing
        output_file = f"test_synthesis_{language}.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"Voice synthesis successful. Audio saved to {output_file}")
        return True
    else:
        logger.error("Voice synthesis failed")
        return False

def test_voice_transcription(audio_file):
    """Test voice transcription."""
    logger.info(f"Testing voice transcription for file: {audio_file}")
    
    if not os.path.exists(audio_file):
        logger.error(f"Audio file not found: {audio_file}")
        return False
    
    config = load_config()
    transcription_config = config.get("transcription", {})
    
    # Initialize voice processing service
    voice_service = VoiceProcessingService(transcription_config)
    
    # Transcribe audio
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    
    text = voice_service.transcribe_audio_data(audio_data)
    
    if text:
        logger.info(f"Transcription successful: '{text}'")
        return True
    else:
        logger.error("Transcription failed")
        return False

def test_complete_integration(phone, message, language="en"):
    """Test the complete voice integration flow."""
    logger.info(f"Testing complete voice integration flow")
    logger.info(f"Phone: {phone}, Message: '{message}', Language: {language}")
    
    config = load_config()
    
    # Step 1: Synthesize voice from text
    hume_service = HumeEVIService(config.get("hume_evi", {}))
    audio_data = hume_service.generate_speech(message, language)
    
    if not audio_data:
        logger.error("Voice synthesis failed")
        return False
    
    # Step 2: Send voice message via Twilio
    success = send_voice_message(phone, audio_data)
    
    if not success:
        logger.error("Failed to send voice message")
        return False
    
    # Step 3: Also send text message
    text_success = send_text_message(phone, message)
    
    if not text_success:
        logger.warning("Failed to send text message, but voice message was sent")
    
    logger.info("Complete integration test successful")
    return True

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Test voice integration components")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Synthesis test
    synthesis_parser = subparsers.add_parser("synthesis", help="Test voice synthesis")
    synthesis_parser.add_argument("--text", required=True, help="Text to synthesize")
    synthesis_parser.add_argument("--language", default="en", help="Language code (default: en)")
    
    # Transcription test
    transcription_parser = subparsers.add_parser("transcription", help="Test voice transcription")
    transcription_parser.add_argument("--audio_file", required=True, help="Audio file to transcribe")
    
    # Complete integration test
    integration_parser = subparsers.add_parser("integration", help="Test complete integration")
    integration_parser.add_argument("--phone", required=True, help="Phone number to send message to")
    integration_parser.add_argument("--message", required=True, help="Message to send")
    integration_parser.add_argument("--language", default="en", help="Language code (default: en)")
    
    args = parser.parse_args()
    
    if args.command == "synthesis":
        test_voice_synthesis(args.text, args.language)
    elif args.command == "transcription":
        test_voice_transcription(args.audio_file)
    elif args.command == "integration":
        test_complete_integration(args.phone, args.message, args.language)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 