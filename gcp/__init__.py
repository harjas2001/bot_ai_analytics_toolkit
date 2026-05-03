"""
gcp/
────
Google Cloud Platform utilities for the conversational AI NLU toolkit.

Modules:
  storage_utils   — upload / download files to/from Cloud Storage
  bigquery_utils  — push DataFrames to BigQuery, run queries

Authentication:
  Set GOOGLE_APPLICATION_CREDENTIALS in .env pointing to your service account
  key file, or use Application Default Credentials (ADC) if running on GCP.
"""
