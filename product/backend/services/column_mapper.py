"""
Column auto-detection service.
Ported from src/segmentaciones/RFM/seleccionador_columnas.py with extensions
for quantity, unit_price and satisfaction columns.
"""
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional

import pandas as pd


TARGET_SCHEMA = {
    "customer_id": {
        "type": "string",
        "aliases": [
            "user_id", "usuario", "cliente", "customer_id", "client_id",
            "user", "cliente_id", "id_cliente", "userid", "customerid",
            "clientid", "id_usuario",
        ],
    },
    "order_id": {
        "type": "string",
        "aliases": [
            "order_id", "pedido", "orden", "order", "num_pedido",
            "numero_pedido", "id_orden", "orderid", "order_number",
            "numero_orden", "invoice", "invoiceno", "id_pedido",
        ],
    },
    "order_date": {
        "type": "date",
        "aliases": [
            "fecha", "date", "created_at", "order_date", "fecha_orden",
            "timestamp", "fecha_creacion", "purchase_date", "fecha_compra",
            "order_timestamp", "created_date", "invoicedate", "fecha_pedido",
        ],
    },
    "order_total": {
        "type": "number",
        "aliases": [
            "total", "amount", "importe", "total_price", "totalprice",
            "monto", "valor", "total_order", "importe_total", "total_amount",
            "order_total", "order_amount", "invoice_total", "grand_total",
            "precio_total", "price", "precio", "subtotal", "total_pedido",
        ],
    },
    "quantity": {
        "type": "number",
        "aliases": [
            "qty", "quantity", "cantidad", "units", "items", "count",
            "num_items", "item_count",
        ],
    },
    "unit_price": {
        "type": "number",
        "aliases": [
            "unit_price", "unitprice", "price", "precio_unitario",
            "precio_unit", "price_per_unit", "unit_cost",
        ],
    },
    "satisfaction": {
        "type": "number",
        "aliases": [
            "satisfaction", "rating", "score", "review", "stars",
            "puntuacion", "valoracion", "nota",
        ],
    },
}

REQUIRED_COLS = {"customer_id", "order_id", "order_date"}


def _normalize(text: str) -> str:
    return text.lower().replace("_", "").replace("-", "").replace(" ", "")


def _similarity(a: str, b: str) -> float:
    a, b = _normalize(a), _normalize(b)
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.85
    return SequenceMatcher(None, a, b).ratio()


def _best_name_score(col: str, target: str, aliases: list[str]) -> float:
    score = _similarity(col, target)
    for alias in aliases:
        score = max(score, _similarity(col, alias))
    return score


def _is_date(value) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, (pd.Timestamp, datetime)):
        return True
    try:
        pd.to_datetime(value)
        return True
    except Exception:
        return False


def _type_score(series: pd.Series, expected: str) -> float:
    sample = series.dropna().head(20)
    if len(sample) == 0:
        return 0.5
    hits = 0
    for v in sample:
        if expected == "number":
            try:
                float(v)
                hits += 1
            except (ValueError, TypeError):
                pass
        elif expected == "date":
            if _is_date(v):
                hits += 1
        elif expected == "string":
            hits += 1  # anything can be string
    return hits / len(sample)


def auto_map(df: pd.DataFrame, threshold: float = 0.5) -> tuple[dict, dict]:
    """
    Returns:
        mapping        — {target_col: source_col}
        confidence     — {target_col: score}
    """
    all_scores: dict[str, dict[str, float]] = {}

    for target, cfg in TARGET_SCHEMA.items():
        all_scores[target] = {}
        for col in df.columns:
            name_sc = _best_name_score(col, target, cfg["aliases"])
            type_sc = _type_score(df[col], cfg["type"])
            final = name_sc * 0.7 + type_sc * 0.3
            if final >= threshold:
                all_scores[target][col] = final

    candidates = [
        (score, target, col)
        for target, scores in all_scores.items()
        for col, score in scores.items()
    ]
    candidates.sort(reverse=True, key=lambda x: x[0])

    mapping: dict[str, str] = {}
    confidence: dict[str, float] = {}
    used: set[str] = set()

    for score, target, col in candidates:
        if col not in used and target not in mapping:
            mapping[target] = col
            confidence[target] = score
            used.add(col)

    return mapping, confidence


def apply_mapping(df: pd.DataFrame, mapping: dict[str, Optional[str]]) -> pd.DataFrame:
    """
    Rename and cast columns according to confirmed mapping.
    If order_total is None but quantity + unit_price are mapped, compute total = qty * price.
    """
    result = pd.DataFrame(index=df.index)

    for target, source in mapping.items():
        if source is None:
            continue
        if source not in df.columns:
            continue
        cfg = TARGET_SCHEMA.get(target, {})
        col = df[source].copy()
        if cfg.get("type") == "number":
            col = pd.to_numeric(col, errors="coerce")
        elif cfg.get("type") == "date":
            col = pd.to_datetime(col, errors="coerce")
        else:
            # Preserve NaN so null-removal in the cleaner can catch them.
            # astype(str) would convert NaN → the literal string "nan".
            col = col.where(col.isna(), col.astype(str))
        result[target] = col

    # Derive order_total from qty * price if not directly mapped
    if "order_total" not in result.columns:
        if "quantity" in result.columns and "unit_price" in result.columns:
            result["order_total"] = result["quantity"] * result["unit_price"]

    return result
