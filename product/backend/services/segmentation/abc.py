"""
ABC (Pareto-based) customer segmentation.
A = customers contributing the first a_threshold of cumulative revenue
B = next bucket up to b_threshold
C = rest
"""
import pandas as pd


def run(orders: pd.DataFrame, a_threshold: float = 0.80, b_threshold: float = 0.95) -> pd.DataFrame:
    """
    Input: orders DataFrame with [customer_id, order_total]
    Output: DataFrame with [customer_id, monetary, cumulative_pct, segment]
    """
    customer_rev = (
        orders.groupby("customer_id")["order_total"]
        .sum()
        .reset_index()
        .rename(columns={"order_total": "monetary"})
    )

    customer_rev = customer_rev.sort_values("monetary", ascending=False).reset_index(drop=True)
    total = customer_rev["monetary"].sum()

    if total == 0:
        customer_rev["cumulative_pct"] = 0.0
        customer_rev["segment"] = "C"
        return customer_rev

    customer_rev["cumulative_pct"] = customer_rev["monetary"].cumsum() / total
    customer_rev["prev_cum"] = customer_rev["cumulative_pct"].shift(1, fill_value=0.0)

    customer_rev["segment"] = "C"
    customer_rev.loc[customer_rev["prev_cum"] < a_threshold, "segment"] = "A"
    customer_rev.loc[
        (customer_rev["prev_cum"] >= a_threshold) & (customer_rev["prev_cum"] < b_threshold),
        "segment",
    ] = "B"

    return customer_rev[["customer_id", "monetary", "cumulative_pct", "segment"]].copy()


def summarise(df: pd.DataFrame) -> list[dict]:
    total_customers = len(df)
    total_revenue = df["monetary"].sum()
    summaries = []
    for label, g in df.groupby("segment"):
        summaries.append({
            "label": label,
            "count": len(g),
            "pct_customers": round(len(g) / total_customers * 100, 1),
            "avg_monetary": round(g["monetary"].mean(), 1),
            "total_revenue": round(g["monetary"].sum(), 1),
            "pct_revenue": round(g["monetary"].sum() / total_revenue * 100, 1) if total_revenue > 0 else 0,
        })
    summaries.sort(key=lambda x: x["label"])
    return summaries
