import os
import json
import logging
import time
from datetime import datetime, UTC
from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.api_core.exceptions import DeadlineExceeded

from utils.logging import setup_logging
from utils.parser import Parser

# # Debug stuff
# from dotenv import load_dotenv
# load_dotenv()

# Create a logger
logger = setup_logging()

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

        parser = Parser(
            max_iterations=20
        )

        for iteration in range(parser.max_iterations):
            logger.info(f"Starting pull iteration {iteration+1}")
            start_time_loc = datetime.now()
            try:
                response = subscriber_client.pull(
                    request={
                        "subscription": subscription_path,
                        "max_messages": parser.max_messages,
                    },
                    timeout=5
                )
                logger.info(f"Iteration {iteration + 1}: Received "
                            f"{len(response.received_messages)} messages.")
                parser.total_received_messages += len(response.received_messages)
            except DeadlineExceeded:
                logger.info(f"Pull deadline exceeded. No messages available.")
                response = -1
            except Exception as e:
                logger.exception(f"Couldn't pull the messages. Error: {e}")
                raise

            if response == -1 or not response.received_messages:
                logger.info("No messages available.")
                break

            parser.reset_iteration_info()
            logging.info("Start processing messages.")
            for received_message in response.received_messages:
                try:
                    parser.process_message(received_message)
                except Exception as e:
                    logger.exception(f"Error processing message: {e}")
                    parser.add_message_to_dlq(received_message, e)

            # Print out summary
            logger.info(f"Number of duplicated messages removed: {parser.iter_duplicate_count}")
            parser.total_duplicate_count += parser.iter_duplicate_count

            # Insert successfully processed messages into BigQuery
            if parser.iter_rows_to_insert:
                logger.info("Start inserting messages to BQ")
                insertion_errors = []
                for i in range(0, len(parser.iter_rows_to_insert), parser.BQI_STEP):
                    batch = parser.iter_rows_to_insert[i:i + parser.BQI_STEP]

                    # Add timestamp
                    for b in batch:
                        b['ingestionTimestamp'] =  datetime.now(UTC).isoformat()

                    errors = bigquery_client.insert_rows_json(
                        table=TABLE_ID,
                        json_rows=batch
                    )
                    if errors:
                        insertion_errors.append(errors)
                        logger.error(f"Errors occurred during batch insertion: {errors}")
                        # Implement retry logic if necessary
                        time.sleep(2) 

                logger.info("BQ insertion done!")
                if not insertion_errors:
                    logger.info(f"Inserted {len(parser.iter_rows_to_insert)} rows "#
                                f"into BigQuery table {TABLE_ID}.")
                else:
                    logger.error(f"Errors inserting rows into BigQuery: {insertion_errors}")
                    # Move failed inserts to DLQ
                    for i, error in enumerate(insertion_errors):
                        dlq_row = {
                            'message_data': json.dumps(parser.iter_rows_to_insert[i]),
                            'error_message': str(error),
                            'timestamp': datetime.now(UTC).isoformat(),
                        }
                        parser.iter_dlq_rows.append(dlq_row)

            # Insert failed messages into DLQ BigQuery table
            if parser.iter_dlq_rows:
                insertion_errors = []
                for i in range(0, len(parser.iter_dlq_rows), parser.BQI_STEP):
                    batch = parser.iter_dlq_rows[i:i + parser.BQI_STEP]
                    dlq_errors = bigquery_client.insert_rows_json(
                        table=DLQ_TABLE_ID,
                        json_rows=batch
                    )
                    if dlq_errors:
                        insertion_errors.append(dlq_errors)
                        logger.error(f"Errors occured during inserting DLQ table: {dlq_errors}")

                logger.info("BQ DLQ insertion done!")
                if not dlq_errors:
                    logger.info(f"Inserted {len(parser.iter_dlq_rows)} rows into "
                                f"DLQ BigQuery table {DLQ_TABLE_ID}.")
                else:
                    logger.error(f"Errors inserting rows into DLQ table: {insertion_errors}")

                    # Add a specific log message for alerting
                    logger.error("DLQ_INSERTION_FAILURE", extra={
                        'dlq_errors': insertion_errors,
                        'dlq_rows': parser.iter_dlq_rows
                    })

            # Acknowledge messages
            parser.total_acknowledged_messages += len(parser.iter_ack_ids)
            if parser.iter_ack_ids:
                subscriber_client.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": parser.iter_ack_ids,
                    }
                )
                logger.info(f"Acknowledged {len(parser.iter_ack_ids)} messages.")

            parser.total_messages_processed += len(parser.iter_rows_to_insert)
            end_time_loc = datetime.now()
            message_diff = (parser.total_acknowledged_messages 
                            - parser.total_received_messages)
            if message_diff == 0:
                logger.info("All messages acknowledged")
            else:
                logger.warning(f"Number of acknowledged - received = {message_diff}")
            logger.info(f"Iteration elapsed time: {end_time_loc - start_time_loc}")

        logger.info(f"Total messages processed: {parser.total_messages_processed}")
        logger.info(f"Total duplicates removed: {parser.total_duplicate_count}")
        end_time_glob = datetime.now()
        logger.info(f"Total elapsed time: {end_time_glob - start_time_glob}")
        return ('', 200)

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return (f"An error occurred: {e}", 500)