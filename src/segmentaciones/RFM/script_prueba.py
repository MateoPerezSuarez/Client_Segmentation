import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from seleccionador_columnas import DatasetMapper


# ─────────────────────────────────────────────────────────────────
# PALETA VISUAL
# ─────────────────────────────────────────────────────────────────
PALETTE = [
    "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
    "#F4A261", "#6D6875", "#264653", "#A8DADC",
    "#F1FAEE", "#1D3557",
]
BG        = "#0F1117"
CARD_BG   = "#1A1D27"
TEXT_MAIN = "#F1FAEE"
TEXT_SUB  = "#A8DADC"
ACCENT    = "#E63946"


def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=TEXT_SUB, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2E3347")
    if title:
        ax.set_title(title, color=TEXT_MAIN, fontsize=11, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT_SUB, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_SUB, fontsize=9)
    ax.grid(color="#2E3347", linestyle="--", linewidth=0.6, alpha=0.7)


# ─────────────────────────────────────────────────────────────────
# FUNCIÓN: SELECCIÓN AUTOMÁTICA DE K
# ─────────────────────────────────────────────────────────────────

def auto_select_k(rfm_scaled, k_min: int = 2, k_max: int = 10) -> tuple[int, list]:
    """
    Calcula WCSS para k en [1, k_max] y elige automáticamente el k óptimo
    usando la segunda derivada de la curva (punto de máxima curvatura / codo).

    Garantiza k_óptimo >= k_min.

    Returns
    -------
    optimal_k : int
    wcss      : list  (longitud k_max)
    """
    wcss = []
    for k in range(1, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(rfm_scaled)
        wcss.append(km.inertia_)

    # Segunda derivada discreta: mide la "curvatura" en cada punto interior
    wcss_arr   = np.array(wcss)
    deltas     = np.diff(wcss_arr)          # 1ª derivada  (longitud k_max-1)
    curvature  = np.diff(deltas)            # 2ª derivada  (longitud k_max-2)
    # curvature[0]  corresponde a k=2, curvature[1] a k=3, …
    # El codo es donde la curvatura es máxima (mayor cambio de pendiente)
    codo_idx   = int(np.argmax(curvature))  # índice en curvature → k = codo_idx + 2
    optimal_k  = max(k_min, codo_idx + 2)

    return optimal_k, wcss


# ─────────────────────────────────────────────────────────────────
# 1) LECTURA + PRIMERA VISTA
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("LECTURA DE LOS DATOS")
print("="*60)

df = pd.read_excel("data/online+retail/Online Retail.xlsx")

print("\nDatos insertados (primeras 5 filas):")
print(df.head(5))

fig, ax = plt.subplots(figsize=(12, 2.5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.axis("off")
table = ax.table(
    cellText=df.head(5).values,
    colLabels=df.head(5).columns,
    loc="center",
    cellLoc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.4)
for (r, c), cell in table.get_celld().items():
    cell.set_edgecolor("#2E3347")
    cell.set_facecolor(CARD_BG if r > 0 else "#1D3557")
    cell.set_text_props(color=TEXT_MAIN)
plt.tight_layout()
plt.show()

# ─────────────────────────────────────────────────────────────────
# 2) CALIDAD + LIMPIEZA
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("CALIDAD DE DATOS: NULOS Y NEGATIVOS")
print("="*60)

nulls_por_col = df.isnull().sum()
print("\nNulos por columna:\n", nulls_por_col)

num = df.select_dtypes(include="number")
negativos_por_col = (num < 0).sum().sort_values(ascending=False)
print("\nNegativos por columna (numéricas):\n", negativos_por_col)

n_inicial = len(df)
df_sin_nulos = df.dropna().copy()

cols_neg = [c for c in ["Quantity", "UnitPrice"] if c in df_sin_nulos.columns]
mask_neg  = (df_sin_nulos[cols_neg] < 0).any(axis=1)
df_limpio = df_sin_nulos.loc[~mask_neg].copy()

print(f"\nFilas iniciales: {n_inicial:,}  →  tras limpieza: {len(df_limpio):,}")

# ─────────────────────────────────────────────────────────────────
# 3) TOTAL PRICE + MAPPER
# ─────────────────────────────────────────────────────────────────
df_limpio["total_price"] = df_limpio["Quantity"] * df_limpio["UnitPrice"]
df_limpio = df_limpio[df_limpio["total_price"] > 0].copy()

mapper = DatasetMapper()
df_std  = mapper.transform(df_limpio, auto_map_threshold=0.55, verbose=True)

# ─────────────────────────────────────────────────────────────────
# 4) PEDIDOS + RFM
# ─────────────────────────────────────────────────────────────────
df_pedidos = df_std.groupby(
    ["id_usuario", "id_pedido", "fecha_pedido"], as_index=False
).agg({"total_pedido": "sum"})
df_pedidos = df_pedidos[df_pedidos["total_pedido"] > 0].copy()

fecha_ref = df_std["fecha_pedido"].max() + pd.Timedelta(days=1)

rfm = df_pedidos.groupby("id_usuario").agg(
    Recency  = ("fecha_pedido", lambda x: (fecha_ref - x.max()).days),
    Frequency= ("id_pedido",    "nunique"),
    Monetary = ("total_pedido", "sum"),
).reset_index()

print("\nRFM describe:")
print(rfm[["Recency", "Frequency", "Monetary"]].describe())

# ─────────────────────────────────────────────────────────────────
# 5) ESCALADO + SELECCIÓN AUTOMÁTICA DE K
# ─────────────────────────────────────────────────────────────────
scaler     = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])

K_MAX      = 10
optimal_k, wcss = auto_select_k(rfm_scaled, k_min=2, k_max=K_MAX)
k_range    = range(1, K_MAX + 1)

print(f"\n✅ Número de clusters seleccionado automáticamente: k = {optimal_k}")

# ─────────────────────────────────────────────────────────────────
# 6) K-MEANS CON k ÓPTIMO
# ─────────────────────────────────────────────────────────────────
kmeans          = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
rfm["Cluster"]  = kmeans.fit_predict(rfm_scaled)

cluster_profile = rfm.groupby("Cluster").agg(
    Recency  =("Recency",   "mean"),
    Frequency=("Frequency", "mean"),
    Monetary =("Monetary",  "mean"),
    Clientes =("id_usuario","count"),
).round(1)

print("\nPerfiles de clusters:")
print(cluster_profile)

# ─────────────────────────────────────────────────────────────────
# 7) DASHBOARD DE PLOTS EXPLICATIVOS
# ─────────────────────────────────────────────────────────────────
colors = [PALETTE[i % len(PALETTE)] for i in range(optimal_k)]

fig = plt.figure(figsize=(18, 14), facecolor=BG)
fig.suptitle(
    f"Segmentación RFM · k = {optimal_k} clusters (automático)",
    color=TEXT_MAIN, fontsize=16, fontweight="bold", y=0.98
)

gs = gridspec.GridSpec(
    3, 3,
    figure=fig,
    hspace=0.45,
    wspace=0.35,
    left=0.07, right=0.97,
    top=0.93,  bottom=0.06,
)

# ── 7.1  Elbow + codo marcado ────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
style_ax(ax1, "Método del Codo (WCSS)", "k (nº de clusters)", "WCSS")
ax1.plot(k_range, wcss, marker="o", color=TEXT_SUB, linewidth=2, zorder=3)
ax1.axvline(optimal_k, color=ACCENT, linestyle="--", linewidth=1.8, label=f"k = {optimal_k}")
ax1.scatter([optimal_k], [wcss[optimal_k-1]], color=ACCENT, s=100, zorder=5)
ax1.set_xticks(list(k_range))
ax1.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

# ── 7.2  Distribución última compra ─────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
style_ax(ax2, "Última Compra por Cliente", "Fecha", "Clientes")
ultimas = df_pedidos.groupby("id_usuario")["fecha_pedido"].max()
ax2.hist(ultimas, bins=30, color=PALETTE[1], edgecolor=BG, alpha=0.85)
mean_fecha = df_std["fecha_pedido"].max() - pd.to_timedelta(rfm["Recency"].mean(), unit="D")
ax2.axvline(mean_fecha, color=ACCENT, linestyle="--", linewidth=1.5, label="Promedio")
ax2.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

# ── 7.3  Tamaño de clusters ──────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
style_ax(ax3, "Clientes por Cluster", "Cluster", "Nº de Clientes")
counts = rfm["Cluster"].value_counts().sort_index()
bars   = ax3.bar(
    [f"C{i}" for i in counts.index],
    counts.values,
    color=colors,
    edgecolor=BG,
    width=0.6,
)
for bar, val in zip(bars, counts.values):
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + counts.max() * 0.02,
        str(val),
        ha="center", va="bottom", color=TEXT_MAIN, fontsize=9, fontweight="bold",
    )
