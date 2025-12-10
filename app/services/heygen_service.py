"""HeyGen service for avatar video generation"""
import os
import logging
logger = logging.getLogger(__name__)

class HeyGenService:
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        
        # Check both MOCK_MODE and HEYGEN_MOCK_MODE
        general_mock = os.getenv('MOCK_MODE', 'False').lower() == 'true'
        specific_mock = os.getenv('HEYGEN_MOCK_MODE', 'False').lower() == 'true'
        self.mock_mode = general_mock or specific_mock
        
        self.avatar_id = os.getenv('HEYGEN_AVATAR_ID', 'default')
        
        logger.info(f"HeyGen initialized: mock_mode={self.mock_mode}")
    
    def create_avatar_video(self, audio_url, avatar_id=None):
        """Create avatar video from audio"""
        if self.mock_mode:
            logger.info("MOCK: Creating HeyGen avatar video")
            filename = f"mock_avatar_video_{os.urandom(4).hex()}.mp4"
            self._create_mock_video(filename)
            return filename
        
        # TODO: Implement real HeyGen API call
        logger.warning("HeyGen integration not yet implemented")
        return None
    
    def _create_mock_video(self, filename):
        """Create a mock MP4 file (empty file for testing)"""
        try:
            # Create empty MP4 file
            with open(filename, 'wb') as f:
                # Write minimal MP4 header
                f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41')
                f.write(b'\x00' * 100)  # Pad with zeros
            
            logger.info(f"Created mock video: {filename}")
        except Exception as e:
            logger.error(f"Failed to create mock video: {e}")
            raise
