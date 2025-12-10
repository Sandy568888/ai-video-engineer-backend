"""
Wasabi/S3 Cleanup Script
Deletes old audio and video files to manage storage costs
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.wasabi_service import WasabiService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WasabiCleanup:
    """Cleanup old files from Wasabi S3 storage"""
    
    def __init__(self):
        self.wasabi = WasabiService()
        
        # Retention policies (days)
        self.audio_retention_days = int(os.getenv('WASABI_AUDIO_RETENTION_DAYS', '7'))
        self.video_retention_days = int(os.getenv('WASABI_VIDEO_RETENTION_DAYS', '30'))
        self.temp_retention_days = int(os.getenv('WASABI_TEMP_RETENTION_DAYS', '1'))
        
        # Dry run mode (don't actually delete)
        self.dry_run = os.getenv('CLEANUP_DRY_RUN', 'false').lower() == 'true'
        
        logger.info(f"Wasabi Cleanup initialized")
        logger.info(f"Audio retention: {self.audio_retention_days} days")
        logger.info(f"Video retention: {self.video_retention_days} days")
        logger.info(f"Temp retention: {self.temp_retention_days} days")
        logger.info(f"Dry run: {self.dry_run}")
    
    def get_old_files(self, prefix: str, retention_days: int) -> List[Dict]:
        """
        Get files older than retention period
        
        Args:
            prefix: S3 prefix (folder path)
            retention_days: Files older than this will be deleted
        
        Returns:
            List of file objects to delete
        """
        
        if self.wasabi.mock_mode:
            logger.info(f"🎭 MOCK MODE: Would check {prefix}/* older than {retention_days} days")
            return []
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # List objects in S3
            response = self.wasabi.s3_client.list_objects_v2(
                Bucket=self.wasabi.bucket_name,
                Prefix=prefix
            )
            
            old_files = []
            
            if 'Contents' not in response:
                logger.info(f"No files found in {prefix}/")
                return []
            
            for obj in response['Contents']:
                last_modified = obj['LastModified'].replace(tzinfo=None)
                
                if last_modified < cutoff_date:
                    old_files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': last_modified.isoformat()
                    })
            
            logger.info(f"Found {len(old_files)} old files in {prefix}/")
            return old_files
            
        except Exception as e:
            logger.error(f"Error listing files in {prefix}/: {e}")
            return []
    
    def delete_files(self, files: List[Dict]) -> Dict[str, int]:
        """
        Delete files from S3
        
        Args:
            files: List of file objects to delete
        
        Returns:
            Statistics dictionary
        """
        
        stats = {
            'attempted': len(files),
            'deleted': 0,
            'failed': 0,
            'bytes_freed': 0
        }
        
        if not files:
            return stats
        
        for file in files:
            key = file['key']
            size = file['size']
            
            if self.dry_run:
                logger.info(f"🔍 DRY RUN: Would delete {key} ({size} bytes)")
                stats['deleted'] += 1
                stats['bytes_freed'] += size
                continue
            
            try:
                self.wasabi.delete_file(key)
                logger.info(f"🗑️ Deleted: {key} ({size} bytes)")
                stats['deleted'] += 1
                stats['bytes_freed'] += size
                
            except Exception as e:
                logger.error(f"❌ Failed to delete {key}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def cleanup_audio_files(self) -> Dict[str, int]:
        """Cleanup old audio files"""
        logger.info(f"\n🎵 Cleaning up audio files (>{self.audio_retention_days} days old)")
        
        old_files = self.get_old_files('audio/', self.audio_retention_days)
        stats = self.delete_files(old_files)
        
        logger.info(f"Audio cleanup: {stats['deleted']}/{stats['attempted']} deleted, "
                   f"{stats['bytes_freed']:,} bytes freed")
        
        return stats
    
    def cleanup_video_files(self) -> Dict[str, int]:
        """Cleanup old video files"""
        logger.info(f"\n🎬 Cleaning up video files (>{self.video_retention_days} days old)")
        
        old_files = self.get_old_files('videos/', self.video_retention_days)
        stats = self.delete_files(old_files)
        
        logger.info(f"Video cleanup: {stats['deleted']}/{stats['attempted']} deleted, "
                   f"{stats['bytes_freed']:,} bytes freed")
        
        return stats
    
    def cleanup_temp_files(self) -> Dict[str, int]:
        """Cleanup temporary files"""
        logger.info(f"\n🔧 Cleaning up temp files (>{self.temp_retention_days} days old)")
        
        old_files = self.get_old_files('temp/', self.temp_retention_days)
        stats = self.delete_files(old_files)
        
        logger.info(f"Temp cleanup: {stats['deleted']}/{stats['attempted']} deleted, "
                   f"{stats['bytes_freed']:,} bytes freed")
        
        return stats
    
    def run_cleanup(self) -> Dict[str, Dict[str, int]]:
        """Run full cleanup process"""
        logger.info("🧹 Starting Wasabi cleanup...")
        
        if self.dry_run:
            logger.warning("⚠️ DRY RUN MODE - No files will be actually deleted")
        
        results = {
            'audio': self.cleanup_audio_files(),
            'video': self.cleanup_video_files(),
            'temp': self.cleanup_temp_files()
        }
        
        # Calculate totals
        total_deleted = sum(r['deleted'] for r in results.values())
        total_bytes = sum(r['bytes_freed'] for r in results.values())
        total_mb = total_bytes / (1024 * 1024)
        
        logger.info(f"\n✅ Cleanup complete!")
        logger.info(f"Total files deleted: {total_deleted}")
        logger.info(f"Total space freed: {total_mb:.2f} MB ({total_bytes:,} bytes)")
        
        return results


def main():
    """Main cleanup function"""
    try:
        cleanup = WasabiCleanup()
        results = cleanup.run_cleanup()
        
        # Exit with success
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
