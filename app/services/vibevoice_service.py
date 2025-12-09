"""VibeVoice service for voice synthesis via WebSocket streaming"""
import os
import json
import logging
import asyncio
import websockets
import wave
from typing import Optional

logger = logging.getLogger(__name__)


class VibeVoiceService:
    """VibeVoice TTS client using WebSocket streaming"""
    
    def __init__(self):
        self.ws_endpoint = os.getenv('VIBEVOICE_WS_ENDPOINT')
        self.mock_mode = os.getenv('MOCK_MODE', 'False') == 'True'
        self.sample_rate = int(os.getenv('VIBEVOICE_SAMPLE_RATE', '24000'))
        self.voice_id = os.getenv('VIBEVOICE_VOICE_ID', 'default')
        
        if not self.ws_endpoint and not self.mock_mode:
            logger.warning("⚠️ VIBEVOICE_WS_ENDPOINT not set and MOCK_MODE is disabled")
    
    def generate_voiceover(
        self,
        text: str,
        filename_prefix: str = "vibevoice_audio",
        voice: Optional[str] = None,
        format: str = "wav"
    ) -> Optional[str]:
        """Generate voiceover from text using VibeVoice WebSocket API"""
        
        if self.mock_mode:
            logger.info("🎭 MOCK MODE: Generating mock VibeVoice audio")
            return self._generate_mock_audio(filename_prefix)
        
        if not self.ws_endpoint:
            raise ValueError("VIBEVOICE_WS_ENDPOINT not configured")
        
        if format != 'wav':
            logger.warning(f"Format '{format}' requested, but VibeVoice only outputs WAV")
        
        output_filename = f"{filename_prefix}_{os.urandom(8).hex()}.wav"
        
        try:
            audio_data = asyncio.run(self._generate_via_websocket(text, voice))
            
            if audio_data:
                self._save_wav(audio_data, output_filename)
                logger.info(f"✅ VibeVoice audio saved: {output_filename}")
                return output_filename
            else:
                logger.error("❌ VibeVoice returned no audio data")
                return None
                
        except Exception as e:
            logger.error(f"❌ VibeVoice generation failed: {e}", exc_info=True)
            return None
    
    async def _generate_via_websocket(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[bytes]:
        """Connect to VibeVoice WebSocket and stream audio generation"""
        
        voice_to_use = voice or self.voice_id
        audio_chunks = []
        
        try:
            logger.info(f"🔌 Connecting to VibeVoice WebSocket: {self.ws_endpoint}")
            
            async with websockets.connect(self.ws_endpoint) as websocket:
                
                request = {
                    "action": "synthesize",
                    "text": text,
                    "voice": voice_to_use,
                    "sample_rate": self.sample_rate,
                    "format": "pcm"
                }
                
                await websocket.send(json.dumps(request))
                logger.info(f"📤 Sent TTS request for {len(text)} characters")
                
                while True:
                    try:
                        message = await websocket.recv()
                        
                        if isinstance(message, str):
                            response = json.loads(message)
                            
                            if response.get('status') == 'completed':
                                logger.info("✅ Audio generation completed")
                                break
                            elif response.get('status') == 'error':
                                error_msg = response.get('message', 'Unknown error')
                                logger.error(f"❌ VibeVoice error: {error_msg}")
                                return None
                            else:
                                logger.debug(f"Status update: {response}")
                        
                        elif isinstance(message, bytes):
                            audio_chunks.append(message)
                            logger.debug(f"📥 Received audio chunk: {len(message)} bytes")
                    
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket connection closed")
                        break
                
                if audio_chunks:
                    full_audio = b''.join(audio_chunks)
                    logger.info(f"✅ Total audio data: {len(full_audio)} bytes")
                    return full_audio
                else:
                    logger.warning("⚠️ No audio chunks received")
                    return None
        
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}", exc_info=True)
            return None
    
    def _save_wav(self, audio_data: bytes, filename: str) -> None:
        """Save raw PCM audio as WAV file"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            logger.info(f"💾 WAV file saved: {filename}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save WAV: {e}", exc_info=True)
            raise
    
    def _generate_mock_audio(self, filename_prefix: str) -> str:
        """Generate a mock WAV file for testing"""
        filename = f"{filename_prefix}_mock.wav"
        
        try:
            sample_rate = 24000
            duration = 1
            num_samples = sample_rate * duration
            silent_audio = b'\x00\x00' * num_samples
            
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silent_audio)
            
            logger.info(f"🎭 Mock audio created: {filename}")
            return filename
        
        except Exception as e:
            logger.error(f"❌ Failed to create mock audio: {e}")
            raise
