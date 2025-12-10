"""ElevenLabs service for voice synthesis"""
import os
import logging
logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Check both MOCK_MODE and ELEVENLABS_MOCK_MODE
        general_mock = os.getenv('MOCK_MODE', 'False').lower() == 'true'
        specific_mock = os.getenv('ELEVENLABS_MOCK_MODE', 'False').lower() == 'true'
        self.mock_mode = general_mock or specific_mock
        
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'default')
        
        logger.info(f"ElevenLabs initialized: mock_mode={self.mock_mode}")
    
    def generate_voiceover(self, text, voice_id=None):
        """Generate voiceover from text"""
        if self.mock_mode:
            logger.info("MOCK: Generating ElevenLabs voiceover")
            return "mock_audio.mp3"
        
        try:
            from elevenlabs import generate, save
            audio = generate(text=text, voice=voice_id or self.voice_id, api_key=self.api_key)
            filename = f"voiceover_{os.urandom(8).hex()}.mp3"
            save(audio, filename)
            return filename
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            return None
