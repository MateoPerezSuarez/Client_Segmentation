"""Data cleaning logic applied on the standardised DataFrame."""
import pandas as pd


def clean(
    df: pd.DataFrame,
    remove_nulls: bool = True,
    remove_negatives: bool = True,
    remove_duplicates: bool = True,
    raw_df: pd.DataFrame = None,
) -> tuple[pd.DataFrame, dict]:
    rows_before = len(df)
    removed_nulls = 0
    removed_negatives = 0
    removed_duplicates = 0
    removed_zero_total = 0

    # Deduplicate first, using original columns to avoid false positives.
    # Mapped df drops product-level columns (StockCode etc.), so two different
    # products in the same invoice with the same price/qty would look identical.
    # Using raw_df keeps all original columns for an accurate duplicate check.
    if remove_duplicates:
        before = len(df)
        if raw_df is not None and len(raw_df) == len(df):
            keep = ~raw_df.duplicated()
            df = df[keep.values]
        else:
            df = df.drop_duplicates()
        removed_duplicates = before - len(df)

    if remove_nulls:
        before = len(df)
        df = df.dropna(subset=[c for c in ["customer_id", "order_id", "order_date", "order_total"] if c in df.columns])
        removed_nulls = before - len(df)

    if remove_negatives:
        before = len(df)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            mask_neg = (df[num_cols] < 0).any(axis=1)
            df = df[~mask_neg]
        removed_negatives = before - len(df)

    # Remove zero/negative order_total.
    # When remove_negatives=False (returns mode) only strip exact zeros so that
    # negative-total rows are preserved for LRFMS S computation.
    if "order_total" in df.columns:
        before = len(df)
        if remove_negatives:
            df = df[df["order_total"] > 0]
        else:
            df = df[df["order_total"] != 0]
        removed_zero_total = before - len(df)

    unique_customers = df["customer_id"].nunique() if "customer_id" in df.columns else 0
    unique_orders = df["order_id"].nunique() if "order_id" in df.columns else 0

    stats = {
        "rows_before": rows_before,
        "rows_after": len(df),
        "removed_nulls": removed_nulls,
        "removed_negatives": removed_negatives,
        "removed_duplicates": removed_duplicates,
        "removed_zero_total": removed_zero_total,
        "unique_customers": unique_customers,
        "unique_orders": unique_orders,
    }
    return df.reset_index(drop=True), stats
