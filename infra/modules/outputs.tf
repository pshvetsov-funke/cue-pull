output "pubsub_subscription" {
  value = google_pubsub_subscription.cue_ex_playout_subscription.name
}

output "bigquery_table" {
  value = "${google_bigquery_table.cue_ex_playout_table.dataset_id}.${google_bigquery_table.cue_ex_playout_table.table_id}"
}

output "bigquery_deadletter_table" {
  value = "${google_bigquery_table.cue_ex_playout_table_deadletter.dataset_id}.${google_bigquery_table.cue_ex_playout_table_deadletter.table_id}"
}

output "pull_cue_ex_playout_function_url" {
  value = google_cloudfunctions_function.pull_cue_ex_playout_function.https_trigger_url
  description = "The URL fo the HTTP-triggered cloud run function"
}