from main import pull_and_process_messages

if __name__ == "__main__":
    #TODO check duplicates. Is there a case when a message is not aknowledged,
    # despite being processed?

    # Local dev case
    env_vars = {
        'GCP_PROJECT': 'fmg-regio-data-as',
        'SUBSCRIPTION_NAME': 'cue-playout-subscription',
        'TABLE_ID': 'fmg-regio-data-as.dev_psh_source.dev_src_spark_articles_playout_deduplicated',
        'DLQ_TABLE_ID': 'fmg-regio-data-as.dev_psh_source.dev_src_spark_articles_playout_deadletter'
    }
    pull_and_process_messages(None, dev_evn=env_vars)