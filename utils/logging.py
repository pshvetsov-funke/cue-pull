import logging


def get_logger():
    """Create a logger instance with Stream Handler

    Returns:
        logging instance
    """
    logger = logging.getLogger('customLogger')
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = get_logger()