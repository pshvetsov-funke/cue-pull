resource "google_bigquery_dataset" "cue_ex_playout_dataset" {
  dataset_id = var.dataset_id
  location   = var.location
}

resource "google_bigquery_table" "cue_ex_playout_table" {
  dataset_id = google_bigquery_dataset.cue_ex_playout_dataset.dataset_id
  table_id   = var.table_id
  schema     = file("${path.module}/bq_schema.json")
  time_partitioning {
    type = "DAY"
    field = "ingestionTimestamp"
  }
  clustering = [ "publication" ]
  deletion_protection = var.bq_deletion_protection
}

resource "google_bigquery_table" "cue_ex_playout_table_deadletter" {
  dataset_id = google_bigquery_dataset.cue_ex_playout_dataset.dataset_id
  table_id   = var.table_deadletter_id
  schema     = file("${path.module}/bq_deadletter_schema.json")
  deletion_protection = var.bq_deletion_protection
}