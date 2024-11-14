resource "google_bigquery_dataset" "psh_source" {
  dataset_id = var.dataset_id
  location   = var.location
}

resource "google_bigquery_table" "playout_table" {
  dataset_id = google_bigquery_dataset.psh_source.dataset_id
  table_id   = var.table_id
  schema     = file("${path.module}/schemas/bq_schema.json")
}
