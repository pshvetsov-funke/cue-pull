terraform {
  source = "../../modules/"
}

remote_state {
  backend = "gcs"
  config = {
    bucket = "terraform-state-bucket-data-pe" # cue-ex-playout-terraform-state
    prefix = "cue-ex-playout/dev/state"
    credentials = "${get_terragrunt_dir()}/../../secrets/fmg-regio-data-as-03ddb544b117.json"
  }
}

inputs = {
  credentials = "${get_terragrunt_dir()}/../../secrets/fmg-regio-data-as-03ddb544b117.json"
  environment = "dev"
  project_id = "fmg-regio-data-as"
  region = "europe-west3"
  location = "EU"
  
  # PubSub
  subscription_name = "cue-ex-playout-subscription-dev"
  pubsub_topic_id = "cue-ex-playout-topic-dev"
  pubsub_retention_duration = "604800s"

  # Cloud Run Function
  cloud_run_function_name = "cue-ex-playout-dev"
  function_src_dir = "${get_terragrunt_dir()}/../../../cue-ex-playout"

  # Cloud Scheduler
  scheduler_job_name = "cue-ex-playout-trigger-dev"
  scheduler_service_account = "823771140216-compute@developer.gserviceaccount.com"

  # Cloud Storage
  # function_deploy_bucket = "cue-ex-playout-function-deploy-tmp-bucket"
  function_deploy_bucket = "fmg-regio-data-as-functions"

  # BigQuery
  table_id = "dev_src_spark_articles_playout"
  dataset_id = "dev_psh_source"
  table_deadletter_id = "dev_src_spark_articles_playout_deadletter"
  bq_deletion_protection = false
    
  default_labels = {
      environment = "dev"
      managed-by = "terraform"
  }
}