data "google_pubsub_topic" "playout_topic" {
  name = var.topic_id
}

resource "google_pubsub_subscription" "cue_playout_subscription" {
  name  = var.subscription_name
  topic = data.google_pubsub_topic.playout_topic.name

  message_retention_duration = "4200s" # 1h 10m
  retain_acked_messages = false
  ack_deadline_seconds = "600"

  enable_exactly_once_delivery = true
  expiration_policy {
    ttl = "2678400s"
  }
}
