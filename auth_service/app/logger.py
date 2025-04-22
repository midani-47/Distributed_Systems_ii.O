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
    # create our logger object
    logger = logging.getLogger(name)
    
    # if we already got this logger setup just return it
    if logger.handlers:
        return logger
    
    # we only want info and above, no debug stuff
    logger.setLevel(logging.INFO)
    
    # this is how our logs will look like
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # show logs in console for debugging
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # save logs to file if they want that
    if log_file:
        # make logs directory if it dont exist
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # put the log file in the logs directory
        log_path = os.path.join(logs_dir, log_file)
        
        # setup the file logging thing
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# special filter to add more info to our logs
class RequestFilter(logging.Filter):
    """
    Add request/response context to log records
    """
    def __init__(self, source=None, destination=None):
        super().__init__()
        self.source = source
        self.destination = destination
    
    def filter(self, record):
        # stick some extra info in each log message
        record.source = self.source or "-"
        record.destination = self.destination or "-"
        return True