data "google_pubsub_topic" "pubsub_topic" {
  name = var.pubsub_topic_id
}

resource "google_pubsub_subscription" "cue_ex_playout_subscription" {
  name  = var.subscription_name
  topic = data.google_pubsub_topic.pubsub_topic.name

  message_retention_duration = "4200s" # 1h 10m
  retain_acked_messages = false
  ack_deadline_seconds = "600"

  enable_exactly_once_delivery = true
}
