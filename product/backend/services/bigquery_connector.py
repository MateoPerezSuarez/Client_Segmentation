"""Connect to Google BigQuery using a service account key and run a SQL query."""
import json

import pandas as pd
from fastapi import HTTPException

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    _BQ_AVAILABLE = True
except ImportError:
    _BQ_AVAILABLE = False


def query_bigquery(credentials_json: str, table_path: str) -> pd.DataFrame:
    if not _BQ_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="BigQuery support is not installed. Run: pip install google-cloud-bigquery db-dtypes"
        )
    """
    Fetch all rows from a BigQuery table using a service account JSON key.

    Parameters
    ----------
    credentials_json : str
        Full content of a Google service account key file (JSON string).
    table_path : str
        BigQuery table path, e.g.  project.dataset.table

    Returns
    -------
    pd.DataFrame
        Table contents as a DataFrame.
    """
    # Parse credentials
    try:
        creds_dict = json.loads(credentials_json)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid credentials: not valid JSON.")

    required_keys = {"type", "project_id", "private_key", "client_email"}
    missing = required_keys - creds_dict.keys()
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Credentials JSON is missing required fields: {', '.join(sorted(missing))}."
        )

    if creds_dict.get("type") != "service_account":
        raise HTTPException(
            status_code=400,
            detail="Only service account credentials are supported (\"type\": \"service_account\")."
        )

    if not table_path or not table_path.strip():
        raise HTTPException(status_code=400, detail="Table path cannot be empty.")

    query = f"SELECT * FROM `{table_path.strip()}`"

    # Build BigQuery client
    try:
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        client = bigquery.Client(
            credentials=credentials,
            project=creds_dict["project_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not authenticate with BigQuery: {e}")

    # Run query
    try:
        job = client.query(query)
        df = job.to_dataframe()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"BigQuery query failed: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Query returned no rows.")

    # Normalise column names (BigQuery may return mixed types in some columns)
    for col in df.columns:
        try:
            df[col] = df[col].where(df[col].isna(), df[col])
        except Exception:
            pass

    return df.reset_index(drop=True)
