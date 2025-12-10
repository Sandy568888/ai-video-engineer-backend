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
            return "mock_avatar_video.mp4"
        
        # TODO: Implement real HeyGen API call
        logger.warning("HeyGen integration not yet implemented")
        return None