ax3.set_ylim(0, counts.max() * 1.18)

# ── 7.4  Scatter Recency vs Monetary ────────────────────────────
ax4 = fig.add_subplot(gs[1, 0])
style_ax(ax4, "Recency vs Monetary", "Recency (días)", "Monetary (€)")
for cid in sorted(rfm["Cluster"].unique()):
    sub = rfm[rfm["Cluster"] == cid]
    ax4.scatter(
        sub["Recency"], sub["Monetary"],
        c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
    )
ax4.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

# ── 7.5  Scatter Frequency vs Monetary ──────────────────────────
ax5 = fig.add_subplot(gs[1, 1])
style_ax(ax5, "Frequency vs Monetary", "Frequency (pedidos)", "Monetary (€)")
for cid in sorted(rfm["Cluster"].unique()):
    sub = rfm[rfm["Cluster"] == cid]
    ax5.scatter(
        sub["Frequency"], sub["Monetary"],
        c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
    )
ax5.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

# ── 7.6  Scatter Recency vs Frequency ───────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
style_ax(ax6, "Recency vs Frequency", "Recency (días)", "Frequency (pedidos)")
for cid in sorted(rfm["Cluster"].unique()):
    sub = rfm[rfm["Cluster"] == cid]
    ax6.scatter(
        sub["Recency"], sub["Frequency"],
        c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
    )
