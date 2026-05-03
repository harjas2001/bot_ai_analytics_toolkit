"""
gcp/bigquery_utils.py
─────────────────────────────────────────────────────────────────────────────
BigQuery utilities for the NLU toolkit.

Push analysis results to BigQuery for long-term storage, trending, and
consumption by BI tools (PowerBI, Looker, Data Studio). Also supports
running queries and returning results as pandas DataFrames.

Configuration (via .env):
  GCP_PROJECT_ID      — your GCP project
  BQ_DATASET_ID       — target BigQuery dataset
  BQ_TABLE_*          — individual table names per output type
  GOOGLE_APPLICATION_CREDENTIALS — path to service account key (gitignored)
─────────────────────────────────────────────────────────────────────────────
"""

import os
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET_ID  = os.getenv("BQ_DATASET_ID", "conversational_ai")


def _get_client() -> bigquery.Client:
    """Return an authenticated BigQuery client."""
    return bigquery.Client(project=GCP_PROJECT_ID)


def push_dataframe(
    df: pd.DataFrame,
    table_id: str,
    dataset_id: str = None,
    project_id: str = None,
    if_exists: str = "append",
    schema: list = None,
) -> None:
    """
    Push a pandas DataFrame to a BigQuery table.

    Args:
        df:         DataFrame to upload.
        table_id:   Target table name.
        dataset_id: Dataset (defaults to BQ_DATASET_ID).
        project_id: GCP project (defaults to GCP_PROJECT_ID).
        if_exists:  'append' (default), 'replace', or 'fail'.
        schema:     Optional list of bigquery.SchemaField to enforce schema.

    Example:
        push_dataframe(results_df, table_id="training_phrase_analysis")
    """
    project_id = project_id or GCP_PROJECT_ID
    dataset_id = dataset_id or BQ_DATASET_ID
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"

    client = _get_client()

    disposition_map = {
        "append":  bigquery.WriteDisposition.WRITE_APPEND,
        "replace": bigquery.WriteDisposition.WRITE_TRUNCATE,
        "fail":    bigquery.WriteDisposition.WRITE_EMPTY,
    }

    job_config = bigquery.LoadJobConfig(
        write_disposition=disposition_map.get(if_exists, bigquery.WriteDisposition.WRITE_APPEND),
        schema=schema or [],
        autodetect=(schema is None),
    )

    job = client.load_table_from_dataframe(df, full_table_id, job_config=job_config)
    job.result()  # wait for completion

    table = client.get_table(full_table_id)
    print(f"Pushed {len(df):,} rows → {full_table_id} (total rows: {table.num_rows:,})")


def query_to_dataframe(query: str, project_id: str = None) -> pd.DataFrame:
    """
    Run a BigQuery SQL query and return results as a pandas DataFrame.

    Args:
        query:      Standard SQL query string.
        project_id: GCP project (defaults to GCP_PROJECT_ID).

    Returns:
        Query results as a DataFrame.

    Example:
        df = query_to_dataframe(
            f"SELECT intent, COUNT(*) as count FROM `{GCP_PROJECT_ID}.{BQ_DATASET_ID}.training_phrase_analysis` GROUP BY intent"
        )
    """
    project_id = project_id or GCP_PROJECT_ID
    client = _get_client()
    df = client.query(query, project=project_id).to_dataframe()
    print(f"Query returned {len(df):,} rows.")
    return df


def ensure_dataset_exists(dataset_id: str = None, location: str = "australia-southeast1") -> None:
    """
    Create the BigQuery dataset if it does not already exist.

    Args:
        dataset_id: Dataset to create (defaults to BQ_DATASET_ID).
        location:   GCP region for the dataset.

    Example:
        ensure_dataset_exists()
    """
    dataset_id = dataset_id or BQ_DATASET_ID
    client = _get_client()
    full_dataset_id = f"{GCP_PROJECT_ID}.{dataset_id}"

    dataset = bigquery.Dataset(full_dataset_id)
    dataset.location = location

    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset ready: {full_dataset_id} ({location})")


def push_phrase_analysis(df: pd.DataFrame, table_id: str = None) -> None:
    """
    Convenience wrapper: push training phrase analysis results to BigQuery.
    Maps directly to the output of tools/analyse_training_phrases.py.

    Args:
        df:       Results DataFrame from the analysis script.
        table_id: Target table (defaults to BQ_TABLE_PHRASE_ANALYSIS env var).
    """
    table_id = table_id or os.getenv("BQ_TABLE_PHRASE_ANALYSIS", "training_phrase_analysis")
    push_dataframe(df, table_id=table_id)


def push_topic_results(df: pd.DataFrame, table_id: str = None) -> None:
    """
    Convenience wrapper: push fallback topic modelling results to BigQuery.
    Maps directly to the output of the nlu-fallback-topic-modeller pipeline.

    Args:
        df:       Results DataFrame from the topic modeller.
        table_id: Target table (defaults to BQ_TABLE_TOPIC_RESULTS env var).
    """
    table_id = table_id or os.getenv("BQ_TABLE_TOPIC_RESULTS", "fallback_topic_results")
    push_dataframe(df, table_id=table_id)
