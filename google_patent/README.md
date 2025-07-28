1. Installation bigquery
https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python

```bash
pip install --upgrade google-cloud-bigquery
```
	
2. Init Google project
https://cloud.google.com/sdk/docs/install
```bash
gcloud init
```
Select your project or create a new one.

3. Authorization
```text
gcloud config set billing/quota_project PROJECT_ID
```


To use df = pandas_gbq.read_gbq(query, project_id=PROJECT_ID)
you need to create a service account.

# 1. Set project
gcloud config set project YOUR_PROJECT_ID

# 2. Create service account
gcloud iam service-accounts create my-bq-service-account \
  --description="Service account for BigQuery access" \
  --display-name="BigQuery Service Account"

# 3. Grant roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:my-bq-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:my-bq-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# 4. Create and download key
gcloud iam service-accounts keys create ~/my-bq-key.json \
  --iam-account=my-bq-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 5. Set the environment variable in your shell
export GOOGLE_APPLICATION_CREDENTIALS=~/my-bq-key.json
