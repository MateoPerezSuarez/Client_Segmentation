"""
LRFMS time-series segmentation.
Based on: Wang, S., Sun, L. & Yu, Y. (2024). Scientific Reports, 14, 17491.

Steps:
1. Divide order history into n_intervals equal-width date bins.
2. For each (customer, interval) compute L, R', F, M, [S].
3. Build a wide feature matrix (customers × intervals*metrics).
4. Scale and K-Means cluster.

S computation (return-rate based):
  - Negative-quantity rows are treated as return events.
  - Return rate = returns / total_transactions in interval.
  - Mapped to 1-10 score using the following scale:
      0%        → 9.0
      1-2%      → 8.5
      3-5%      → 8.0 - rate*10
      6-10%     → 6.5 - rate*5
      11-20%    → 4.0
      >20%      → 2.0

If s_weight == 0.0 the S metric is excluded entirely from the feature matrix.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from utils.clustering import evaluate_k_range, select_optimal_k


def _return_rate_to_score(rate: float) -> float:
    """Map a return rate (0-1) to a satisfaction score (1-10)."""
    pct = rate * 100
    if pct == 0:
        return 9.0
    elif pct <= 2:
        return 8.5
    elif pct <= 5:
        return 8.0 - pct * 0.1 * 10   # 8.0 - rate*10 where rate is fraction → pct/100*10 = pct*0.1
    elif pct <= 10:
        return 6.5 - pct * 0.05 * 100 * 0.01 * 100 * 0.005  # simplify below
    elif pct <= 20:
        return 4.0
    else:
        return 2.0


def _return_rate_to_score(rate: float) -> float:
    """Map a return rate (0–1) to satisfaction score (1–10)."""
    pct = rate * 100
    if pct == 0:
        return 9.0
    elif pct <= 2:
        return 8.5
    elif pct <= 5:
        # 8.0 - (rate * 10)  where rate is 0-1 fraction → 8.0 - pct/100 * 10
        return 8.0 - rate * 10
    elif pct <= 10:
        # 6.5 - (rate * 5)
        return 6.5 - rate * 5
    elif pct <= 20:
        return 4.0
    else:
        return 2.0


def _calc_lrfms_group(
    group: pd.DataFrame,
    interval_end: pd.Timestamp,
    p: int,
    compute_s: bool,
    use_survey_s: bool,
) -> pd.Series:
    """
    Compute LRFMS metrics for one (customer, interval) group.

    group must contain columns: order_date, order_id, order_total, (quantity), (satisfaction)
    Rows with negative order_total are return events and are excluded from L/R/F/M
    but counted for S computation.
    """
    # Split purchases vs returns
    returns = group[group["order_total"] < 0] if "order_total" in group.columns else group.iloc[0:0]
    purchases = group[group["order_total"] >= 0]

    dates = purchases["order_date"].sort_values()

    length = (dates.iloc[-1] - dates.iloc[0]).days if len(dates) > 1 else 0

    p_actual = min(p, len(dates))
    if p_actual > 0:
        last_p = dates.tail(p_actual)
        recency_prime = sum((interval_end - d).days for d in last_p) / p_actual
    else:
        recency_prime = (interval_end - interval_end).days  # 0 if no purchases

    frequency = purchases["order_id"].nunique() if len(purchases) else 0
    monetary = float(purchases["order_total"].sum()) if len(purchases) else 0.0

    result = {
        "L": float(length),
        "R": float(recency_prime),
        "F": float(frequency),
        "M": float(monetary),
    }

    if compute_s:
        if use_survey_s and "satisfaction" in group.columns and group["satisfaction"].notna().any():
            # Use survey satisfaction score directly (assumed already on 1-10 scale)
            result["S"] = float(group["satisfaction"].mean())
        else:
            # Return-rate based S
            total_tx = len(group)
            n_returns = len(returns)
            rate = n_returns / total_tx if total_tx > 0 else 0.0
            result["S"] = _return_rate_to_score(rate)

    return pd.Series(result)


def run(
    orders: pd.DataFrame,
    n_intervals: int = 4,
    p_value: int = 3,
    k_min: int = 2,
    k_max: int = 10,
    method: str = "combined",
    use_satisfaction: bool = False,   # legacy — if True, treated as s_weight=1.0
    s_weight: float = 0.0,
    treat_negatives_as_returns: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Input: orders DataFrame with [customer_id, order_id, order_date, order_total, (quantity), (satisfaction)]
    Output: (labelled_df, extras)
    """
    # Resolve whether to compute S
    effective_s_weight = s_weight if s_weight > 0 else (1.0 if use_satisfaction else 0.0)
    compute_s = effective_s_weight > 0

    # Use survey satisfaction column if it exists
    use_survey_s = "satisfaction" in orders.columns and orders["satisfaction"].notna().any()

    orders = orders.copy()

    # If treat_negatives_as_returns, keep negative rows so S can see them;
    # otherwise filter them out (cleaner already did that for regular flow).
    if not treat_negatives_as_returns:
        orders = orders[orders["order_total"] >= 0].copy()

    date_min = orders[orders["order_total"] >= 0]["order_date"].min()
    date_max = orders[orders["order_total"] >= 0]["order_date"].max()

    bins = pd.date_range(
        start=date_min,
        end=date_max + pd.Timedelta(days=1),
        periods=n_intervals + 1,
    )
    orders["interval"] = pd.cut(
        orders["order_date"], bins=bins, labels=False, include_lowest=True
    )

    metrics = ["L", "R", "F", "M"] + (["S"] if compute_s else [])

    # Compute LRFMS per (customer, interval)
    records = []
    for (cid, iv), grp in orders.groupby(["customer_id", "interval"]):
        if pd.isna(iv):
            continue
        interval_end = bins[int(iv) + 1]
        lrfms = _calc_lrfms_group(grp, interval_end, p_value, compute_s, use_survey_s)
        row = {"customer_id": cid, "interval": int(iv)}
        row.update(lrfms.to_dict())
        records.append(row)

    long_df = pd.DataFrame(records)

    # Pivot to wide format: one row per customer
    wide = long_df.pivot_table(
        index="customer_id", columns="interval", values=metrics, fill_value=0
    )
    wide.columns = [f"{m}_t{t}" for m, t in wide.columns]
    wide = wide.reset_index()

    feature_cols = [c for c in wide.columns if c != "customer_id"]

    # Feature weighting: S columns get s_weight, others get 1.0
    # (paper uses variance-based weights; here we use user-supplied weight for S)
    X_raw = wide[feature_cols].values.astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    if compute_s and effective_s_weight != 1.0:
        s_cols_idx = [i for i, c in enumerate(feature_cols) if c.startswith("S_")]
        other_idx = [i for i, c in enumerate(feature_cols) if not c.startswith("S_")]
        # Rescale S columns by s_weight (relative to other features)
        for idx in s_cols_idx:
            X_scaled[:, idx] *= effective_s_weight

    scores = evaluate_k_range(X_scaled, k_min, k_max)
    optimal_k = select_optimal_k(scores, method)

    km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    wide["segment"] = [f"Cluster {i}" for i in labels]

    # Aggregate avg LRFMS per customer (for summary)
    agg = long_df.groupby("customer_id")[metrics].mean().reset_index()
    agg.columns = ["customer_id"] + [f"avg_{m.lower()}" for m in metrics]
    result = wide[["customer_id", "segment"]].merge(agg, on="customer_id", how="left")

    extras = {
        "optimal_k": optimal_k,
        "k_scores": {k: scores[k] for k in ["ks", "wcss", "silhouette", "davies_bouldin", "calinski_harabasz", "combined"]},
        "n_intervals": n_intervals,
        "metrics": metrics,
        "s_weight": effective_s_weight,
        "s_source": "survey" if (compute_s and use_survey_s) else ("return_rate" if compute_s else "none"),
    }
    return result, extras


def summarise(df: pd.DataFrame) -> list[dict]:
    total = len(df)
    metric_cols = [c for c in df.columns if c.startswith("avg_")]
    summaries = []
    for label, g in df.groupby("segment"):
        entry: dict = {
            "label": label,
            "count": len(g),
            "pct_customers": round(len(g) / total * 100, 1),
        }
        if "avg_m" in df.columns:
            entry["avg_monetary"] = round(g["avg_m"].mean(), 1)
            entry["total_revenue"] = round(g["avg_m"].sum(), 1)
            entry["pct_revenue"] = round(g["avg_m"].sum() / df["avg_m"].sum() * 100, 1) if df["avg_m"].sum() > 0 else 0
        for col in metric_cols:
            entry[col] = round(g[col].mean(), 2)
        summaries.append(entry)
    summaries.sort(key=lambda x: x["count"], reverse=True)
    return summaries
