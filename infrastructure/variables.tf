variable "project_id" {
  type        = string
  description = "Google Cloud project ID"
  default     = "fmg-regio-data-as"
}

variable "region" {
  type        = string
  description = "Google Cloud region"
  default     = "europe-west3"
}

variable "subscription_name" {
  type        = string
  description = "Pub/Sub subscription name"
  default     = "cue-playout-subscription"
}

variable "dataset_id" {
  type        = string
  description = "BigQuery dataset ID"
  default     = "dev_psh_source"
}

variable "table_id" {
  type        = string
  description = "BigQuery table ID"
  default     = "dev_src_spark_articles_playout"
}

variable "topic_id" {
  type        = string
  description = "PubSub playout topic id"
  default     = "data-spark-article-playout"
}

variable "location" {
    type = string
    description = "Location of the dataset"
    default = "EU"
  
}