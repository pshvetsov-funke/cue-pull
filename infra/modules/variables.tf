variable "project_id" {
  type        = string
  description = "Google Cloud project ID"
}

variable "region" {
  type        = string
  description = "Google Cloud region"
}

variable "subscription_name" {
  type        = string
  description = "Pub/Sub subscription name"
}

variable "dataset_id" {
  type        = string
  description = "BigQuery dataset ID"
}

variable "table_id" {
  type        = string
  description = "BigQuery table ID"
}

variable "table_deadletter_id" {
  type        = string
  description = "BigQuery deadletter table ID"
}

variable "location" {
    type = string
    description = "Location of the dataset"
}

variable "credentials" {
  description = "Service Account credentials for GCP"
  type        = string
  default = "non-existing-credentials.json"
}

variable "default_labels" {
  description = "Default labels for all resources"
  type        = map(string)
}

variable "pubsub_topic_id" {
  type        = string
  description = "PubSub playout topic id"
}

variable "cloud_run_function_name" {
  type = string
  description = "Cloud run function"
}

variable "function_src_dir" {
  type = string
  description = "Path to function source code"
}

variable "function_deploy_bucket" {
  type = string
  description = "Temporary bucket for cloud run function deployment"
}

variable "scheduler_job_name" {
  type = string
  description = "Cloud scheduler job name. It triggers cloud run function that pulls data."
}

variable "scheduler_service_account" {
  type = string
  description = "Service account for cloud scheduler (uses pre-existing account)"
}

variable "bq_deletion_protection" {
  type = bool
  description = "Deletion protection flag. False - can be deleted by terraform?"
}

variable "pubsub_retention_duration" {
  type = string
  description = "Retention duration of PubSub topic"
}