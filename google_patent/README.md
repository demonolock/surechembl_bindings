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
