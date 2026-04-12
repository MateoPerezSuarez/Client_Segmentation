import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core import session_store as store
from core.exceptions import DataNotCleaned, SessionNotFound
from models.requests import ABCRequest, LRFMSRequest, RFMKMeansPreviewRequest, RFMKMeansRequest, RFMQuintilesRequest
from models.responses import SegmentationResponse, SegmentSummary
from services.aggregator import compute_rfm
from services.segmentation import abc, lrfms, rfm_kmeans, rfm_quintiles
from utils.export import to_csv_bytes

router = APIRouter(prefix="/segment", tags=["segmentation"])
_executor = ThreadPoolExecutor(max_workers=4)


def _require_orders(session_id: str):
    if not store.exists(session_id):
        raise SessionNotFound(session_id)
    orders = store.get(session_id, "orders_df")
    if orders is None:
        raise DataNotCleaned()
    return orders


def _save_result(session_id: str, result_df) -> str:
    token = str(uuid.uuid4())
    store.set_value(session_id, f"download_{token}", result_df)
    return token


@router.post("/rfm-quintiles", response_model=SegmentationResponse)
async def segment_rfm_quintiles(req: RFMQuintilesRequest):
    orders = _require_orders(req.session_id)

    custom = [s.model_dump() for s in req.custom_segments] if req.custom_segments else None

    loop = asyncio.get_event_loop()
    rfm = await loop.run_in_executor(_executor, compute_rfm, orders)
    result = await loop.run_in_executor(_executor, rfm_quintiles.run, rfm, custom)

    summaries = rfm_quintiles.summarise(result)
    token = _save_result(req.session_id, result)

    return SegmentationResponse(
        method="rfm_quintiles",
        total_customers=len(result),
        segments=[SegmentSummary(**s) for s in summaries],
        download_token=token,
    )


@router.post("/rfm-kmeans/preview")
async def preview_rfm_k_scores(req: RFMKMeansPreviewRequest):
    """Evaluate k range and return scores so the frontend can show the elbow chart."""
    orders = _require_orders(req.session_id)
    loop = asyncio.get_event_loop()
    rfm = await loop.run_in_executor(_executor, compute_rfm, orders)
    scores = await loop.run_in_executor(_executor, rfm_kmeans.preview_k, rfm, req.k_min, req.k_max)
    return {"k_scores": scores}


@router.post("/rfm-kmeans", response_model=SegmentationResponse)
async def segment_rfm_kmeans(req: RFMKMeansRequest):
    orders = _require_orders(req.session_id)

    loop = asyncio.get_event_loop()
    rfm = await loop.run_in_executor(_executor, compute_rfm, orders)
    result, extras = await loop.run_in_executor(
        _executor,
        lambda: rfm_kmeans.run(
            rfm,
            k_min=req.k_min,
            k_max=req.k_max,
            method=req.selection_method,
            k_override=req.k_override,
            algorithm=req.algorithm,
            eps=req.eps,
            min_samples=req.min_samples,
        ),
    )

    summaries = rfm_kmeans.summarise(result)
    token = _save_result(req.session_id, result)

    return SegmentationResponse(
        method="rfm_kmeans",
        total_customers=len(result),
        segments=[SegmentSummary(**s) for s in summaries],
        download_token=token,
        extra=extras,
    )


@router.post("/abc", response_model=SegmentationResponse)
async def segment_abc(req: ABCRequest):
    orders = _require_orders(req.session_id)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor, abc.run, orders, req.a_threshold, req.b_threshold
    )

    summaries = abc.summarise(result)
    token = _save_result(req.session_id, result)

    return SegmentationResponse(
        method="abc",
        total_customers=len(result),
        segments=[SegmentSummary(**s) for s in summaries],
        download_token=token,
    )


@router.post("/lrfms", response_model=SegmentationResponse)
async def segment_lrfms(req: LRFMSRequest):
    if not store.exists(req.session_id):
        raise SessionNotFound(req.session_id)
    # Use orders_with_returns when requested so negative rows are visible to LRFMS
    if req.treat_negatives_as_returns:
        orders = store.get(req.session_id, "orders_with_returns_df")
        if orders is None:
            orders = _require_orders(req.session_id)   # fallback
    else:
        orders = _require_orders(req.session_id)

    loop = asyncio.get_event_loop()
    result, extras = await loop.run_in_executor(
        _executor,
        lambda: lrfms.run(
            orders,
            n_intervals=req.n_intervals,
            p_value=req.p_value,
            k_min=req.k_min,
            k_max=req.k_max,
            method=req.selection_method,
            use_satisfaction=req.use_satisfaction,
            s_weight=req.s_weight,
            treat_negatives_as_returns=req.treat_negatives_as_returns,
        ),
    )

    summaries = lrfms.summarise(result)
    token = _save_result(req.session_id, result)

    return SegmentationResponse(
        method="lrfms",
        total_customers=len(result),
        segments=[SegmentSummary(**s) for s in summaries],
        download_token=token,
        extra=extras,
    )


