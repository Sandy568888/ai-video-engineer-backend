"""
TTS Adapter - Unified interface for text-to-speech services
Supports VibeVoice (default) with automatic ElevenLabs fallback
"""
import os
import logging
from typing import Optional
from app.services.tts_limits import TTSLimits

logger = logging.getLogger(__name__)

# Global provider state (can be changed via admin endpoint)
_current_provider = os.getenv('TTS_PROVIDER', 'vibevoice').lower()


def set_provider(provider: str) -> bool:
    """Set the TTS provider (for admin override only)"""
    global _current_provider
    provider = provider.lower()
    
    if provider not in ['vibevoice', 'elevenlabs']:
        logger.error(f"Invalid TTS provider: {provider}")
        return False
    
    _current_provider = provider
    logger.info(f"TTS provider manually set to: {provider}")
    return True


def get_current_provider() -> str:
    """Get the current TTS provider"""
    return _current_provider


def generate_audio(
    text: str,
    filename_prefix: str = "audio",
    voice: Optional[str] = None,
    format: str = "wav"
) -> Optional[str]:
    """
    Generate audio from text using the configured TTS provider
    
    Args:
        text: The text to convert to speech
        filename_prefix: Prefix for the output filename
        voice: Voice ID/name (provider-specific)
        format: Audio format (default: wav for HeyGen compatibility)
    
    Returns:
        str: Path to the generated audio file, or None if failed
    
    Note:
        - VibeVoice is used by default
        - If VibeVoice fails, automatically falls back to ElevenLabs
        - Fallback is automatic and does NOT require env var changes
    """
    
    # STEP 1: Validate input limits
    is_valid, error_message = TTSLimits.validate_input(text)
    if not is_valid:
        logger.error(f"❌ Input validation failed: {error_message}")
        raise ValueError(error_message)
    
    # Lazy import to avoid import errors if dependencies not installed
    from app.services.vibevoice_service import VibeVoiceService
    from app.services.elevenlabs_service import ElevenLabsService
    
    audio_path = None
    
    # STEP 2: Try primary provider first
    if _current_provider == 'vibevoice':
        logger.info("Attempting audio generation with VibeVoice (primary)")
        try:
            vibevoice = VibeVoiceService()
            audio_path = vibevoice.generate_voiceover(
                text=text,
                filename_prefix=filename_prefix,
                voice=voice,
                format=format
            )
            
            if audio_path:
                logger.info(f"✅ VibeVoice succeeded: {audio_path}")
                return audio_path
            else:
                logger.warning("⚠️ VibeVoice returned None, falling back to ElevenLabs")
                
        except Exception as e:
            logger.error(f"❌ VibeVoice failed with error: {e}", exc_info=True)
            logger.info("🔄 Falling back to ElevenLabs...")
    
    # STEP 3: Use ElevenLabs (either as primary or fallback)
    logger.info("Using ElevenLabs for audio generation")
    try:
        elevenlabs = ElevenLabsService()
        audio_path = elevenlabs.generate_voiceover(
            text=text,
            voice_id=voice
        )
        
        if audio_path:
            logger.info(f"✅ ElevenLabs succeeded: {audio_path}")
            return audio_path
        else:
            logger.error("❌ ElevenLabs also failed (returned None)")
            return None
            
    except Exception as e:
        logger.error(f"❌ ElevenLabs failed with error: {e}", exc_info=True)
        return None


def get_limits_info() -> dict:
    """Get current TTS input/output limits"""
    return TTSLimits.get_limits_info()


def health_check() -> dict:
    """Check health of all TTS providers"""
    from app.services.vibevoice_service import VibeVoiceService
    from app.services.elevenlabs_service import ElevenLabsService
    
    health = {
        'current_provider': _current_provider,
        'limits': get_limits_info(),
        'providers': {}
    }
    
    # Check VibeVoice
    try:
        vibevoice = VibeVoiceService()
        health['providers']['vibevoice'] = {
            'status': 'configured' if vibevoice.ws_endpoint else 'not_configured',
            'endpoint': vibevoice.ws_endpoint or 'not_set',
            'connection_timeout': vibevoice.connection_timeout,
            'max_retries': vibevoice.max_retries
        }
    except Exception as e:
        health['providers']['vibevoice'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Check ElevenLabs
    try:
        elevenlabs = ElevenLabsService()
        health['providers']['elevenlabs'] = {
            'status': 'configured' if elevenlabs.api_key else 'not_configured',
            'mock_mode': elevenlabs.mock_mode
        }
    except Exception as e:
        health['providers']['elevenlabs'] = {
            'status': 'error',
            'error': str(e)
        }
    
    return health


def get_streaming_config() -> dict:
    """Get streaming TTS configuration"""
    from app.services.streaming_config import StreamingConfig
    config = StreamingConfig()
    return {
        'enabled': config.enabled,
        'chunk_size': config.chunk_size,
        'buffer_size': config.buffer_size,
        'stream_timeout': config.stream_timeout,
        'note': 'Streaming TTS is currently in development'
    }
