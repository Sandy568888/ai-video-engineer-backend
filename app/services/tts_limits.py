"""TTS Input/Output Limits and Validation"""
import os
import logging

logger = logging.getLogger(__name__)


class TTSLimits:
    """TTS input and output validation"""
    
    # Input limits
    MAX_INPUT_CHARS = int(os.getenv('TTS_MAX_INPUT_CHARS', '3000'))
    MIN_INPUT_CHARS = int(os.getenv('TTS_MIN_INPUT_CHARS', '1'))
    
    # Output limits
    MAX_AUDIO_DURATION_SECONDS = int(os.getenv('TTS_MAX_AUDIO_DURATION', '90'))
    
    # Character per second estimate (for duration calculation)
    CHARS_PER_SECOND = int(os.getenv('TTS_CHARS_PER_SECOND', '15'))
    
    @classmethod
    def validate_input(cls, text: str) -> tuple[bool, str]:
        """
        Validate input text before TTS generation
        
        Returns:
            (is_valid, error_message)
        """
        
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        text_length = len(text)
        
        if text_length < cls.MIN_INPUT_CHARS:
            return False, f"Text too short (minimum {cls.MIN_INPUT_CHARS} characters)"
        
        if text_length > cls.MAX_INPUT_CHARS:
            return False, f"Text too long (maximum {cls.MAX_INPUT_CHARS} characters, got {text_length})"
        
        # Estimate audio duration
        estimated_duration = text_length / cls.CHARS_PER_SECOND
        
        if estimated_duration > cls.MAX_AUDIO_DURATION_SECONDS:
            return False, (
                f"Text would generate audio longer than {cls.MAX_AUDIO_DURATION_SECONDS}s "
                f"(estimated {estimated_duration:.1f}s). Please shorten your script."
            )
        
        logger.info(f"✅ Input validated: {text_length} chars, ~{estimated_duration:.1f}s audio")
        return True, ""
    
    @classmethod
    def get_limits_info(cls) -> dict:
        """Get current limits configuration"""
        return {
            'max_input_chars': cls.MAX_INPUT_CHARS,
            'min_input_chars': cls.MIN_INPUT_CHARS,
            'max_audio_duration_seconds': cls.MAX_AUDIO_DURATION_SECONDS,
            'chars_per_second_estimate': cls.CHARS_PER_SECOND
        }
