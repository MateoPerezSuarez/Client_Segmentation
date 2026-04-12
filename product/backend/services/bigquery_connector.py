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


def query_bigquery(credentials_json: str, query: str) -> pd.DataFrame:
    if not _BQ_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="BigQuery support is not installed. Run: pip install google-cloud-bigquery db-dtypes"
        )
    """
    Execute a SQL query against BigQuery using a service account JSON key.

    Parameters
    ----------
    credentials_json : str
        Full content of a Google service account key file (JSON string).
    query : str
        Standard SQL query, e.g.  SELECT * FROM `project.dataset.table` LIMIT 500000

    Returns
    -------
    pd.DataFrame
        Query results as a DataFrame.
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

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty.")

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
