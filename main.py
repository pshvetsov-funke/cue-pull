import os
import sys
import json
import logging
import time
from datetime import datetime, UTC
from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.api_core.exceptions import DeadlineExceeded

from utils.helpers import process_message, generate_insert_id

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Check if the logger already has handlers to avoid adding duplicate handlers
if not logger.hasHandlers():
    # Create a StreamHandler to output logs to the console (stdout)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Initialize clients outside the function scope for better performance
subscriber_client = pubsub_v1.SubscriberClient()
bigquery_client = bigquery.Client()
    
# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT')
SUBSCRIPTION_NAME = os.environ.get('SUBSCRIPTION_NAME')
TABLE_ID = os.environ.get('TABLE_ID')
DLQ_TABLE_ID = os.environ.get('DLQ_TABLE_ID')

def pull_and_process_messages(request):
    """
    HTTP Cloud Function triggered by Cloud Scheduler.
    Pulls messages from a Pub/Sub subscription, processes them, and writes to BigQuery.
    """
    
    start_time_glob = datetime.now()
    try:
        logger.info(f"Function triggered at {datetime.now(UTC).isoformat()}")

        subscription_path = subscriber_client.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)

        max_messages = 1000
        total_messages_processed = 0

        # Since max messages to pull is limited from GCP side to 1000. This will
        # ensure that all available messages are pulled (assumed they are 
        # less that max_messages*max_iterations)
        max_iterations = 20

        duplicate_count = 0
        unique_messages = set()
        total_number_of_received_messages = 0
        total_number_of_acknowledged_messages = 0

        for iteration in range(max_iterations):
            logger.info(f"Starting pull iteration {iteration+1}")
            start_time_loc = datetime.now()
            try:
                response = subscriber_client.pull(
                    request={
                        "subscription": subscription_path,
                        "max_messages": max_messages,
                    },
                    timeout=5
                )
                logger.info(f"Iteration {iteration + 1}: Received "
                            f"{len(response.received_messages)} messages.")
                total_number_of_received_messages += len(response.received_messages)
            except DeadlineExceeded:
                logger.info(f"Pull deadline exceeded. No messages available.")
                response = -1
            except Exception as e:
                logger.error(f"Couldn't pull the messages. Error: {e}")

            if response == -1 or not response.received_messages:
                logger.info("No messages available.")
                break

            ack_ids = []
            rows_to_insert = []
            dlq_rows = []
            insert_ids = []

            logging.info("Start processing messages.")            
            for received_message in response.received_messages:
                message_data = received_message.message.data.decode('utf-8')
                try:
                    message_dict = json.loads(message_data)

                    message_frozenset = frozenset(message_dict.items())
                    # Check for duplicates
                    if message_frozenset in unique_messages:
                        duplicate_count += 1
                        ack_ids.append(received_message.ack_id)
                        continue  # Skip processing this duplicate message

                    unique_messages.add(message_frozenset)

                    processed_message = process_message(message_dict)
                    rows_to_insert.append(processed_message)
                    ack_ids.append(received_message.ack_id)

                    # Generate insertId
                    insert_id = generate_insert_id(processed_message)
                    insert_ids.append(insert_id)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Prepare the message for DLQ
                    dlq_row = {
                        'message_data': message_data,
                        'error_message': str(e),
                        'timestamp': datetime.now(UTC).isoformat(),
                    }
                    dlq_rows.append(dlq_row)
                    # Acknowledge the message to prevent redelivery
                    ack_ids.append(received_message.ack_id)

            # Print out summary
            set_size = sys.getsizeof(unique_messages) + sum(sys.getsizeof(item) for item in unique_messages)
            logger.info(f"Unique set size: {set_size/1024/1024} MB")
            logger.info(f"Number of duplicated messages removed: {duplicate_count}")

            # Insert successfully processed messages into BigQuery
            if rows_to_insert:
                logger.info("Start inserting messages to BQ")

                for i in range(0, len(rows_to_insert), 100):
                    #TODO This part should be implemented better
                    batch = rows_to_insert[i:i + 100]
                    batch_ids = insert_ids[i:i + 100]
                    errors = bigquery_client.insert_rows_json(
                        table=TABLE_ID,
                        json_rows=batch,
                        row_ids=batch_ids
                    )
                    if errors:
                        logger.error(f"Errors occurred during batch insertion: {errors}")
                        # Implement retry logic if necessary
                        time.sleep(2) 

                # errors = bigquery_client.insert_rows_json(TABLE_ID, rows_to_insert)
                logger.info("BQ insertion done!")
                if not errors:
                    logger.info(f"Inserted {len(rows_to_insert)} rows into BigQuery table {TABLE_ID}.")
                else:
                    logger.error(f"Errors inserting rows into BigQuery: {errors}")
                    # Move failed inserts to DLQ
                    for i, error in enumerate(errors):
                        dlq_row = {
                            'message_data': json.dumps(rows_to_insert[i]),
                            'error_message': str(error),
                            'timestamp': datetime.now(UTC).isoformat(),
                        }
                        dlq_rows.append(dlq_row)

            # Insert failed messages into DLQ BigQuery table
            if dlq_rows:
                dlq_errors = bigquery_client.insert_rows_json(DLQ_TABLE_ID, dlq_rows)
                if not dlq_errors:
                    logger.info(f"Inserted {len(dlq_rows)} rows into DLQ BigQuery table {DLQ_TABLE_ID}.")
                else:
                    logger.error(f"Errors inserting rows into DLQ table: {dlq_errors}")

                    # Add a specific log message for alerting
                    logger.error("DLQ_INSERTION_FAILURE", extra={
                        'dlq_errors': dlq_errors,
                        'dlq_rows': dlq_rows
                    })

            # Acknowledge messages
            total_number_of_acknowledged_messages += len(ack_ids)
            if ack_ids:
                subscriber_client.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": ack_ids,
                    }
                )
                logger.info(f"Acknowledged {len(ack_ids)} messages.")

            total_messages_processed += len(ack_ids)
            end_time_loc = datetime.now()
            message_diff = total_number_of_acknowledged_messages - total_number_of_received_messages
            if message_diff == 0:
                logger.info("All messages acknowledged")
            else:
                logger.warning(f"Number of acknowledged - received = {message_diff}")
            logger.info(f"Iteration elapsed time: {end_time_loc - start_time_loc}")

        logger.info(f"Total messages processed: {total_messages_processed}")
        end_time_glob = datetime.now()
        logger.info(f"Total elapsed time: {end_time_glob - start_time_glob}")
        return ('', 200)

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return (f"An error occurred: {e}", 500)