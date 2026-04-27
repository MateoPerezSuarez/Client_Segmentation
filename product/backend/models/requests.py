from typing import Optional
from pydantic import BaseModel


class BigQueryRequest(BaseModel):
    credentials_json: str   # full content of service account key JSON
    table_path: str         # BigQuery table path, e.g. project.dataset.table


class AutoMappingRequest(BaseModel):
    session_id: str


class ConfirmMappingRequest(BaseModel):
    session_id: str
    mapping: dict[str, Optional[str]]  # target_col -> source_col (None = not mapped)


class CleanRequest(BaseModel):
    session_id: str
    remove_nulls: bool = True
    remove_negatives: bool = True
    remove_duplicates: bool = True


class SegmentRule(BaseModel):
    pattern: str   # regex applied to RFM_Score, e.g. "[4-5][4-5][4-5]"
    name: str      # label for this segment


class RFMQuintilesRequest(BaseModel):
    session_id: str
    custom_segments: Optional[list[SegmentRule]] = None  # None = use built-in defaults


class RFMKMeansPreviewRequest(BaseModel):
    session_id: str
    k_min: int = 2
    k_max: int = 10


class RFMKMeansRequest(BaseModel):
    session_id: str
    algorithm: str = "kmeans"        # kmeans | dbscan
    k_min: int = 2
    k_max: int = 10
    selection_method: str = "combined"  # silhouette | elbow | davies_bouldin | combined
    k_override: Optional[int] = None    # manually fix k after seeing elbow
    eps: float = 0.5                 # DBSCAN: neighbourhood radius
    min_samples: int = 5             # DBSCAN: core point threshold


class ABCRequest(BaseModel):
    session_id: str
    a_threshold: float = 0.80
    b_threshold: float = 0.95


class LRFMSRequest(BaseModel):
    session_id: str
    n_intervals: int = 4
    p_value: int = 3
    k_min: int = 2
    k_max: int = 10
    selection_method: str = "combined"
    use_satisfaction: bool = False          # legacy — kept for compatibility
    s_weight: float = 0.0                   # 0.0 = exclude S; >0 = include with this weight
    treat_negatives_as_returns: bool = True # negative quantity rows → return events for S
