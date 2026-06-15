from typing import Any, Optional
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    source_col: Optional[str]
    score: float


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: list[str]
    preview: list[dict]
    quality: dict


class AutoMappingResponse(BaseModel):
    mapping: dict[str, ColumnMapping]
    all_columns: list[str]


class ConfirmMappingResponse(BaseModel):
    ok: bool
    mapped_columns: list[str]


class CleanResponse(BaseModel):
    rows_before: int
    rows_after: int
    removed_nulls: int
    filled_nulls: int = 0
    removed_negatives: int
    removed_duplicates: int
    removed_zero_total: int
    unique_customers: int
    unique_orders: int


class SegmentSummary(BaseModel):
    label: str
    count: int
    pct_customers: float
    avg_recency: Optional[float] = None
    avg_frequency: Optional[float] = None
    avg_monetary: Optional[float] = None
    total_revenue: Optional[float] = None
    pct_revenue: Optional[float] = None
    avg_r_score: Optional[float] = None
    avg_f_score: Optional[float] = None
    avg_m_score: Optional[float] = None


class SegmentationResponse(BaseModel):
    method: str
    total_customers: int
    segments: list[SegmentSummary]
    download_token: str
    extra: Optional[dict[str, Any]] = None  # method-specific extras (k_scores, optimal_k, etc.)


class ExportResponse(BaseModel):
    run_id: str
    bigquery: Optional[dict[str, Any]] = None  # {table, rows, view}
    gcs: Optional[dict[str, Any]] = None        # {uri, rows}
