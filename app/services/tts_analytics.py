"""TTS Analytics and Metadata Storage"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TTSMetadata:
    """TTS generation metadata for analytics"""
    
    video_id: str
    user_id: str
    provider: str  # 'vibevoice' or 'elevenlabs'
    fallback_triggered: bool
    execution_time_ms: int
    audio_duration_seconds: Optional[float]
    text_length: int
    voice_id: Optional[str]
    status: str  # 'success', 'failed', 'fallback_success'
    error_message: Optional[str]
    timestamp: str
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class TTSAnalytics:
    """Store and manage TTS analytics"""
    
    def __init__(self):
        self.storage_path = os.getenv('TTS_ANALYTICS_PATH', '/tmp/tts_analytics')
        self.enabled = os.getenv('TTS_ANALYTICS_ENABLED', 'true').lower() == 'true'
        
        # Create storage directory
        if self.enabled:
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info(f"TTS Analytics enabled: {self.storage_path}")
    
    def log_generation(
        self,
        video_id: str,
        user_id: str,
        provider: str,
        fallback_triggered: bool,
        execution_time_ms: int,
        audio_duration_seconds: Optional[float],
        text_length: int,
        voice_id: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        retry_count: int = 0
    ) -> None:
        """
        Log TTS generation metadata
        
        Args:
            video_id: Video identifier
            user_id: User identifier
            provider: TTS provider used
            fallback_triggered: Whether fallback was used
            execution_time_ms: Generation time in milliseconds
            audio_duration_seconds: Duration of generated audio
            text_length: Length of input text
            voice_id: Voice identifier used
            status: Generation status
            error_message: Error message if failed
            retry_count: Number of retries attempted
        """
        
        if not self.enabled:
            return
        
        try:
            metadata = TTSMetadata(
                video_id=video_id,
                user_id=user_id,
                provider=provider,
                fallback_triggered=fallback_triggered,
                execution_time_ms=execution_time_ms,
                audio_duration_seconds=audio_duration_seconds,
                text_length=text_length,
                voice_id=voice_id,
                status=status,
                error_message=error_message,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                retry_count=retry_count
            )
            
            # Log to file (append mode)
            log_file = os.path.join(
                self.storage_path,
                f"tts_analytics_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            )
            
            with open(log_file, 'a') as f:
                f.write(metadata.to_json() + '\n')
            
            logger.info(f"📊 Analytics logged: {provider}, {status}, {execution_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Failed to log TTS analytics: {e}", exc_info=True)
    
    def get_stats(self, days: int = 1) -> Dict[str, Any]:
        """
        Get analytics statistics for the last N days
        
        Args:
            days: Number of days to include
        
        Returns:
            Statistics dictionary
        """
        
        if not self.enabled:
            return {'error': 'Analytics not enabled'}
        
        try:
            from datetime import timedelta
            
            stats = {
                'total_generations': 0,
                'successful': 0,
                'failed': 0,
                'fallback_triggered': 0,
                'providers': {},
                'avg_execution_time_ms': 0,
                'avg_audio_duration_s': 0,
                'total_text_chars': 0
            }
            
            # Read log files for the past N days
            execution_times = []
            audio_durations = []
            
            for day_offset in range(days):
                date = datetime.utcnow() - timedelta(days=day_offset)
                log_file = os.path.join(
                    self.storage_path,
                    f"tts_analytics_{date.strftime('%Y%m%d')}.jsonl"
                )
                
                if not os.path.exists(log_file):
                    continue
                
                with open(log_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        data = json.loads(line)
                        
                        stats['total_generations'] += 1
                        
                        if data['status'] == 'success' or data['status'] == 'fallback_success':
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1
                        
                        if data['fallback_triggered']:
                            stats['fallback_triggered'] += 1
                        
                        provider = data['provider']
                        if provider not in stats['providers']:
                            stats['providers'][provider] = 0
                        stats['providers'][provider] += 1
                        
                        execution_times.append(data['execution_time_ms'])
                        
                        if data['audio_duration_seconds']:
                            audio_durations.append(data['audio_duration_seconds'])
                        
                        stats['total_text_chars'] += data['text_length']
            
            # Calculate averages
            if execution_times:
                stats['avg_execution_time_ms'] = round(sum(execution_times) / len(execution_times), 2)
            
            if audio_durations:
                stats['avg_audio_duration_s'] = round(sum(audio_durations) / len(audio_durations), 2)
            
            # Calculate success rate
            if stats['total_generations'] > 0:
                stats['success_rate'] = round(
                    (stats['successful'] / stats['total_generations']) * 100, 2
                )
                stats['fallback_rate'] = round(
                    (stats['fallback_triggered'] / stats['total_generations']) * 100, 2
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get analytics stats: {e}", exc_info=True)
            return {'error': str(e)}
