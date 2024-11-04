import os
import json
import logging
from datetime import datetime, UTC
from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.api_core.exceptions import DeadlineExceeded

from utils.helpers import process_message

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

dev_run = True
if dev_run:
    # Dev case
    os.environ['GCP_PROJECT'] = 'fmg-regio-data-as'
    os.environ['SUBSCRIPTION_NAME'] = 'cue-playout-subscription'
    os.environ['TABLE_ID'] = 'fmg-regio-data-as.dev_psh_source.dev_src_spark_articles_playout'
    os.environ['DLQ_TABLE_ID'] = 'fmg-regio-data-as.dev_psh_source.dev_src_spark_articles_playout_deadletter'
    
# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT')
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

            for received_message in response.received_messages:
                message_data = received_message.message.data.decode('utf-8')
                try:
                    message_dict = json.loads(message_data)
                    processed_message = process_message(message_dict)
                    rows_to_insert.append(processed_message)
                    ack_ids.append(received_message.ack_id)
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

            # Insert successfully processed messages into BigQuery
            if rows_to_insert:
                errors = bigquery_client.insert_rows_json(TABLE_ID, rows_to_insert)
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
            logger.info(f"Iteration elapsed time: {end_time_loc - start_time_loc}")

        logger.info(f"Total messages processed: {total_messages_processed}")
        end_time_glob = datetime.now()
        logger.info(f"Total elapsed time: {end_time_glob - start_time_glob}")
        return ('', 200)

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return (f"An error occurred: {e}", 500)


if __name__ == "__main__":
    #TODO check duplicates. Is there a case when a message is not aknowledged,
    # despite being processed?
    
    pull_and_process_messages(None)