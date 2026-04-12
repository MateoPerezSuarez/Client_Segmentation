"""Aggregate line-level rows to order level, then compute RFM base table."""
import pandas as pd


def aggregate_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by (customer_id, order_id, order_date) summing order_total.
    Excludes rows with order_total <= 0 (used for RFM / ABC).
    """
    group_cols = [c for c in ["customer_id", "order_id", "order_date"] if c in df.columns]
    agg_dict = {}
    if "order_total" in df.columns:
        agg_dict["order_total"] = "sum"
    if "satisfaction" in df.columns:
        agg_dict["satisfaction"] = "mean"

    orders = df.groupby(group_cols, as_index=False).agg(agg_dict)
    if "order_total" in orders.columns:
        orders = orders[orders["order_total"] > 0].copy()
    return orders.reset_index(drop=True)


def aggregate_orders_with_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Same aggregation but keeps negative order_total rows (returns).
    Used by LRFMS when treat_negatives_as_returns=True.
    Only filters out exact zeros.
    """
    group_cols = [c for c in ["customer_id", "order_id", "order_date"] if c in df.columns]
    agg_dict = {}
    if "order_total" in df.columns:
        agg_dict["order_total"] = "sum"
    if "satisfaction" in df.columns:
        agg_dict["satisfaction"] = "mean"

    orders = df.groupby(group_cols, as_index=False).agg(agg_dict)
    if "order_total" in orders.columns:
        orders = orders[orders["order_total"] != 0].copy()
    return orders.reset_index(drop=True)


def compute_rfm(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Recency, Frequency, Monetary from an orders DataFrame.
    Reference date = max(order_date) + 1 day.
    """
    ref_date = orders["order_date"].max() + pd.Timedelta(days=1)
    rfm = orders.groupby("customer_id").agg(
        Recency=("order_date", lambda x: (ref_date - x.max()).days),
        Frequency=("order_id", "nunique"),
        Monetary=("order_total", "sum"),
    ).reset_index()
    return rfm
