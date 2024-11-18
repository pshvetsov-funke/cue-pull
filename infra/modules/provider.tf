provider "google" {
  credentials = var.credentials
  project     = "fmg-regio-data-as"
  region      = "europe-west3"
  default_labels = var.default_labels
}