"""JSON Structured Logging"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: Log record
        
        Returns:
            JSON formatted log string
        """
        
        # Base log structure
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add source location
        log_data['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add custom fields from extra parameter
        if hasattr(record, 'video_id'):
            log_data['video_id'] = record.video_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'provider'):
            log_data['provider'] = record.provider
        if hasattr(record, 'execution_ms'):
            log_data['execution_ms'] = record.execution_ms
        if hasattr(record, 'status'):
            log_data['status'] = record.status
        if hasattr(record, 'fallback_used'):
            log_data['fallback_used'] = record.fallback_used
        
        return json.dumps(log_data)


def setup_json_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> None:
    """
    Setup JSON structured logging
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    
    # Create JSON formatter
    json_formatter = JSONFormatter()
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(level)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:-1]:
        root_logger.removeHandler(handler)


class StructuredLogger:
    """Helper for structured logging with consistent fields"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_tts_generation(
        self,
        level: int,
        message: str,
        video_id: Optional[str] = None,
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        execution_ms: Optional[int] = None,
        status: Optional[str] = None,
        fallback_used: bool = False,
        **kwargs
    ) -> None:
        """
        Log TTS generation event
        
        Args:
            level: Log level
            message: Log message
            video_id: Video identifier
            user_id: User identifier
            provider: TTS provider
            execution_ms: Execution time in milliseconds
            status: Generation status
            fallback_used: Whether fallback was used
            **kwargs: Additional fields
        """
        
        extra = {
            'video_id': video_id,
            'user_id': user_id,
            'provider': provider,
            'execution_ms': execution_ms,
            'status': status,
            'fallback_used': fallback_used,
            **kwargs
        }
        
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log_tts_generation(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log_tts_generation(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.log_tts_generation(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log_tts_generation(logging.DEBUG, message, **kwargs)
