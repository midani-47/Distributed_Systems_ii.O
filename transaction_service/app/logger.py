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
    # creating logger instance with given name
    logger = logging.getLogger(name)
    
    # returning already configured logger to avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # configuring minimum log level
    logger.setLevel(logging.INFO)
    
    # setting up log message format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # adding console output for immediate visibility
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # adding file logging if specified
    if log_file:
        # creating logs directory if needed
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # resolving full path to log file
        log_path = os.path.join(logs_dir, log_file)
        
        # configuring file output handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# custom filter for adding request metadata to log entries
class RequestResponseFilter(logging.Filter):
    """
    Add request/response context to log records
    """
    def __init__(self, source=None, destination=None):
        super().__init__()
        self.source = source
        self.destination = destination
    
    def filter(self, record):
        # enriching log record with request context data
        record.source = self.source or "-"
        record.destination = self.destination or "-"
        return True