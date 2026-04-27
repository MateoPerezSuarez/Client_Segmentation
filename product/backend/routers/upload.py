from fastapi import APIRouter, UploadFile, File

from core import session_store as store
from models.requests import BigQueryRequest
from models.responses import UploadResponse
from services.file_parser import compute_quality, parse_upload
from services import bigquery_connector

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    df = await parse_upload(file)

    sid = store.create_session()
    store.set_value(sid, "raw_df", df)
    store.set_value(sid, "filename", file.filename)

    preview = df.head(10).fillna("").astype(str).to_dict(orient="records")
    quality = compute_quality(df)

    return UploadResponse(
        session_id=sid,
        filename=file.filename,
        rows=len(df),
        columns=list(df.columns),
        preview=preview,
        quality=quality,
    )


@router.post("/bigquery", response_model=UploadResponse)
def upload_bigquery(req: BigQueryRequest):
    df = bigquery_connector.query_bigquery(req.credentials_json, req.table_path)

    sid = store.create_session()
    store.set_value(sid, "raw_df", df)
    store.set_value(sid, "filename", "bigquery")

    preview = df.head(10).fillna("").astype(str).to_dict(orient="records")
    quality = compute_quality(df)

    return UploadResponse(
        session_id=sid,
        filename="BigQuery",
        rows=len(df),
        columns=list(df.columns),
        preview=preview,
        quality=quality,
    )
