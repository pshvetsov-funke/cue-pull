output "pubsub_subscription" {
  value = google_pubsub_subscription.cue_playout_subscription.name
}

output "bigquery_table" {
  value = "${google_bigquery_table.playout_table.dataset_id}.${google_bigquery_table.playout_table.table_id}"
}
