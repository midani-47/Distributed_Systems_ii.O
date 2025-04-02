import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs("../../logs", exist_ok=True)

# Configure formatter with detailed information
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(source)s:%(destination)s]'
)

def get_logger(name, log_file=None):
    """
    Create and configure a logger with both console and file handlers
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        # Logger already configured
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = RotatingFileHandler(
            f"../../logs/{log_file}",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Add extra context to log records
class RequestResponseFilter(logging.Filter):
    """
    Filter that adds source, destination, headers and metadata fields to log records
    """
    def __init__(self, source=None, destination=None, headers=None, metadata=None):
        super().__init__()
        self.source = source
        self.destination = destination
        self.headers = headers or {}
        self.metadata = metadata or {}
    
    def filter(self, record):
        record.source = self.source or "unknown"
        record.destination = self.destination or "unknown"
        record.headers = self.headers
        record.metadata = self.metadata
        return True 