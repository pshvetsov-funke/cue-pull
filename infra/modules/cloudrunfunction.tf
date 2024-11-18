# Define bucket where the function code will be stored
# resource "google_storage_bucket" "cloud_run_function_bucket" {
#     name = var.function_deploy_bucket
#     location = var.location
# }

data "google_storage_bucket" "cloud_run_function_deployment_bucket" {
  name =  var.function_deploy_bucket
}

data "archive_file" "function_src" {
  type = "zip"
  source_dir = var.function_src_dir
  output_path = "${path.module}/index.zip"
  depends_on = [ data.google_storage_bucket.cloud_run_function_deployment_bucket ]
}

resource "google_storage_bucket_object" "archive" {
  # Why not just index.zip? If source code changes, terraform cannot detect it.
  # So cloud run function will not be redeployed. Provide unique filename to always
  # redeploy the function if content is changed.
  name   = "${var.cloud_run_function_name}/index_${data.archive_file.function_src.output_md5}.zip"
  bucket = data.google_storage_bucket.cloud_run_function_deployment_bucket.name
  source = "${path.module}/index.zip"
  depends_on = [ data.archive_file.function_src ]
}

resource "google_cloudfunctions_function" "pull_cue_ex_playout_function" {
  name        = var.cloud_run_function_name
  description = "Cloud Run Function to pull data from pubsub topic and injest it into BQ"
  runtime     = "python312"

  available_memory_mb = 512
  source_archive_bucket = data.google_storage_bucket.cloud_run_function_deployment_bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  entry_point           = "pull_and_process_messages"
  trigger_http = true
  https_trigger_security_level = "SECURE_ALWAYS"
  timeout = 240
  region = var.region

  environment_variables = {
    GCP_PROJECT = var.project_id
    SUBSCRIPTION_NAME = var.subscription_name
    TABLE_ID = "${var.project_id}.${var.dataset_id}.${var.table_id}"
    DLQ_TABLE_ID = "${var.project_id}.${var.dataset_id}.${var.table_deadletter_id}"
  }

  depends_on = [ google_storage_bucket_object.archive ]
}