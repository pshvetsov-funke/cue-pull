# pull

1. Need to create bucket gs://cue-ex-playout-terraform-state
    `gsutil mb gs://cue-ex-playout-terraform-state`
2. Require Service account with following roles
 - roles/bigquery.admin
 - roles/cloudfunctions.developer
 - roles/iam.serviceAccountUser
 - roles/pubsub.admin
 - roles/storage.admin
 - roles/cloudscheduler.admin

 - roles/iam.serviceAccountUser ?


Bucket for managing terraform state is 

Service account used is ex-cue-playout

Roles for service account:
 


gcloud iam service-accounts create cue-ex-playout-terraform \
    --project=fmg-regio-data-as \
    --description="Service account for managing Pub/Sub, Cloud Run Function, Cloud Storage, and BigQuery ressources for cue-ex-playout pipeline" \
    --display-name="cue-ex-playout-terraform"


gcloud projects add-iam-policy-binding fmg-regio-data-as \
    --member="serviceAccount:cue-ex-playout-terraform@fmg-regio-data-as.iam.gserviceaccount.com" \
    --role="roles/cloudscheduler.admin"




gcloud projects get-iam-policy fmg-regio-data-as \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:cue-ex-playout-terraform@fmg-regio-data-as.iam.gserviceaccount.com" \
  --format="table(bindings.role)"