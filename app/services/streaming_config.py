"""Streaming TTS Configuration - Future-Proofing"""
import os
import logging
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming TTS support"""
    
    # Enable streaming mode (future feature)
    enabled: bool = os.getenv('TTS_STREAMING_ENABLED', 'false').lower() == 'true'
    
    # Chunk size for streaming (bytes)
    chunk_size: int = int(os.getenv('TTS_STREAMING_CHUNK_SIZE', '4096'))
    
    # Buffer size before starting playback
    buffer_size: int = int(os.getenv('TTS_STREAMING_BUFFER_SIZE', '8192'))
    
    # Stream timeout (seconds)
    stream_timeout: int = int(os.getenv('TTS_STREAMING_TIMEOUT', '30'))


class StreamingTTSHandler:
    """
    Handler for streaming TTS audio chunks
    Future-proofing for real-time audio streaming
    """
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        self.config = config or StreamingConfig()
        logger.info(f"StreamingTTS initialized: enabled={self.config.enabled}")
    
    async def stream_audio_chunks(
        self,
        audio_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks as they're generated
        
        Args:
            audio_generator: Async generator yielding audio bytes
        
        Yields:
            Audio chunks ready for transmission
        """
        
        if not self.config.enabled:
            logger.info("Streaming disabled, collecting all chunks")
            chunks = []
            async for chunk in audio_generator:
                chunks.append(chunk)
            yield b''.join(chunks)
            return
        
        logger.info("🎵 Streaming mode enabled")
        buffer = b''
        
        async for chunk in audio_generator:
            buffer += chunk
            
            # Yield chunks when buffer reaches threshold
            while len(buffer) >= self.config.chunk_size:
                yield_chunk = buffer[:self.config.chunk_size]
                buffer = buffer[self.config.chunk_size:]
                yield yield_chunk
        
        # Yield remaining buffer
        if buffer:
            yield buffer
    
    def get_config(self) -> dict:
        """Get streaming configuration"""
        return {
            'enabled': self.config.enabled,
            'chunk_size': self.config.chunk_size,
            'buffer_size': self.config.buffer_size,
            'stream_timeout': self.config.stream_timeout
        }
