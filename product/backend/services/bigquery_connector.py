"""Connect to Google BigQuery and run a SQL query.

Authentication uses Application Default Credentials (ADC) — the identity of the
environment the backend runs in:

* On Cloud Run: the service's runtime service account (Workload Identity).
* Locally for development: run `gcloud auth application-default login`.

Service account key files are intentionally NOT accepted. Credentials must never
travel through the browser or be embedded in the repository.
"""
import os

import pandas as pd
from fastapi import HTTPException

try:
    from google.cloud import bigquery
    _BQ_AVAILABLE = True
except ImportError:
    _BQ_AVAILABLE = False


def query_bigquery(table_path: str) -> pd.DataFrame:
    """
    Fetch all rows from a BigQuery table using Application Default Credentials.

    Parameters
    ----------
    table_path : str
        BigQuery table path, e.g.  project.dataset.table

    Returns
    -------
    pd.DataFrame
        Table contents as a DataFrame.
    """
    if not _BQ_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="BigQuery support is not installed. Run: pip install google-cloud-bigquery db-dtypes",
        )

    if not table_path or not table_path.strip():
        raise HTTPException(status_code=400, detail="Table path cannot be empty.")

    query = f"SELECT * FROM `{table_path.strip()}`"

    # Build BigQuery client from ADC. Project is inferred from the credentials /
    # GOOGLE_CLOUD_PROJECT, with an optional explicit override.
    try:
        client = bigquery.Client(project=os.getenv("BIGQUERY_PROJECT") or None)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not initialise BigQuery credentials. The server is not "
                f"authenticated with Google Cloud: {e}"
            ),
        )

    # Run query
    try:
        job = client.query(query)
        df = job.to_dataframe()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"BigQuery query failed: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Query returned no rows.")

    return df.reset_index(drop=True)
