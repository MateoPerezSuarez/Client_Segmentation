"""
RFM clustering segmentation — K-Means and DBSCAN.
Features are always StandardScaler-normalised before clustering.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from utils.clustering import evaluate_k_range, select_optimal_k


def _scale(rfm: pd.DataFrame) -> np.ndarray:
    return StandardScaler().fit_transform(rfm[["Recency", "Frequency", "Monetary"]].values)


def run(
    rfm: pd.DataFrame,
    k_min: int = 2,
    k_max: int = 10,
    method: str = "combined",
    k_override: int = None,
    algorithm: str = "kmeans",
    eps: float = 0.5,
    min_samples: int = 5,
) -> tuple[pd.DataFrame, dict]:
    X = _scale(rfm)

    if algorithm == "dbscan":
        db = DBSCAN(eps=eps, min_samples=min_samples)
        labels = db.fit_predict(X)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        df = rfm.copy()
        df["segment"] = [f"Cluster {l}" if l >= 0 else "Noise" for l in labels]

        extras = {
            "algorithm": "dbscan",
            "optimal_k": n_clusters,
            "n_clusters": n_clusters,
            "noise_points": int((labels == -1).sum()),
        }
        return df, extras

    # K-Means
    scores = evaluate_k_range(X, k_min, k_max)

    if k_override is not None and k_min <= k_override <= k_max:
        optimal_k = k_override
    else:
        optimal_k = select_optimal_k(scores, method)

    km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    df = rfm.copy()
    df["segment"] = [f"Cluster {i}" for i in labels]

    extras = {
        "algorithm": "kmeans",
        "optimal_k": optimal_k,
        "k_scores": {k: scores[k] for k in ["ks", "wcss", "silhouette", "davies_bouldin", "calinski_harabasz", "combined"]},
    }
    return df, extras


def preview_k(rfm: pd.DataFrame, k_min: int, k_max: int) -> dict:
    """Return k-evaluation scores without running final clustering."""
    X = _scale(rfm)
    return evaluate_k_range(X, k_min, k_max)


def summarise(df: pd.DataFrame) -> list[dict]:
    total = len(df)
    total_rev = df["Monetary"].sum()
    summaries = []
    for label, g in df.groupby("segment"):
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
