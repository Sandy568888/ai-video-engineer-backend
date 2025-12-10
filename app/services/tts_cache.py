"""TTS Output Caching System"""
import os
import hashlib
import json
import logging
import shutil
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class TTSCache:
    """Cache TTS audio outputs to avoid regenerating identical content"""
    
    def __init__(self):
        self.cache_dir = os.getenv('TTS_CACHE_DIR', '/tmp/tts_cache')
        self.enabled = os.getenv('TTS_CACHE_ENABLED', 'true').lower() == 'true'
        self.max_cache_size_mb = int(os.getenv('TTS_CACHE_MAX_SIZE_MB', '500'))
        self.cache_ttl_hours = int(os.getenv('TTS_CACHE_TTL_HOURS', '168'))  # 7 days default
        
        # Create cache directory
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"TTS Cache enabled: {self.cache_dir}")
            logger.info(f"Max cache size: {self.max_cache_size_mb} MB")
            logger.info(f"Cache TTL: {self.cache_ttl_hours} hours")
    
    def _generate_cache_key(
        self,
        text: str,
        provider: str,
        voice_id: Optional[str] = None,
        format: str = 'wav'
    ) -> str:
        """
        Generate cache key from input parameters
        
        Args:
            text: Input text
            provider: TTS provider
            voice_id: Voice identifier
            format: Audio format
        
        Returns:
            Cache key (hash)
        """
        
        # Create unique identifier from parameters
        cache_input = {
            'text': text.strip().lower(),
            'provider': provider,
            'voice_id': voice_id or 'default',
            'format': format
        }
        
        # Generate hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()
        
        return cache_hash
    
    def _get_cache_file_path(self, cache_key: str, format: str = 'wav') -> str:
        """Get full path to cache file"""
        return os.path.join(self.cache_dir, f"{cache_key}.{format}")
    
    def _get_metadata_path(self, cache_key: str) -> str:
        """Get path to cache metadata file"""
        return os.path.join(self.cache_dir, f"{cache_key}.meta.json")
    
    def get(
        self,
        text: str,
        provider: str,
        voice_id: Optional[str] = None,
        format: str = 'wav'
    ) -> Optional[str]:
        """
        Get cached audio file if available
        
        Returns:
            Path to cached audio file, or None if not cached
        """
        
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key(text, provider, voice_id, format)
            cache_file = self._get_cache_file_path(cache_key, format)
            meta_file = self._get_metadata_path(cache_key)
            
            # Check if cache exists
            if not os.path.exists(cache_file) or not os.path.exists(meta_file):
                logger.debug(f"Cache miss: {cache_key}")
                return None
            
            # Check cache age
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            
            created_at = datetime.fromisoformat(metadata['created_at'])
            age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
            
            if age_hours > self.cache_ttl_hours:
                logger.info(f"Cache expired: {cache_key} (age: {age_hours:.1f}h)")
                self._delete_cache_entry(cache_key, format)
                return None
            
            # Cache hit!
            logger.info(f"✅ Cache HIT: {cache_key} (age: {age_hours:.1f}h)")
            
            # Update access time
            metadata['last_accessed'] = datetime.utcnow().isoformat()
            metadata['hit_count'] = metadata.get('hit_count', 0) + 1
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return cache_file
            
        except Exception as e:
            logger.error(f"Cache get error: {e}", exc_info=True)
            return None
    
    def set(
        self,
        text: str,
        provider: str,
        audio_file_path: str,
        voice_id: Optional[str] = None,
        format: str = 'wav',
        audio_duration: Optional[float] = None
    ) -> bool:
        """
        Store audio file in cache
        
        Args:
            text: Input text
            provider: TTS provider used
            audio_file_path: Path to generated audio file
            voice_id: Voice identifier
            format: Audio format
            audio_duration: Duration of audio in seconds
        
        Returns:
            True if cached successfully
        """
        
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(text, provider, voice_id, format)
            cache_file = self._get_cache_file_path(cache_key, format)
            meta_file = self._get_metadata_path(cache_key)
            
            # Copy audio file to cache
            shutil.copy2(audio_file_path, cache_file)
            
            # Create metadata
            metadata = {
                'cache_key': cache_key,
                'text_hash': hashlib.sha256(text.encode()).hexdigest(),
                'text_length': len(text),
                'provider': provider,
                'voice_id': voice_id,
                'format': format,
                'audio_duration': audio_duration,
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed': datetime.utcnow().isoformat(),
                'hit_count': 0,
                'file_size': os.path.getsize(audio_file_path)
            }
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"💾 Cached: {cache_key}")
            
            # Cleanup if cache is too large
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}", exc_info=True)
            return False
    
    def _delete_cache_entry(self, cache_key: str, format: str = 'wav') -> None:
        """Delete a cache entry"""
        try:
            cache_file = self._get_cache_file_path(cache_key, format)
            meta_file = self._get_metadata_path(cache_key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
            if os.path.exists(meta_file):
                os.remove(meta_file)
            
            logger.debug(f"Deleted cache entry: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error deleting cache entry: {e}")
    
    def _get_cache_size_mb(self) -> float:
        """Get total cache size in MB"""
        total_size = 0
        
        for file in Path(self.cache_dir).iterdir():
            if file.is_file():
                total_size += file.stat().st_size
        
        return total_size / (1024 * 1024)
    
    def _cleanup_if_needed(self) -> None:
        """Clean up old cache entries if cache is too large"""
        try:
            current_size = self._get_cache_size_mb()
            
            if current_size <= self.max_cache_size_mb:
                return
            
            logger.info(f"🧹 Cache cleanup needed: {current_size:.2f} MB / {self.max_cache_size_mb} MB")
            
            # Get all metadata files sorted by last access time
            meta_files = []
            
            for file in Path(self.cache_dir).glob('*.meta.json'):
                try:
                    with open(file, 'r') as f:
                        metadata = json.load(f)
                    
                    last_accessed = datetime.fromisoformat(metadata['last_accessed'])
                    meta_files.append((file, last_accessed, metadata['cache_key']))
                    
                except Exception as e:
                    logger.error(f"Error reading metadata {file}: {e}")
            
            # Sort by last accessed (oldest first)
            meta_files.sort(key=lambda x: x[1])
            
            # Delete oldest entries until under limit
            deleted_count = 0
            
            for meta_file, _, cache_key in meta_files:
                self._delete_cache_entry(cache_key)
                deleted_count += 1
                
                current_size = self._get_cache_size_mb()
                if current_size <= self.max_cache_size_mb * 0.8:  # Target 80% of max
                    break
            
            logger.info(f"✅ Cleaned up {deleted_count} cache entries")
            logger.info(f"New cache size: {current_size:.2f} MB")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                'enabled': self.enabled,
                'cache_dir': self.cache_dir,
                'total_entries': 0,
                'total_size_mb': 0,
                'max_size_mb': self.max_cache_size_mb,
                'ttl_hours': self.cache_ttl_hours,
                'total_hits': 0,
                'entries': []
            }
            
            if not self.enabled:
                return stats
            
            # Count entries and calculate stats
            for meta_file in Path(self.cache_dir).glob('*.meta.json'):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    stats['total_entries'] += 1
                    stats['total_hits'] += metadata.get('hit_count', 0)
                    
                    stats['entries'].append({
                        'cache_key': metadata['cache_key'],
                        'provider': metadata['provider'],
                        'text_length': metadata['text_length'],
                        'hit_count': metadata.get('hit_count', 0),
                        'created_at': metadata['created_at'],
                        'file_size_kb': metadata['file_size'] / 1024
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading metadata {meta_file}: {e}")
            
            stats['total_size_mb'] = round(self._get_cache_size_mb(), 2)
            stats['usage_percent'] = round(
                (stats['total_size_mb'] / stats['max_size_mb']) * 100, 2
            )
            
            # Sort entries by hit count
            stats['entries'].sort(key=lambda x: x['hit_count'], reverse=True)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def clear(self) -> int:
        """Clear entire cache"""
        try:
            deleted = 0
            
            for file in Path(self.cache_dir).iterdir():
                if file.is_file():
                    file.unlink()
                    deleted += 1
            
            logger.info(f"🗑️ Cleared cache: {deleted} files deleted")
            return deleted
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
