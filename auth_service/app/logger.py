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
    # instantiating logger with specified name
    logger = logging.getLogger(name)
    
    # returning existing logger if already configured
    if logger.handlers:
        return logger
    
    # setting log level to INFO to filter out debug messages
    logger.setLevel(logging.INFO)
    
    # defining log format for consistency
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # adding console output handler for development visibility
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # configuring file-based logging if requested
    if log_file:
        # ensuring logs directory exists
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # constructing full path to log file
        log_path = os.path.join(logs_dir, log_file)
        
        # setting up file handler for persistent logging
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# filter for enriching log records with request context
class RequestFilter(logging.Filter):
    """
    Add request/response context to log records
    """
    def __init__(self, source=None, destination=None):
        super().__init__()
        self.source = source
        self.destination = destination
    
    def filter(self, record):
        # augmenting log record with additional context
        record.source = self.source or "-"
        record.destination = self.destination or "-"
        return True