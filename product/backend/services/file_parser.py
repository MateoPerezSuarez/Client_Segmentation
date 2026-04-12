"""Parse uploaded CSV or Excel files into a pandas DataFrame."""
import io
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


async def parse_upload(file: UploadFile) -> pd.DataFrame:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Upload a CSV or Excel file."
        )

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum 50 MB.")

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    return df


def compute_quality(df: pd.DataFrame) -> dict:
    null_rows = int(df.isnull().any(axis=1).sum())
    num_cols = df.select_dtypes(include="number")
    negative_rows = int((num_cols < 0).any(axis=1).sum()) if not num_cols.empty else 0
    duplicate_rows = int(df.duplicated().sum())
    null_per_column = {col: int(df[col].isnull().sum()) for col in df.columns}
    negative_per_column = {
        col: int((df[col] < 0).sum())
        for col in df.select_dtypes(include="number").columns
    }
    return {
        "null_rows": null_rows,
        "negative_rows": negative_rows,
        "duplicate_rows": duplicate_rows,
        "null_per_column": null_per_column,
        "negative_per_column": negative_per_column,
        "total_rows": len(df),
    }
