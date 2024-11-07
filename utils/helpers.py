import json
import logging
import hashlib
from google.cloud import monitoring_v3
from google.protobuf.duration_pb2 import Duration
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

def process_message(message_dict):
    logger.debug(f"Processing message: {message_dict}")
    # Processing logic here
    return message_dict

def generate_insert_id(message_data):
    message_bytes = json.dumps(message_data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(message_bytes).hexdigest()