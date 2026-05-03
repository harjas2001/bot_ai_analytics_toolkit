"""
gcp/storage_utils.py
─────────────────────────────────────────────────────────────────────────────
Google Cloud Storage utilities for the NLU toolkit.

Supports uploading local files to GCS and downloading blobs to local paths.
Useful for pulling monthly data exports from a shared bucket and pushing
analysis outputs back for consumption by PowerBI, Looker, or downstream jobs.

Configuration (via .env):
  GCP_PROJECT_ID               — your GCP project
  GCS_BUCKET_NAME              — default bucket
  GCS_INPUT_PREFIX             — prefix for input data blobs
  GCS_OUTPUT_PREFIX            — prefix for output result blobs
  GOOGLE_APPLICATION_CREDENTIALS — path to service account key (gitignored)
─────────────────────────────────────────────────────────────────────────────
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

GCP_PROJECT_ID    = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME   = os.getenv("GCS_BUCKET_NAME")
GCS_INPUT_PREFIX  = os.getenv("GCS_INPUT_PREFIX",  "nlu-toolkit/input/")
GCS_OUTPUT_PREFIX = os.getenv("GCS_OUTPUT_PREFIX", "nlu-toolkit/output/")


def _get_client() -> storage.Client:
    """Return an authenticated GCS client."""
    return storage.Client(project=GCP_PROJECT_ID)


def upload_file(
    local_path: str,
    blob_name: str,
    bucket_name: str = None,
    prefix: str = "",
) -> str:
    """
    Upload a local file to a GCS bucket.

    Args:
        local_path:   Path to the local file.
        blob_name:    Destination blob name within the bucket.
        bucket_name:  Bucket to upload to (defaults to GCS_BUCKET_NAME).
        prefix:       Optional prefix prepended to blob_name.

    Returns:
        Full GCS URI of the uploaded blob (gs://bucket/blob).

    Example:
        uri = upload_file("output/analysis.xlsx", "analysis.xlsx", prefix=GCS_OUTPUT_PREFIX)
    """
    bucket_name = bucket_name or GCS_BUCKET_NAME
    full_blob_name = f"{prefix}{blob_name}" if prefix else blob_name

    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(full_blob_name)
    blob.upload_from_filename(local_path)

    uri = f"gs://{bucket_name}/{full_blob_name}"
    print(f"Uploaded: {local_path} → {uri}")
    return uri


def download_file(
    blob_name: str,
    local_path: str,
    bucket_name: str = None,
    prefix: str = "",
) -> str:
    """
    Download a GCS blob to a local file.

    Args:
        blob_name:    Name of the blob in the bucket.
        local_path:   Destination local path.
        bucket_name:  Bucket to download from (defaults to GCS_BUCKET_NAME).
        prefix:       Optional prefix prepended to blob_name.

    Returns:
        Local path of the downloaded file.

    Example:
        path = download_file("fallback_aug.csv", "data/fallback.csv", prefix=GCS_INPUT_PREFIX)
    """
    bucket_name = bucket_name or GCS_BUCKET_NAME
    full_blob_name = f"{prefix}{blob_name}" if prefix else blob_name

    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(full_blob_name)
    blob.download_to_filename(local_path)

    print(f"Downloaded: gs://{bucket_name}/{full_blob_name} → {local_path}")
    return local_path


def list_blobs(prefix: str = None, bucket_name: str = None) -> list[str]:
    """
    List all blob names in a bucket, optionally filtered by prefix.

    Args:
        prefix:      Filter blobs by this prefix (e.g. 'nlu-toolkit/input/').
        bucket_name: Bucket to list (defaults to GCS_BUCKET_NAME).

    Returns:
        List of blob name strings.

    Example:
        blobs = list_blobs(prefix=GCS_INPUT_PREFIX)
    """
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = _get_client()
    blobs = client.list_blobs(bucket_name, prefix=prefix)
    return [b.name for b in blobs]


def upload_output(local_path: str, blob_name: str = None, bucket_name: str = None) -> str:
    """
    Convenience wrapper: upload a file to the configured output prefix.

    Args:
        local_path:   Path to the local output file.
        blob_name:    Blob name (defaults to the filename).
        bucket_name:  Bucket (defaults to GCS_BUCKET_NAME).

    Returns:
        Full GCS URI.
    """
    blob_name = blob_name or Path(local_path).name
    return upload_file(local_path, blob_name, bucket_name=bucket_name, prefix=GCS_OUTPUT_PREFIX)


def download_input(blob_name: str, local_path: str = None, bucket_name: str = None) -> str:
    """
    Convenience wrapper: download a file from the configured input prefix.

    Args:
        blob_name:   Blob name within the input prefix.
        local_path:  Local destination (defaults to data/<blob_name>).
        bucket_name: Bucket (defaults to GCS_BUCKET_NAME).

    Returns:
        Local path of the downloaded file.
    """
    local_path = local_path or f"data/{blob_name}"
    return download_file(blob_name, local_path, bucket_name=bucket_name, prefix=GCS_INPUT_PREFIX)
