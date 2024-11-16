resource "google_cloud_scheduler_job" "trigger_job" {
  name             = var.scheduler_job_name
  description      = "Job to trigger cloud run function that pulls messages and save them to BQ"
  schedule         = "*/5 * * * *"
  time_zone        = "Europe/Berlin"
  attempt_deadline = "180s"

  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.pull_cue_ex_playout_function.https_trigger_url
    
    # Body is irrelevent. Function should just receive post request.
    body        = base64encode("{\"foo\":\"bar\"}")
    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = var.scheduler_service_account
      audience = google_cloudfunctions_function.pull_cue_ex_playout_function.https_trigger_url
    }
  }
}