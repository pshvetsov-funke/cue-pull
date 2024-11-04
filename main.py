import time
import json
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import bigquery

def pull_messages(subscription_name, table_id):
    """Pulls messages from a Pub/Sub subscription, processes them, and writes to BigQuery."""
    
    pull_multiplicator = 10
    start_time = datetime.now()
    # Initialize a Subscriber client
    subscriber = pubsub_v1.SubscriberClient()
    # Initialize a BigQuery client
    bigquery_client = bigquery.Client()
    
    while True:
        print(f"Checking for messages on {subscription_name}...")
        
        # The maximum number of messages to retrieve per request
        max_messages = 1000  # Adjust as needed (max 1000)
        n_iterations = 10
        n_tries_max = 2
        n_tries = 0

        for i_iter in range(n_iterations):
            # Pull messages. Try to 
            print(f"Pulling messages. Iteration {i_iter+1} out of {n_iterations}")
            response = subscriber.pull(
                request={
                    "subscription": subscription_name,
                    "max_messages": max_messages,
                },
                timeout=10  # Adjust the timeout as needed
            )
            
            if not response.received_messages:
                print("No messages available.")
                n_tries += 1
                if n_tries >= n_tries_max:
                    print("Max number of tries achieved. No messages found")
                    break
            else:
                print(f"Received {len(response.received_messages)} messages.")
                ack_ids = []
                rows_to_insert = []  # List to hold the rows to be inserted into BigQuery
                
                for received_message in response.received_messages:
                    message_data = received_message.message.data.decode('utf-8')
                    try:
                        # Parse the JSON message
                        message_dict = json.loads(message_data)
                        # Append the message to the list of rows to insert
                        rows_to_insert.append(message_dict)
                        # Collect ack IDs to acknowledge messages after processing
                        ack_ids.append(received_message.ack_id)
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON message: {e}")
                        # Optionally, handle the invalid message (e.g., log, send to dead-letter queue)
                
                if rows_to_insert:
                    # Write to BigQuery
                    errors = bigquery_client.insert_rows_json(table_id, rows_to_insert)
                    if errors == []:
                        print(f"New rows have been added to {table_id}.")
                        # Acknowledge all successfully processed messages
                        subscriber.acknowledge(
                            request={
                                "subscription": subscription_name,
                                "ack_ids": ack_ids,
                            }
                        )
                        print(f"Acknowledged {len(ack_ids)} messages.")
                    else:
                        print(f"Encountered errors while inserting rows: {errors}")
                        # Optionally, handle errors (e.g., retry, send to dead-letter queue)
                else:
                    print("No valid messages to insert into BigQuery.")
        
        # Wait for 15 minutes before checking again
        end_time = datetime.now()
        print(f"Total elapsed time: {end_time-start_time}")
        print("Sleeping for 15 minutes...")
        time.sleep(2*60)  # 15 minutes in seconds

if __name__ == "__main__":
    # Replace with your project ID, subscription ID, and BigQuery table ID
    subscription_name = "projects/fmg-regio-data-as/subscriptions/cue-playout-subscription"
    table_id = "fmg-regio-data-as.dev_psh_source.dev_src_spark_articles_playout"
    
    pull_messages(subscription_name, table_id)