ax6.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

# ── 7.7  Radar / Barras agrupadas de perfiles ────────────────────
ax7 = fig.add_subplot(gs[2, :])   # ocupa toda la fila inferior
style_ax(ax7, "Perfil medio de cada Cluster (valores normalizados 0-1)", "Cluster", "Valor normalizado")

metrics      = ["Recency", "Frequency", "Monetary"]
profile_norm = cluster_profile[metrics].copy()
# normalizar cada métrica a [0,1] para hacerlas comparables visualmente
for col in metrics:
    col_min, col_max = profile_norm[col].min(), profile_norm[col].max()
    profile_norm[col] = (
        (profile_norm[col] - col_min) / (col_max - col_min)
        if col_max != col_min else 0.5
    )

n_clusters = len(cluster_profile)
n_metrics  = len(metrics)
x          = np.arange(n_clusters)
bar_w      = 0.22

metric_colors = [PALETTE[5], PALETTE[2], PALETTE[3]]
for j, (metric, mc) in enumerate(zip(metrics, metric_colors)):
    offset = (j - n_metrics / 2 + 0.5) * bar_w
    bars   = ax7.bar(
        x + offset,
        profile_norm[metric].values,
        width=bar_w,
        color=mc,
        alpha=0.85,
        edgecolor=BG,
        label=metric,
    )

ax7.set_xticks(x)
ax7.set_xticklabels([f"Cluster {i}" for i in cluster_profile.index], color=TEXT_MAIN)
ax7.set_ylim(0, 1.25)
ax7.legend(
    fontsize=9, framealpha=0, labelcolor=TEXT_MAIN,
    loc="upper right",
    title="Métrica RFM",
    title_fontproperties={"size": 9},
)

# Anotar valores reales encima de cada grupo
for i, cid in enumerate(cluster_profile.index):
    r = cluster_profile.loc[cid, "Recency"]
    f = cluster_profile.loc[cid, "Frequency"]
    m = cluster_profile.loc[cid, "Monetary"]
    n = int(cluster_profile.loc[cid, "Clientes"])
    ax7.text(
        i, 1.08,
        f"R:{r:.0f}d  F:{f:.1f}  M:€{m:,.0f}\n({n} clientes)",
        ha="center", va="bottom", color=TEXT_MAIN,
        fontsize=8, fontweight="bold",
    )

plt.savefig("rfm_segmentation_dashboard.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.show()

print("\n✅ Dashboard guardado como 'rfm_segmentation_dashboard.png'")
print(f"\n✅ Segmentación completada con k = {optimal_k} clusters (automático, mínimo 2).")