"""
TTS Adapter with Analytics - Unified interface for text-to-speech services
"""
import os
import time
import logging
from typing import Optional
from app.services.tts_limits import TTSLimits
from app.services.tts_analytics import TTSAnalytics
from app.services.tts_cache import TTSCache

logger = logging.getLogger(__name__)

# Global provider state
_current_provider = os.getenv('TTS_PROVIDER', 'vibevoice').lower()

# Analytics instance
_analytics = TTSAnalytics()

# Cache instance
_cache = TTSCache()


def set_provider(provider: str) -> bool:
    """Set the TTS provider"""
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
    format: str = "wav",
    video_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Optional[str]:
    """
    Generate audio with analytics tracking
    """
    
    start_time = time.time()
    fallback_triggered = False
    retry_count = 0
    provider_used = _current_provider
    status = 'failed'
    error_message = None
    audio_path = None
    
    try:
        # Validate input
        is_valid, validation_error = TTSLimits.validate_input(text)
        if not is_valid:
            error_message = validation_error
            raise ValueError(validation_error)
        
        # Import services
        from app.services.vibevoice_service import VibeVoiceService
        from app.services.elevenlabs_service import ElevenLabsService
        
        # Try primary provider
        if _current_provider == 'vibevoice':
            logger.info("Attempting VibeVoice (primary)")
            try:
                vibevoice = VibeVoiceService()
                retry_count = vibevoice.max_retries
                audio_path = vibevoice.generate_voiceover(
                    text=text,
                    filename_prefix=filename_prefix,
                    voice=voice,
                    format=format
                )
                
                if audio_path:
                    logger.info(f"✅ VibeVoice succeeded: {audio_path}")
                    status = 'success'
                    provider_used = 'vibevoice'
                else:
                    logger.warning("⚠️ VibeVoice returned None, falling back")
                    fallback_triggered = True
                    
            except Exception as e:
                logger.error(f"❌ VibeVoice failed: {e}")
                error_message = str(e)
                fallback_triggered = True
        
        # Use ElevenLabs (primary or fallback)
        if not audio_path:
            logger.info("Using ElevenLabs")
            provider_used = 'elevenlabs'
            
            try:
                elevenlabs = ElevenLabsService()
                audio_path = elevenlabs.generate_voiceover(
                    text=text,
                    voice_id=voice
                )
                
                if audio_path:
                    logger.info(f"✅ ElevenLabs succeeded: {audio_path}")
                    status = 'fallback_success' if fallback_triggered else 'success'
                else:
                    logger.error("❌ ElevenLabs failed (returned None)")
                    status = 'failed'
                    error_message = "ElevenLabs returned None"
                    
            except Exception as e:
                logger.error(f"❌ ElevenLabs failed: {e}")
                status = 'failed'
                error_message = str(e)
        
        return audio_path
        
    finally:
        # Log analytics
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Estimate audio duration (rough calculation)
        audio_duration = len(text) / 15.0 if text else None  # ~15 chars/sec
        
        _analytics.log_generation(
            video_id=video_id or 'unknown',
            user_id=user_id or 'anonymous',
            provider=provider_used,
            fallback_triggered=fallback_triggered,
            execution_time_ms=execution_time_ms,
            audio_duration_seconds=audio_duration,
            text_length=len(text),
            voice_id=voice,
            status=status,
            error_message=error_message,
            retry_count=retry_count
        )


def get_analytics_stats(days: int = 1) -> dict:
    """Get TTS analytics statistics"""
    return _analytics.get_stats(days)


def get_limits_info() -> dict:
    """Get current TTS limits"""
    return TTSLimits.get_limits_info()


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
