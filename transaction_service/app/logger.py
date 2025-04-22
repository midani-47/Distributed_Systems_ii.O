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
    # make a logger with the name
    logger = logging.getLogger(name)
    
    # skip if we already setup this logger before
    if logger.handlers:
        return logger
    
    # set how detailed the logs should be
    logger.setLevel(logging.INFO)
    
    # how the logs gonna look
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # put logs in console so we can see em
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # also put in file if they asked for that
    if log_file:
        # make sure we got a logs folder
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # figure out the whole path to log file
        log_path = os.path.join(logs_dir, log_file)
        
        # this handler writes to the file
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# this add extra info to our logs
class RequestResponseFilter(logging.Filter):
    """
    Add request/response context to log records
    """
    def __init__(self, source=None, destination=None):
        super().__init__()
        self.source = source
        self.destination = destination
    
    def filter(self, record):
        # add the extra stuff to each log entry
        record.source = self.source or "-"
        record.destination = self.destination or "-"
        return True