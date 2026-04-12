"""Shared k-selection utilities used by RFM K-Means and LRFMS."""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


def evaluate_k_range(
    X: np.ndarray, k_min: int = 2, k_max: int = 10
) -> dict:
    """
    Evaluate k from k_min to k_max.
    Returns dict with lists: wcss, silhouette, davies_bouldin, calinski_harabasz, combined.
    """
    wcss, sil, db, ch = [], [], [], []
    ks = list(range(k_min, k_max + 1))

    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        wcss.append(float(km.inertia_))
        sil.append(float(silhouette_score(X, labels)))
        db.append(float(davies_bouldin_score(X, labels)))
        ch.append(float(calinski_harabasz_score(X, labels)))

    # Normalise to [0,1] for combination (higher = better)
    def norm(arr):
        mn, mx = min(arr), max(arr)
        if mx == mn:
            return [1.0] * len(arr)
        return [(v - mn) / (mx - mn) for v in arr]

    sil_n = norm(sil)
    db_n = norm(db)
    db_inv = [1 - v for v in db_n]   # lower DB is better
    ch_n = norm(ch)

    combined = [
        0.4 * s + 0.3 * d + 0.3 * c
        for s, d, c in zip(sil_n, db_inv, ch_n)
    ]

    return {
        "ks": ks,
        "wcss": wcss,
        "silhouette": sil,
        "davies_bouldin": db,
        "calinski_harabasz": ch,
        "combined": combined,
    }


def select_optimal_k(scores: dict, method: str) -> int:
    ks = scores["ks"]
    if method == "silhouette":
        idx = int(np.argmax(scores["silhouette"]))
    elif method == "davies_bouldin":
        idx = int(np.argmin(scores["davies_bouldin"]))
    elif method == "elbow":
        wcss = scores["wcss"]
        diffs = np.diff(wcss)
        second_diffs = np.diff(diffs)
        idx = int(np.argmax(second_diffs)) + 1
    else:  # combined (default)
        idx = int(np.argmax(scores["combined"]))
    return ks[idx]
