"""GPU Health Monitoring Service"""
import os
import logging
import subprocess
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Monitor GPU health and usage statistics"""
    
    def __init__(self):
        self.mock_mode = os.getenv('MOCK_MODE', 'False') == 'True'
        self.has_nvidia = self._check_nvidia_smi()
    
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        if self.mock_mode:
            return True
        
        try:
            result = subprocess.run(
                ['nvidia-smi', '--version'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"nvidia-smi not available: {e}")
            return False
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """
        Get GPU statistics
        
        Returns:
            dict with GPU metrics
        """
        
        if self.mock_mode:
            return self._get_mock_stats()
        
        if not self.has_nvidia:
            return {
                'status': 'unavailable',
                'message': 'No NVIDIA GPU detected or nvidia-smi not installed'
            }
        
        try:
            return self._get_nvidia_stats()
        except Exception as e:
            logger.error(f"Failed to get GPU stats: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_nvidia_stats(self) -> Dict[str, Any]:
        """Get real NVIDIA GPU statistics"""
        
        try:
            # Query nvidia-smi for GPU stats
            cmd = [
                'nvidia-smi',
                '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise Exception(f"nvidia-smi error: {result.stderr}")
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    index, name, mem_used, mem_total, util, temp = parts[:6]
                    
                    gpus.append({
                        'index': int(index),
                        'name': name,
                        'memory_used_mb': int(mem_used),
                        'memory_total_mb': int(mem_total),
                        'memory_usage_percent': round((int(mem_used) / int(mem_total)) * 100, 2),
                        'utilization_percent': int(util),
                        'temperature_celsius': int(temp)
                    })
            
            # Get TTS-specific stats (if available)
            tts_stats = self._get_tts_process_stats()
            
            return {
                'status': 'healthy',
                'gpus': gpus,
                'tts_streams': tts_stats,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            raise Exception(f"Failed to parse nvidia-smi output: {e}")
    
    def _get_tts_process_stats(self) -> Dict[str, Any]:
        """Get TTS-specific process statistics"""
        
        # This will be implemented when TTS process tracking is added
        # For now, return placeholder
        
        return {
            'active_streams': 0,
            'queue_depth': 0,
            'total_processed': 0,
            'note': 'TTS process tracking to be implemented'
        }
    
    def _get_mock_stats(self) -> Dict[str, Any]:
        """Get mock GPU statistics for testing"""
        
        return {
            'status': 'healthy (mock)',
            'gpus': [
                {
                    'index': 0,
                    'name': 'NVIDIA RTX 4090 (Mock)',
                    'memory_used_mb': 8192,
                    'memory_total_mb': 24576,
                    'memory_usage_percent': 33.33,
                    'utilization_percent': 45,
                    'temperature_celsius': 62
                }
            ],
            'tts_streams': {
                'active_streams': 2,
                'queue_depth': 5,
                'total_processed': 127,
                'note': 'Mock data for testing'
            },
            'timestamp': self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get simplified GPU health summary"""
        
        stats = self.get_gpu_stats()
        
        if stats.get('status') == 'unavailable':
            return {
                'healthy': False,
                'message': 'GPU not available'
            }
        
        if stats.get('status') == 'error':
            return {
                'healthy': False,
                'message': stats.get('message')
            }
        
        # Check if any GPU is overheating or overloaded
        gpus = stats.get('gpus', [])
        
        for gpu in gpus:
            temp = gpu.get('temperature_celsius', 0)
            mem_usage = gpu.get('memory_usage_percent', 0)
            
            if temp > 85:
                return {
                    'healthy': False,
                    'message': f"GPU {gpu['index']} temperature too high: {temp}°C"
                }
            
            if mem_usage > 95:
                return {
                    'healthy': False,
                    'message': f"GPU {gpu['index']} memory almost full: {mem_usage}%"
                }
        
        return {
            'healthy': True,
            'message': 'All GPUs operating normally',
            'gpu_count': len(gpus)
        }
