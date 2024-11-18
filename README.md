# Article metadata (replacement for data-spark-ingest) pipeline
This repository contains cloud run function code and infrastructure code (terraform) for the pipeline to transfer article metadata (previously playout data) into BigQuery warehouse. This pipeline should replace the data-spark-ingest pipeline.

# Architecture
![architecture](./images/architecture.PNG)

# Pre-requisites
## Python
Python is required to the run script `main_convert_shema.py`. Version is non-relevant.
## Terraform/terragrunt
Terraform is required for infrastructure as a code deployment. Terragrunt is required for managing environments. They can be installed with:
```bash
brew install terraform
brew install terragrunt
```
## Make
For streamlining the deployment process and for ensuring that python scripts are not forgotten to run, make build tool is used. You can install make on MacOS with:
brew install make
```bash
brew install make
```
or with other CLI tools as:
```bash
xcode-select --install
```
## Credentials
For infrastructure deployment you will require service account credentials with following roles:
 - roles/bigquery.admin
 - roles/cloudfunctions.developer
 - roles/cloudscheduler.admin
 - roles/iam.serviceAccountUser
 - roles/pubsub.admin
 - roles/storage.admin

Currently following service account is used: `cue-ex-playout-terraform@fmg-regio-data-as.iam.gserviceaccount.com`
The service account key should be saved in `./infra/secrets/fmg-regio-data-as-... .json`file.

# How to deploy
Terraform uses a global state, that is sync (best practice) through a GCS bucket (saw the idea in data-spark-ingest project, credits to bbartosch), so its required to create this bucket manually beforehand. It can be created with command:
```bash
gsutil mb gs://cue-ex-playout-terraform-state
```
The name of the bucket should be the same as in `remote_state.config.bucket` in `terragrunt.hcl` for your environment.

From the root folder (the folder where `Makefile` is stored) use:
```bash
make terraform-plan
```
and if satisfied:
```bash
make terraform-apply
```
thats it. For detailed workflow of what is happening see `Makefile`. Cloud run function deployment accurs with following steps:
1. The source code (`pul-cue-ex-playout` folder) is archived into `./infra/modules/index.zip` archive.
2. The .zip arhchive is deployed into a GCS bucket with a name `index_<md5_hash>.zip`, where <md5_hash> is a md5 hash of the content of the zip archive. In this way it is ensured, that if the source code of the function is changed - the cloud run function will be redeployed.
3. The cloud run function is deployed from zip archive from step 2 and with configuration defined in `cloudrunfunction.tf` file.

# Commands for service-account management

Create service account:
```bash
gcloud iam service-accounts create <ACCOUNT_NAME> \
    --project=<PROJECT_NAME> \
    --description="Some describefull descriptive description for describing that can be desribed" \
    --display-name="<ACCOUNT_NAME>"
```
Check roles
```bash
gcloud projects get-iam-policy <PROJECT_NAME> \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:<SERVICE_ACCOUNT_EMAIL>" \
        --format="table(bindings.role)"
```
Add new role
```bash
gcloud projects add-iam-policy-binding <PROJECT_NAME> \
    --member="serviceAccount:<SERVICE_ACCOUNT_EMAIL>" \
    --role="<ROLE>"
```
`<ROLE>` should be like described in "Credentials", for example `roles/bigquery.admin`