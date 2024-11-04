import logging
from google.cloud import monitoring_v3
from google.protobuf.duration_pb2 import Duration
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

def process_message(message_dict):
    logger.debug(f"Processing message: {message_dict}")
    # Processing logic here
    return message_dict