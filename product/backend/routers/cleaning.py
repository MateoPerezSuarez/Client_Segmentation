from fastapi import APIRouter

from core import session_store as store
from core.exceptions import MappingNotConfirmed, SessionNotFound
from models.requests import CleanRequest
from models.responses import CleanResponse
from services import cleaner, aggregator

router = APIRouter(prefix="/clean", tags=["clean"])


@router.post("", response_model=CleanResponse)
def clean_data(req: CleanRequest):
    if not store.exists(req.session_id):
        raise SessionNotFound(req.session_id)

    mapped_df = store.get(req.session_id, "mapped_df")
    if mapped_df is None:
        raise MappingNotConfirmed()

    raw_df = store.get(req.session_id, "raw_df")

    clean_df, stats = cleaner.clean(
        mapped_df,
        remove_nulls=req.remove_nulls,
        remove_negatives=req.remove_negatives,
        remove_duplicates=req.remove_duplicates,
        raw_df=raw_df,
    )

    orders_df = aggregator.aggregate_orders(clean_df)

    # Also store a version that keeps negative-total rows (returns) for LRFMS
    orders_with_returns_df = aggregator.aggregate_orders_with_returns(clean_df)

    store.set_value(req.session_id, "clean_df", clean_df)
    store.set_value(req.session_id, "orders_df", orders_df)
    store.set_value(req.session_id, "orders_with_returns_df", orders_with_returns_df)

    return CleanResponse(**stats)