@router.post("/rename/{session_id}/{token}")
def rename_segments(session_id: str, token: str, renames: dict[str, str]):
    """Apply a {old_label: new_label} map to the stored result DataFrame."""
    if not store.exists(session_id):
        raise SessionNotFound(session_id)
    result_df = store.get(session_id, f"download_{token}")
    if result_df is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Token not found or expired.")
    result_df = result_df.copy()
    result_df["segment"] = result_df["segment"].map(lambda s: renames.get(s, s))
    store.set_value(session_id, f"download_{token}", result_df)
    return {"ok": True, "renames": renames}


@router.get("/dashboard/{session_id}/{token}")
def get_dashboard_data(session_id: str, token: str):
    """Return chart-ready data for the frontend dashboard."""
    if not store.exists(session_id):
        raise SessionNotFound(session_id)

    result_df = store.get(session_id, f"download_{token}")
    if result_df is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Token not found or expired.")

    df = result_df.copy()

    # Normalise column names to lowercase for consistent lookup
    df.columns = [c.lower() for c in df.columns]

    # Build scatter data (max 2 000 samples, keep proportional per segment)
    has_rfm = "recency" in df.columns and "frequency" in df.columns and "monetary" in df.columns
    has_monetary = "monetary" in df.columns  # abc uses "monetary" directly

    if has_rfm:
        scatter_cols = ["customer_id", "recency", "frequency", "monetary", "segment"]
    elif has_monetary:
        scatter_cols = ["customer_id", "monetary", "segment"]
    else:
        # LRFMS — use avg_ columns
        avg_cols = [c for c in df.columns if c.startswith("avg_")]
        scatter_cols = ["customer_id", "segment"] + avg_cols[:4]

    scatter_cols = [c for c in scatter_cols if c in df.columns]
    sample = df[scatter_cols].copy()
    if len(sample) > 2000:
        sample = sample.groupby("segment", group_keys=False).apply(
            lambda g: g.sample(min(len(g), max(1, int(2000 * len(g) / len(df)))))
        )
    scatter = sample.fillna(0).to_dict(orient="records")

    # Top-10 customers per segment by monetary value
    monetary_col = "monetary" if "monetary" in df.columns else (
        "avg_m" if "avg_m" in df.columns else None
    )
    top_customers = []
    if monetary_col:
        for seg, grp in df.groupby("segment"):
            top = grp.nlargest(10, monetary_col)[scatter_cols].fillna(0).to_dict(orient="records")
            for row in top:
                row["segment"] = seg
            top_customers.extend(top)

    # ABC Pareto curve
    is_abc = "cumulative_pct" in df.columns
    pareto_curve = []
    abc_thresholds = None

    if is_abc:
        df_sorted = df.sort_values("monetary", ascending=False).reset_index(drop=True)
        n = len(df_sorted)
        step = max(1, n // 300)
        indices = list(range(0, n, step))
        if n - 1 not in indices:
            indices.append(n - 1)
        for idx in indices:
            row = df_sorted.iloc[idx]
            pareto_curve.append({
                "x": round((idx + 1) / n * 100, 2),
                "y": round(float(row["cumulative_pct"]) * 100, 2),
                "segment": row["segment"],
            })
        seg_a = df_sorted[df_sorted["segment"] == "A"]
        seg_b = df_sorted[df_sorted["segment"] == "B"]
        a_x = round(len(seg_a) / n * 100, 1)
        b_x = round((len(seg_a) + len(seg_b)) / n * 100, 1)
        a_y = round(float(seg_a["cumulative_pct"].max()) * 100, 1) if len(seg_a) else 0.0
        b_y = round(float(seg_b["cumulative_pct"].max()) * 100, 1) if len(seg_b) else a_y
        abc_thresholds = {"a_x": a_x, "b_x": b_x, "a_y": a_y, "b_y": b_y}

    # Per-cluster distribution stats (R/F/M mean, std, min, max)
    cluster_stats = []
    if has_rfm:
        for seg, grp in df.groupby("segment"):
            entry = {"segment": seg}
            for metric in ["recency", "frequency", "monetary"]:
                entry[metric] = {
                    "mean": round(float(grp[metric].mean()), 1),
                    "std":  round(float(grp[metric].std()),  1),
                    "min":  round(float(grp[metric].min()),  1),
                    "max":  round(float(grp[metric].max()),  1),
                }
            cluster_stats.append(entry)
        cluster_stats.sort(key=lambda x: x["segment"])

    return {
        "has_rfm": has_rfm,
        "is_abc": is_abc,
        "pareto_curve": pareto_curve,
        "abc_thresholds": abc_thresholds,
        "scatter": scatter,
        "top_customers": top_customers,
        "cluster_stats": cluster_stats,
    }


@router.get("/download/{session_id}/{token}")
def download_result(session_id: str, token: str):
    if not store.exists(session_id):
        raise SessionNotFound(session_id)

    result_df = store.get(session_id, f"download_{token}")
    if result_df is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Download token not found or expired.")

    csv_bytes = to_csv_bytes(result_df)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=segmentation.csv"},
    )
