"""Language Detection and Provider Routing"""
import os
import logging
from typing import Optional, Tuple
import re

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect language and route to appropriate TTS provider"""
    
    # Language detection patterns (simple heuristics)
    LANGUAGE_PATTERNS = {
        'en': r'[a-zA-Z]',
        'es': r'[áéíóúñü¿¡]',
        'fr': r'[àâäæçéèêëïîôùûü]',
        'de': r'[äöüß]',
        'it': r'[àèéìíîòóùú]',
        'pt': r'[ãâáàçéêíóôõú]',
        'zh': r'[\u4e00-\u9fff]',
        'ja': r'[\u3040-\u309f\u30a0-\u30ff]',
        'ko': r'[\uac00-\ud7af]',
        'ar': r'[\u0600-\u06ff]',
        'ru': r'[а-яА-ЯёЁ]',
    }
    
    LANGUAGE_NAMES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'ru': 'Russian',
    }
    
    def __init__(self):
        # Provider routing configuration
        self.vibevoice_languages = os.getenv(
            'VIBEVOICE_SUPPORTED_LANGUAGES',
            'en'
        ).split(',')
        
        self.elevenlabs_languages = os.getenv(
            'ELEVENLABS_SUPPORTED_LANGUAGES',
            'en,es,fr,de,it,pt,zh,ja,ko,ar,ru'
        ).split(',')
        
        self.default_provider = os.getenv('TTS_PROVIDER', 'vibevoice')
        
        logger.info(f"Language routing initialized:")
        logger.info(f"  VibeVoice languages: {self.vibevoice_languages}")
        logger.info(f"  ElevenLabs languages: {self.elevenlabs_languages}")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language from text
        
        Args:
            text: Input text
        
        Returns:
            (language_code, confidence)
        """
        
        if not text or not text.strip():
            return 'en', 0.0
        
        # Count character matches for each language
        scores = {}
        text_length = len(text)
        
        for lang_code, pattern in self.LANGUAGE_PATTERNS.items():
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            scores[lang_code] = matches / text_length if text_length > 0 else 0
        
        # Get language with highest score
        detected_lang = max(scores.items(), key=lambda x: x[1])
        lang_code, confidence = detected_lang
        
        # Default to English if confidence is too low
        if confidence < 0.1:
            lang_code = 'en'
            confidence = 0.5
        
        lang_name = self.LANGUAGE_NAMES.get(lang_code, 'Unknown')
        logger.info(f"🌍 Detected language: {lang_name} ({lang_code}) - confidence: {confidence:.2%}")
        
        return lang_code, confidence
    
    def route_to_provider(
        self,
        text: str,
        force_provider: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Determine which TTS provider to use based on language
        
        Args:
            text: Input text
            force_provider: Force specific provider (optional)
        
        Returns:
            (provider, language_code, confidence)
        """
        
        # Detect language
        lang_code, confidence = self.detect_language(text)
        
        # If provider is forced, use it
        if force_provider:
            logger.info(f"🔒 Forced provider: {force_provider}")
            return force_provider, lang_code, confidence
        
        # Route based on language support
        if lang_code in self.vibevoice_languages:
            provider = 'vibevoice'
            logger.info(f"✅ Routing to VibeVoice (language: {lang_code})")
        elif lang_code in self.elevenlabs_languages:
            provider = 'elevenlabs'
            logger.info(f"🔄 Routing to ElevenLabs (language: {lang_code})")
        else:
            # Default fallback
            provider = self.default_provider
            logger.warning(f"⚠️ Language {lang_code} not explicitly supported, using default: {provider}")
        
        return provider, lang_code, confidence
    
    def get_supported_languages(self) -> dict:
        """Get list of supported languages by provider"""
        return {
            'vibevoice': [
                {'code': code, 'name': self.LANGUAGE_NAMES.get(code, code)}
                for code in self.vibevoice_languages
            ],
            'elevenlabs': [
                {'code': code, 'name': self.LANGUAGE_NAMES.get(code, code)}
                for code in self.elevenlabs_languages
            ]
        }
