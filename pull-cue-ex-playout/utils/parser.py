import json
import logging
import hashlib
from datetime import datetime, UTC
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class Parser:
    """Class to unite all message parsing functionalities
    """
    def __init__(self, max_iterations):
        self.max_messages = 1000
        self.total_messages_processed = 0
        self.total_received_messages = 0
        self.total_acknowledged_messages = 0
        self.unique_messages = set()
        self.total_duplicate_count = 0

        # Step for BigQuery batch injection. If it is too big - more memory is required.
        # Step of 100 show itself good for cloud run function instance size of 512 MB
        self.BQI_STEP = 100

        # Since max messages to pull is limited from GCP side to 1000. This will
        # ensure that all available messages are pulled (assumed they are 
        # less that max_messages*max_iterations)
        self.max_iterations = max_iterations

        # Load json schema for later message validation from file
        with open('./utils/validation_schema.json', 'r') as schema_file:
            self.json_schema = json.load(schema_file)
        
        if not self.json_schema:
            logger.critical("JSON schema couldn't be loaded or is empty!")
            raise ValueError("JSON schema couldn't be loaded or is empty!")


    def reset_iteration_info(self):
        """Reset information that refers to a single iteration
        """
        self.iter_ack_ids = []
        self.iter_rows_to_insert = []
        self.iter_dlq_rows = []
        self.iter_duplicate_count = 0


    def process_message(self, received_message):
        """Functionality for processing the received raw message from PubSub

        Args:
            received_message (PubSub message): raw message received
        """
        message_data = received_message.message.data.decode('utf-8')
        message_dict = json.loads(message_data)

        # Ensure that the message has expected format
        try:
            validate(instance=message_dict, schema=self.json_schema)

            is_duplicate, message_hash = self.deduplicate_message(
                message_dict, received_message.ack_id
            )
            if not is_duplicate:
                processed_message = self.transform_message(message_dict, message_hash)
                self.iter_rows_to_insert.append(processed_message)
                self.iter_ack_ids.append(received_message.ack_id)

        except ValidationError as e:
            logger.warning(f"The JSON message has invalid schema. Error :{e}")
            raise ValidationError
        except Exception as e:
            logger.warning(f"The error occured during message validation. Error: {e}")
            raise ValidationError


    def add_message_to_dlq(self, received_message, error):
        """Add the problematic message to dead letter queue.

        In order not to loose message information - store the message in raw
        format for later processing

        Args:
            received_message (PubSub message): raw message received
        """
        try:
            message_data = received_message.message.data.decode('utf-8')
            dlq_row = {
                'message_data': message_data,
                'error_message': str(error),
                'timestamp': datetime.now(UTC).isoformat()
            }
        except Exception as e:
            dlq_row = {
                'message_data': received_message.message.data,
                'error_message': f"Upstream error: {str(error)}, downstream error: {str(e)}",
                'timestamp': datetime.now(UTC).isoformat()
            }

        self.iter_dlq_rows.append(dlq_row)
        self.iter_ack_ids.append(received_message.ack_id)


    def deduplicate_message(self, message_dict, ack_id):
        """Encapsulates message deduplication logic. Calculate content hash. Ensure uniqueness.

        Args:
            message_dict (dict): message
        """
        is_duplicate = False
        message_bytes = json.dumps(message_dict, sort_keys=True).encode('utf-8')
        message_hash = hashlib.sha256(message_bytes).hexdigest()

        # Check if the message was processed
        if message_hash in self.unique_messages:
            self.iter_duplicate_count += 1
            self.iter_ack_ids.append(ack_id)
            is_duplicate = True
            return is_duplicate, message_hash

        # Adds deduplication logic within single cloud run function invocation.
        # Through unique_messages set the deduplication logic is not perceived between invocations. 
        self.unique_messages.add(message_hash)

        #TODO optionally add functionality to determine and log the 
        # content of first occured duplicate pair for debug reasons 
        # (if duplicates should not occur)

        #TODO optionally add hash as aditional column in BigQuery table to ease the 
        # message deduplication within DWH.

        return is_duplicate, message_hash


    def transform_message(self, message_dict, message_hash):
        """Performs the message transformation

        Args:
            message_dict (dict): message
        """
        # Some future transformation (if there should be one)
        message_dict['content_hash'] = message_hash
        return message_dict
