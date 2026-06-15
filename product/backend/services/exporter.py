"""Export a segmentation result to Google Cloud — BigQuery and/or Cloud Storage.

Authentication uses Application Default Credentials (ADC), i.e. the identity of
the environment the backend runs in (the Cloud Run runtime service account in
production, or `gcloud auth application-default login` locally).

The destination is fully parameterised: it can point to *our* project or to a
*client's* own project. For a client project, the client must grant the backend's
runtime service account access on their side:

    BigQuery  →  roles/bigquery.dataEditor (+ jobUser) on the target dataset
    GCS       →  roles/storage.objectAdmin on the target bucket
"""
import io
import json
import os
from typing import Any, Dict

import pandas as pd
from fastapi import HTTPException

try:
    from google.cloud import bigquery
    _BQ_AVAILABLE = True
except ImportError:
    _BQ_AVAILABLE = False

try:
    from google.cloud import storage
    _GCS_AVAILABLE = True
except ImportError:
    _GCS_AVAILABLE = False


# Metadata columns appended to every exported run so each row is self-describing
# and runs can be told apart / compared over time.
_META_COLS = ["run_id", "run_timestamp", "method", "params"]


def _enrich(df: pd.DataFrame, run_meta: Dict[str, Any]) -> pd.DataFrame:
    out = df.copy()
    out["run_id"] = run_meta["run_id"]
    out["run_timestamp"] = pd.Timestamp(run_meta["run_timestamp"])
    out["method"] = run_meta["method"]
    out["params"] = json.dumps(run_meta["params"], default=str)
    return out


def export_to_bigquery(df: pd.DataFrame, table_path: str, run_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Append the run to a BigQuery table (created if needed) partitioned by
    run_timestamp, and refresh a `<table>_latest` view pointing at the newest run.

    Parameters
    ----------
    table_path : str
        Fully-qualified destination, e.g.  project.dataset.table
    """
    if not _BQ_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="BigQuery support is not installed. Run: pip install google-cloud-bigquery db-dtypes",
        )

    table_path = (table_path or "").strip()
    if table_path.count(".") != 2:
        raise HTTPException(
            status_code=400,
            detail="bq_table must be fully qualified as project.dataset.table.",
        )

    out = _enrich(df, run_meta)

    try:
        client = bigquery.Client(project=os.getenv("BIGQUERY_PROJECT") or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not initialise BigQuery credentials: {e}")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        time_partitioning=bigquery.TimePartitioning(field="run_timestamp"),
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
    )

    try:
        client.load_table_from_dataframe(out, table_path, job_config=job_config).result()
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=(
                f"BigQuery write failed: {e}. If the destination is a client project, "
                "grant the backend's service account roles/bigquery.dataEditor + jobUser on that dataset."
            ),
        )

    # Refresh the "_latest" pointer view (CREATE OR REPLACE avoids exists-checks).
    view_path = f"{table_path}_latest"
    view_sql = (
        f"CREATE OR REPLACE VIEW `{view_path}` AS "
        f"SELECT * FROM `{table_path}` "
        f"WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM `{table_path}`)"
    )
    try:
        client.query(view_sql).result()
    except Exception as e:
        # The data is already written; a failed view is non-fatal.
        return {"table": table_path, "rows": len(out), "view": None, "view_error": str(e)}

    return {"table": table_path, "rows": len(out), "view": view_path}


def export_to_gcs(df: pd.DataFrame, gcs_uri: str, run_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Write the run as a Parquet object under `gs://bucket/prefix/<method>/<run_id>.parquet`."""
    if not _GCS_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Cloud Storage support is not installed. Run: pip install google-cloud-storage pyarrow",
        )

    gcs_uri = (gcs_uri or "").strip()
    if not gcs_uri.startswith("gs://"):
        raise HTTPException(status_code=400, detail="gcs_uri must start with gs://")

    bucket_name, _, prefix = gcs_uri[len("gs://"):].partition("/")
    if not bucket_name:
        raise HTTPException(status_code=400, detail="gcs_uri must include a bucket name.")
    prefix = prefix.strip("/")
    parts = [prefix] if prefix else []
    parts += [run_meta["method"], f"{run_meta['run_id']}.parquet"]
    blob_path = "/".join(parts)

    buf = io.BytesIO()
    try:
        _enrich(df, run_meta).to_parquet(buf, index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not serialise Parquet (is pyarrow installed?): {e}")
    buf.seek(0)

    try:
        client = storage.Client(project=os.getenv("BIGQUERY_PROJECT") or None)
        blob = client.bucket(bucket_name).blob(blob_path)
        blob.upload_from_file(buf, content_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=(
                f"GCS write failed: {e}. If the bucket is in a client project, grant the "
                "backend's service account roles/storage.objectAdmin on that bucket."
            ),
        )

    return {"uri": f"gs://{bucket_name}/{blob_path}", "rows": len(df)}
