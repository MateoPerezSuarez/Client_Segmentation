from fastapi import APIRouter

from core import session_store as store
from core.exceptions import RequiredColumnsError, SessionNotFound
from models.requests import AutoMappingRequest, ConfirmMappingRequest
from models.responses import AutoMappingResponse, ColumnMapping, ConfirmMappingResponse
from services import column_mapper as mapper

router = APIRouter(prefix="/mapping", tags=["mapping"])


@router.post("/auto", response_model=AutoMappingResponse)
def auto_map(req: AutoMappingRequest):
    if not store.exists(req.session_id):
        raise SessionNotFound(req.session_id)

    df = store.get(req.session_id, "raw_df")
    mapping, confidence = mapper.auto_map(df)

    response_mapping = {}
    for target in mapper.TARGET_SCHEMA:
        response_mapping[target] = ColumnMapping(
            source_col=mapping.get(target),
            score=round(confidence.get(target, 0.0), 3),
        )

    return AutoMappingResponse(
        mapping=response_mapping,
        all_columns=list(df.columns),
    )


@router.post("/confirm", response_model=ConfirmMappingResponse)
def confirm_mapping(req: ConfirmMappingRequest):
    if not store.exists(req.session_id):
        raise SessionNotFound(req.session_id)

    df = store.get(req.session_id, "raw_df")

    # Validate required columns are present
    required = {"customer_id", "order_id", "order_date"}
    missing = []
    for col in required:
        mapped_source = req.mapping.get(col)
        if not mapped_source:
            missing.append(col)

    # order_total can be derived from qty*price
    has_total = bool(req.mapping.get("order_total"))
    has_qty_price = bool(req.mapping.get("quantity")) and bool(req.mapping.get("unit_price"))
    if not has_total and not has_qty_price:
        missing.append("order_total (or quantity + unit_price)")

    if missing:
        raise RequiredColumnsError(missing)

    mapped_df = mapper.apply_mapping(df, req.mapping)
    store.set_value(req.session_id, "mapped_df", mapped_df)
    store.set_value(req.session_id, "confirmed_mapping", req.mapping)

    return ConfirmMappingResponse(
        ok=True,
        mapped_columns=[k for k, v in req.mapping.items() if v is not None],
    )
