"""Voice Consistency Parameters for TTS"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VoiceConfig:
    """Voice consistency configuration"""
    
    # Voice style/emotion parameters
    style: Optional[str] = None
    
    # Random seed for reproducibility
    seed: Optional[int] = None
    
    # Voice profile/preset
    profile: Optional[str] = None
    
    # Additional parameters
    speed: float = 1.0
    pitch: float = 1.0
    energy: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'VoiceConfig':
        """Load configuration from environment variables"""
        return cls(
            style=os.getenv('VIBEVOICE_STYLE'),
            seed=int(os.getenv('VIBEVOICE_SEED')) if os.getenv('VIBEVOICE_SEED') else None,
            profile=os.getenv('VIBEVOICE_PROFILE'),
            speed=float(os.getenv('VIBEVOICE_SPEED', '1.0')),
            pitch=float(os.getenv('VIBEVOICE_PITCH', '1.0')),
            energy=float(os.getenv('VIBEVOICE_ENERGY', '1.0'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'style': self.style,
            'seed': self.seed,
            'profile': self.profile,
            'speed': self.speed,
            'pitch': self.pitch,
            'energy': self.energy
        }
    
    def apply_to_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply voice config to TTS request
        
        Args:
            request: Base TTS request
        
        Returns:
            Request with voice parameters applied
        """
        
        if self.style:
            request['style'] = self.style
            logger.debug(f"Applied style: {self.style}")
        
        if self.seed is not None:
            request['seed'] = self.seed
            logger.debug(f"Applied seed: {self.seed}")
        
        if self.profile:
            request['profile'] = self.profile
            logger.debug(f"Applied profile: {self.profile}")
        
        if self.speed != 1.0:
            request['speed'] = self.speed
            logger.debug(f"Applied speed: {self.speed}")
        
        if self.pitch != 1.0:
            request['pitch'] = self.pitch
            logger.debug(f"Applied pitch: {self.pitch}")
        
        if self.energy != 1.0:
            request['energy'] = self.energy
            logger.debug(f"Applied energy: {self.energy}")
        
        return request


class VoiceManager:
    """Manage voice consistency across generations"""
    
    def __init__(self):
        self.default_config = VoiceConfig.from_env()
        logger.info(f"Voice manager initialized with config: {self.default_config.to_dict()}")
    
    def get_config(
        self,
        style: Optional[str] = None,
        seed: Optional[int] = None,
        profile: Optional[str] = None
    ) -> VoiceConfig:
        """
        Get voice configuration with optional overrides
        
        Args:
            style: Override style
            seed: Override seed
            profile: Override profile
        
        Returns:
            VoiceConfig instance
        """
        
        config = VoiceConfig(
            style=style or self.default_config.style,
            seed=seed if seed is not None else self.default_config.seed,
            profile=profile or self.default_config.profile,
            speed=self.default_config.speed,
            pitch=self.default_config.pitch,
            energy=self.default_config.energy
        )
        
        return config
    
    def create_consistent_voice(
        self,
        base_voice_id: str,
        user_id: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create consistent voice parameters for a user/project
        
        Args:
            base_voice_id: Base voice to use
            user_id: User identifier
            project_id: Optional project identifier
        
        Returns:
            Voice parameters dictionary
        """
        
        # Generate consistent seed from user/project
        seed_input = f"{user_id}:{project_id or 'default'}:{base_voice_id}"
        seed = hash(seed_input) % (2**31)  # Positive 32-bit int
        
        config = self.get_config(seed=seed)
        
        return {
            'voice_id': base_voice_id,
            'seed': seed,
            'config': config.to_dict()
        }
