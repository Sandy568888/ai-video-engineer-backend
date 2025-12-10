"""ElevenLabs service for voice synthesis"""
import os
import logging
import wave

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
            # Create actual mock audio file
            filename = f"mock_audio_{os.urandom(4).hex()}.wav"
            self._create_mock_audio(filename)
            return filename
        
        try:
            from elevenlabs import generate, save
            audio = generate(text=text, voice=voice_id or self.voice_id, api_key=self.api_key)
            filename = f"voiceover_{os.urandom(8).hex()}.mp3"
            save(audio, filename)
            return filename
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            return None
    
    def _create_mock_audio(self, filename):
        """Create a mock WAV file"""
        try:
            sample_rate = 24000
            duration = 1  # 1 second
            num_samples = sample_rate * duration
            silent_audio = b'\x00\x00' * num_samples
            
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silent_audio)
            
            logger.info(f"Created mock audio: {filename}")
        except Exception as e:
            logger.error(f"Failed to create mock audio: {e}")
            raise
