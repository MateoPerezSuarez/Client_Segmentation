"""
RFM Quintile segmentation.
Ported from src/segmentaciones/RFM/script_rfm_quartiles.py
"""
import re

import pandas as pd

# Priority-ordered segment map (first match wins)
SEGMENT_MAP = {
    r"[4-5][4-5][4-5]": "Champions",
    r"[2-3][4-5][4-5]": "Loyal Customers",
    r"[4-5][2-5][4-5]": "Potential Loyalists",
    r"[4-5][2-5][1-3]": "Recent Customers",
    r"[2-3][2-3][4-5]": "Occasional Customers",
    r"[2-4][1-5][1-4]": "Potential Customers",
    r"[2-3][4-5][2-3]": "Economic Loyalists",
    r"[1][4-5][4-5]":   "Risky Customers",
    r"[1-2][1-3][4-5]": "Nearly Lost",
    r"[1-2][4-5][1-3]": "Need Attention",
    r"[3-4][1-3][1-3]": "Average Customers",
    r"[1-3][1-3][1-3]": "Non Active",
    r"[1-3][1-3][1-2]": "Sleeping",
    r"[4-5][1][1-5]":   "New Customers",
    r"[1][1][1]":       "Lost",
}


def _assign_segment(score: str, segment_map: dict) -> str:
    for pattern, label in segment_map.items():
        if re.fullmatch(pattern, score):
            return label
    return "Other"


def run(rfm: pd.DataFrame, custom_segments: list[dict] | None = None) -> pd.DataFrame:
    """
    Input: DataFrame with columns [customer_id, Recency, Frequency, Monetary]
    custom_segments: list of {"pattern": str, "name": str} in priority order.
                     If None, uses built-in SEGMENT_MAP defaults.
    Output: same + [Recency_score, Frequency_score, Monetary_score, RFM_Score, segment]
    """
    segment_map = SEGMENT_MAP
    if custom_segments is not None:
        segment_map = {s["pattern"]: s["name"] for s in custom_segments}

    df = rfm.copy()

    df["Recency_score"] = pd.qcut(df["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    df["Frequency_score"] = pd.qcut(
        df["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    df["Monetary_score"] = pd.qcut(df["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    df["RFM_Score"] = (
        df["Recency_score"].astype(str)
        + df["Frequency_score"].astype(str)
        + df["Monetary_score"].astype(str)
    )

    df["segment"] = df["RFM_Score"].apply(lambda s: _assign_segment(s, segment_map))
    return df


def summarise(df: pd.DataFrame) -> list[dict]:
    total = len(df)
    total_rev = df["Monetary"].sum()
    groups = df.groupby("segment")
    summaries = []
    for label, g in groups:
        summaries.append({
            "label": label,
            "count": len(g),
            "pct_customers": round(len(g) / total * 100, 1),
            "avg_recency": round(g["Recency"].mean(), 1),
            "avg_frequency": round(g["Frequency"].mean(), 1),
            "avg_monetary": round(g["Monetary"].mean(), 1),
            "total_revenue": round(g["Monetary"].sum(), 1),
            "pct_revenue": round(g["Monetary"].sum() / total_rev * 100, 1) if total_rev > 0 else 0,
        })
    summaries.sort(key=lambda x: x["count"], reverse=True)
    return summaries
