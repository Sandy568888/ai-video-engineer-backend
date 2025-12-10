"""Logging Configuration"""
import os
import logging
from app.services.json_logger import setup_json_logging

# Determine if JSON logging is enabled
JSON_LOGGING = os.getenv('JSON_LOGGING', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', '/tmp/app.log')

# Map string level to logging constant
LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def configure_logging():
    """Configure application logging"""
    
    level = LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    
    if JSON_LOGGING:
        # Use JSON structured logging
        setup_json_logging(level=level, log_file=LOG_FILE if LOG_FILE != 'null' else None)
        print(f"✅ JSON structured logging enabled (level: {LOG_LEVEL})")
    else:
        # Use standard logging
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(LOG_FILE) if LOG_FILE != 'null' else logging.NullHandler()
            ]
        )
        print(f"✅ Standard logging enabled (level: {LOG_LEVEL})")
