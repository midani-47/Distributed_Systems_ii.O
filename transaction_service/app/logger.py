import logging
import os
import sys

def get_logger(name, log_file=None):
    """
    Create a basic logger with console and optional file output
    
    Args:
        name: Logger name
        log_file: Optional file to log to
    """
    # Set up logger
    logger = logging.getLogger(name)
    
    # Return if already configured
    if logger.handlers:
        return logger
    
    # Set minimum log level
    logger.setLevel(logging.INFO)
    
    # Basic log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console output
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # Add simple file output if requested
    if log_file:
        # Create logs directory
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Full path to log file
        log_path = os.path.join(logs_dir, log_file)
        
        # Create simple file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Simple filter to add extra fields to log records
class RequestResponseFilter(logging.Filter):
    """
    Add request/response context to log records
    """
    def __init__(self, source=None, destination=None):
        super().__init__()
        self.source = source
        self.destination = destination
    
    def filter(self, record):
        # Add fields to the record
        record.source = self.source or "-"
        record.destination = self.destination or "-"
        return True