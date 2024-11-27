import json
import logging
import sys

class JsonFormatter(logging.Formatter):
    """Defines class suitable for cloud logging

    It ensures that the severity of the message is always captured. Also through
    dedicated message structure it will not break multi-line message into separate
    logging messages (occurs by default).
    Args:
        logging (_type_): _description_
    """
    def format(self, record):
        log_entry = {
            'message': record.getMessage(),
            'severity': record.levelname,
            'timestamp': self.formatTime(record, self.datefmt),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    # Get the root logger
    logger = logging.getLogger()
    
    # Check if handlers are already configured to prevent duplication
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
