"""VibeVoice service with timeout, retry, and fallback logic"""
import os
import json
import logging
import asyncio
import websockets
import wave
from typing import Optional
from datetime import datetime
from app.services.voice_config import VoiceConfig

logger = logging.getLogger(__name__)


class VibeVoiceService:
    """VibeVoice TTS client with WebSocket streaming, timeouts, and retries"""
    
    def __init__(self):
        self.ws_endpoint = os.getenv('VIBEVOICE_WS_ENDPOINT')
        self.mock_mode = os.getenv('MOCK_MODE', 'False') == 'True'
        self.sample_rate = int(os.getenv('VIBEVOICE_SAMPLE_RATE', '24000'))
        self.voice_id = os.getenv('VIBEVOICE_VOICE_ID', 'default')
        
        # Voice consistency config
        self.voice_config = VoiceConfig.from_env()
        
        # Timeout & Retry Configuration
        self.connection_timeout = int(os.getenv('VIBEVOICE_CONNECTION_TIMEOUT', '10'))
        self.chunk_timeout = int(os.getenv('VIBEVOICE_CHUNK_TIMEOUT', '5'))
        self.max_retries = int(os.getenv('VIBEVOICE_MAX_RETRIES', '2'))
        
        if not self.ws_endpoint and not self.mock_mode:
            logger.warning("⚠️ VIBEVOICE_WS_ENDPOINT not set and MOCK_MODE is disabled")
    
    def generate_voiceover(
        self,
        text: str,
        filename_prefix: str = "vibevoice_audio",
        voice: Optional[str] = None,
        format: str = "wav"
    ) -> Optional[str]:
        """
        Generate voiceover with retry logic
        
        Attempts:
        1. First attempt
        2. Retry 1 (if fails)
        3. Retry 2 (if fails)
        4. Return None → triggers ElevenLabs fallback in tts_adapter
        """
        
        if self.mock_mode:
            logger.info("🎭 MOCK MODE: Generating mock VibeVoice audio")
            return self._generate_mock_audio(filename_prefix)
        
        if not self.ws_endpoint:
            raise ValueError("VIBEVOICE_WS_ENDPOINT not configured")
        
        if format != 'wav':
            logger.warning(f"Format '{format}' requested, but VibeVoice only outputs WAV")
        
        output_filename = f"{filename_prefix}_{os.urandom(8).hex()}.wav"
        
        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 VibeVoice attempt {attempt}/{self.max_retries}")
                
                audio_data = asyncio.run(
                    self._generate_via_websocket_with_timeout(text, voice)
                )
                
                if audio_data:
                    self._save_wav(audio_data, output_filename)
                    logger.info(f"✅ VibeVoice succeeded on attempt {attempt}: {output_filename}")
                    return output_filename
                else:
                    logger.warning(f"⚠️ VibeVoice attempt {attempt} returned no data")
                    
            except asyncio.TimeoutError as e:
                logger.error(f"⏱️ VibeVoice attempt {attempt} timed out: {e}")
                if attempt < self.max_retries:
                    logger.info(f"🔄 Retrying in 1 second...")
                    asyncio.run(asyncio.sleep(1))
                    
            except Exception as e:
                logger.error(f"❌ VibeVoice attempt {attempt} failed: {e}", exc_info=True)
                if attempt < self.max_retries:
                    logger.info(f"🔄 Retrying in 1 second...")
                    asyncio.run(asyncio.sleep(1))
        
        # All retries exhausted
        logger.error(f"❌ VibeVoice failed after {self.max_retries} attempts")
        return None
    
    async def _generate_via_websocket_with_timeout(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate audio with connection and chunk timeouts"""
        
        try:
            # Apply connection timeout
            return await asyncio.wait_for(
                self._generate_via_websocket(text, voice),
                timeout=self.connection_timeout + 30  # Connection + generation time
            )
        except asyncio.TimeoutError:
            logger.error(f"⏱️ WebSocket generation timed out after {self.connection_timeout + 30}s")
            raise
    
    async def _generate_via_websocket(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[bytes]:
        """Connect to VibeVoice WebSocket and stream audio generation"""
        
        voice_to_use = voice or self.voice_id
        audio_chunks = []
        
        try:
            logger.info(f"🔌 Connecting to VibeVoice: {self.ws_endpoint}")
            
            # Connection timeout
            async with asyncio.timeout(self.connection_timeout):
                websocket = await websockets.connect(self.ws_endpoint)
            
            try:
                request = {
                    "action": "synthesize",
                    "text": text,
                    "voice": voice_to_use,
                    "sample_rate": self.sample_rate,
                    "format": "pcm"
                }
                
                # Apply voice consistency parameters
                request = self.voice_config.apply_to_request(request)
                
                await websocket.send(json.dumps(request))
                logger.info(f"📤 Sent TTS request: {len(text)} chars")
                
                # Receive audio chunks with idle timeout
                last_chunk_time = asyncio.get_event_loop().time()
                
                while True:
                    try:
                        # Chunk timeout
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=self.chunk_timeout
                        )
                        
                        last_chunk_time = asyncio.get_event_loop().time()
                        
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
                                logger.debug(f"📊 Status: {response}")
                        
                        elif isinstance(message, bytes):
                            audio_chunks.append(message)
                            logger.debug(f"📥 Chunk: {len(message)} bytes")
                    
                    except asyncio.TimeoutError:
                        logger.error(f"⏱️ No chunk received for {self.chunk_timeout}s (idle timeout)")
                        raise
                    
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 WebSocket closed")
                        break
                
                if audio_chunks:
                    full_audio = b''.join(audio_chunks)
                    logger.info(f"✅ Total audio: {len(full_audio)} bytes")
                    return full_audio
                else:
                    logger.warning("⚠️ No audio chunks received")
                    return None
                    
            finally:
                await websocket.close()
        
        except asyncio.TimeoutError:
            logger.error("⏱️ Connection timeout")
            raise
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}", exc_info=True)
            raise
    
    def _save_wav(self, audio_data: bytes, filename: str) -> None:
        """Save raw PCM audio as WAV file"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            logger.info(f"💾 WAV saved: {filename}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save WAV: {e}", exc_info=True)
            raise
    
    def _generate_mock_audio(self, filename_prefix: str) -> str:
        """Generate mock WAV file for testing"""
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
