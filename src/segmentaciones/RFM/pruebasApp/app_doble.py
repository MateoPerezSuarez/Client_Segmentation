import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px

try:
    import squarify
    SQUARIFY_AVAILABLE = True
except ImportError:
    SQUARIFY_AVAILABLE = False
    st.warning("⚠️ squarify no está instalado. Instálalo con: pip install squarify")

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RFM Segmentation Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# ─────────────────────────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main {
        background-color: #0F1117;
    }
    .stButton>button {
        background: linear-gradient(135deg, #E63946 0%, #A8324B 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(230, 57, 70, 0.5);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #E63946;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #A8DADC;
        font-weight: 500;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1 {
        color: #F1FAEE;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: #E63946;
        font-weight: 700;
    }
    .stSelectbox label, .stFileUploader label {
        color: #A8DADC !important;
        font-weight: 600;
    }
    .metric-box {
        background-color: #1A1D27;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #E63946;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────

def style_ax(ax, title="", xlabel="", ylabel=""):
    """Estiliza un eje de matplotlib"""
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


def calculate_cluster_metrics(rfm_scaled, labels):
    """Calcula métricas de validación de clusters"""
    n_clusters = len(np.unique(labels))
    
    if n_clusters < 2:
        return None
    
    metrics = {
        'silhouette': silhouette_score(rfm_scaled, labels),
        'davies_bouldin': davies_bouldin_score(rfm_scaled, labels),
        'calinski_harabasz': calinski_harabasz_score(rfm_scaled, labels)
    }
    
    return metrics


def evaluate_k_range(rfm_scaled, k_min=2, k_max=10):
    """Evalúa diferentes valores de k y retorna métricas"""
    results = []
    
    for k in range(k_min, k_max + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(rfm_scaled)
        
        metrics = calculate_cluster_metrics(rfm_scaled, labels)
        
        results.append({
            'k': k,
            'inertia': kmeans.inertia_,
            'silhouette': metrics['silhouette'],
            'davies_bouldin': metrics['davies_bouldin'],
            'calinski_harabasz': metrics['calinski_harabasz']
        })
    
    return pd.DataFrame(results)


def auto_select_k(rfm_scaled, k_min=2, k_max=10):
    """Selecciona automáticamente el k óptimo"""
    results_df = evaluate_k_range(rfm_scaled, k_min, k_max)
    
    # Normalizar métricas
    results_df['silhouette_norm'] = (results_df['silhouette'] - results_df['silhouette'].min()) / \
                                     (results_df['silhouette'].max() - results_df['silhouette'].min())
    
    results_df['davies_bouldin_norm'] = 1 - ((results_df['davies_bouldin'] - results_df['davies_bouldin'].min()) / \
                                              (results_df['davies_bouldin'].max() - results_df['davies_bouldin'].min()))
    
    results_df['calinski_harabasz_norm'] = (results_df['calinski_harabasz'] - results_df['calinski_harabasz'].min()) / \
                                            (results_df['calinski_harabasz'].max() - results_df['calinski_harabasz'].min())
    
    # Score combinado
    results_df['combined_score'] = (
        results_df['silhouette_norm'] * 0.4 +
        results_df['davies_bouldin_norm'] * 0.3 +
        results_df['calinski_harabasz_norm'] * 0.3
    )
    
    optimal_k = results_df.loc[results_df['combined_score'].idxmax(), 'k']
    
    return int(optimal_k), results_df


def rfm_quantiles(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Segmentación por cuartiles"""
    dfq = dataframe.copy()
    dfq["Recency_score"] = pd.qcut(dfq["Recency"], 5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
    dfq["Frequency_score"] = pd.qcut(dfq["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    dfq["Monetary_score"] = pd.qcut(dfq["Monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    dfq["RFM_Score"] = (
        dfq["Recency_score"].astype(str)
        + dfq["Frequency_score"].astype(str)
        + dfq["Monetary_score"].astype(str)
    )
    return dfq


def apply_segment_mapping(rfm, segment_map, default_name="Other / Unassigned"):
    rfm_copy = rfm.copy()

    # segment_map: dict {pattern: name} en el orden que quieres aplicar
    seg = pd.Series([default_name] * len(rfm_copy), index=rfm_copy.index)

    for pattern, name in segment_map.items():
        mask = rfm_copy["RFM_Score"].str.match(pattern, na=False)
        seg[mask] = name

    rfm_copy["Segmento"] = seg
    return rfm_copy



def create_validation_dashboard(results_df):
    """Crea dashboard de validación de clusters"""
    fig = plt.figure(figsize=(18, 10), facecolor=BG)
    fig.suptitle(
        "Validación de Clusters - Métricas de Calidad",
        color=TEXT_MAIN, fontsize=16, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(
        2, 3,
        figure=fig,
        hspace=0.35,
        wspace=0.30,
        left=0.07, right=0.97,
        top=0.93, bottom=0.06,
    )

    # Elbow Method (WCSS)
    ax1 = fig.add_subplot(gs[0, 0])
    style_ax(ax1, "Método del Codo (WCSS)", "k (nº de clusters)", "WCSS")
    ax1.plot(results_df['k'], results_df['inertia'], marker="o", color=PALETTE[1], linewidth=2)
    
    # Silhouette Score
    ax2 = fig.add_subplot(gs[0, 1])
    style_ax(ax2, "Silhouette Score (↑ mejor)", "k (nº de clusters)", "Score")
    ax2.plot(results_df['k'], results_df['silhouette'], marker="o", color=PALETTE[2], linewidth=2)
    ax2.axhline(y=0.5, color=ACCENT, linestyle="--", linewidth=1, alpha=0.5, label="Umbral bueno (0.5)")
    best_silhouette_k = results_df.loc[results_df['silhouette'].idxmax(), 'k']
    ax2.axvline(x=best_silhouette_k, color=ACCENT, linestyle=":", linewidth=1.5, alpha=0.7)
    ax2.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN)
    
    # Davies-Bouldin Index
    ax3 = fig.add_subplot(gs[0, 2])
    style_ax(ax3, "Davies-Bouldin Index (↓ mejor)", "k (nº de clusters)", "Score")
    ax3.plot(results_df['k'], results_df['davies_bouldin'], marker="o", color=PALETTE[3], linewidth=2)
    best_db_k = results_df.loc[results_df['davies_bouldin'].idxmin(), 'k']
    ax3.axvline(x=best_db_k, color=ACCENT, linestyle=":", linewidth=1.5, alpha=0.7)
    
    # Calinski-Harabasz Score
    ax4 = fig.add_subplot(gs[1, 0])
    style_ax(ax4, "Calinski-Harabasz Score (↑ mejor)", "k (nº de clusters)", "Score")
    ax4.plot(results_df['k'], results_df['calinski_harabasz'], marker="o", color=PALETTE[4], linewidth=2)
    best_ch_k = results_df.loc[results_df['calinski_harabasz'].idxmax(), 'k']
    ax4.axvline(x=best_ch_k, color=ACCENT, linestyle=":", linewidth=1.5, alpha=0.7)
    
    # Combined Score
    ax5 = fig.add_subplot(gs[1, 1])
    style_ax(ax5, "Score Combinado (↑ mejor)", "k (nº de clusters)", "Score")
    ax5.plot(results_df['k'], results_df['combined_score'], marker="o", color=ACCENT, linewidth=2.5)
    optimal_k = results_df.loc[results_df['combined_score'].idxmax(), 'k']
    ax5.axvline(x=optimal_k, color=PALETTE[0], linestyle="--", linewidth=2, label=f"k óptimo = {int(optimal_k)}")
    ax5.scatter([optimal_k], [results_df.loc[results_df['combined_score'].idxmax(), 'combined_score']], 
                color=PALETTE[0], s=150, zorder=5, edgecolors=TEXT_MAIN, linewidth=2)
    ax5.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)
    
    # Tabla de métricas
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    
    summary_data = [
        ['Métrica', 'Mejor k', 'Valor'],
        ['Silhouette', f'{int(best_silhouette_k)}', f'{results_df.loc[results_df["silhouette"].idxmax(), "silhouette"]:.3f}'],
        ['Davies-Bouldin', f'{int(best_db_k)}', f'{results_df.loc[results_df["davies_bouldin"].idxmin(), "davies_bouldin"]:.3f}'],
        ['Calinski-Harabasz', f'{int(best_ch_k)}', f'{results_df.loc[results_df["calinski_harabasz"].idxmax(), "calinski_harabasz"]:.1f}'],
        ['Score Combinado', f'{int(optimal_k)}', f'{results_df.loc[results_df["combined_score"].idxmax(), "combined_score"]:.3f}']
    ]
    
    table = ax6.table(cellText=summary_data, cellLoc='left', loc='center',
                      colWidths=[0.5, 0.25, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    for i in range(len(summary_data)):
        for j in range(3):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor(ACCENT)
                cell.set_text_props(weight='bold', color=TEXT_MAIN)
            else:
                cell.set_facecolor(CARD_BG)
                cell.set_text_props(color=TEXT_MAIN)
            cell.set_edgecolor("#2E3347")
    
    return fig


def create_segmentation_dashboard(rfm, method="kmeans"):
    """Crea el dashboard de visualización de segmentación con treemap"""
    
    if method == "kmeans":
        n_segments = rfm["Cluster"].nunique()
        segment_col = "Cluster"
        title_suffix = f"K-Means · k = {n_segments} clusters"
    else:
        n_segments = rfm["Segmento"].nunique()
        segment_col = "Segmento"
        title_suffix = "Segmentación por Cuartiles"
    
    colors = [PALETTE[i % len(PALETTE)] for i in range(n_segments)]
    
    fig = plt.figure(figsize=(20, 18), facecolor=BG)
    fig.suptitle(
        f"Segmentación RFM · {title_suffix}",
        color=TEXT_MAIN, fontsize=16, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(
        4, 3,
        figure=fig,
        hspace=0.45,
        wspace=0.35,
        left=0.07, right=0.97,
        top=0.93, bottom=0.06,
    )

    # Distribución de Recency
    ax1 = fig.add_subplot(gs[0, 0])
    style_ax(ax1, "Distribución de Recency", "Días desde última compra", "Clientes")
    ax1.hist(rfm["Recency"], bins=30, color=PALETTE[1], edgecolor=BG, alpha=0.85)
    mean_recency = rfm["Recency"].mean()
    ax1.axvline(mean_recency, color=ACCENT, linestyle="--", linewidth=1.5, label=f"Media: {mean_recency:.0f} días")
    ax1.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

    # Distribución de Frequency
    ax2 = fig.add_subplot(gs[0, 1])
    style_ax(ax2, "Distribución de Frequency", "Número de pedidos", "Clientes")
    ax2.hist(rfm["Frequency"], bins=30, color=PALETTE[2], edgecolor=BG, alpha=0.85)
    mean_freq = rfm["Frequency"].mean()
    ax2.axvline(mean_freq, color=ACCENT, linestyle="--", linewidth=1.5, label=f"Media: {mean_freq:.1f}")
    ax2.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

    # Distribución de Monetary
    ax3 = fig.add_subplot(gs[0, 2])
    style_ax(ax3, "Distribución de Monetary", "Gasto total (€)", "Clientes")
    ax3.hist(rfm["Monetary"], bins=30, color=PALETTE[3], edgecolor=BG, alpha=0.85)
    mean_mon = rfm["Monetary"].mean()
    ax3.axvline(mean_mon, color=ACCENT, linestyle="--", linewidth=1.5, label=f"Media: €{mean_mon:,.0f}")
    ax3.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

    # Scatter Recency vs Monetary
    ax4 = fig.add_subplot(gs[1, 0])
    style_ax(ax4, "Recency vs Monetary", "Recency (días)", "Monetary (€)")
    
    if method == "kmeans":
        for cid in sorted(rfm[segment_col].unique()):
            sub = rfm[rfm[segment_col] == cid]
            ax4.scatter(
                sub["Recency"], sub["Monetary"],
                c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
            )
    else:
        for i, seg in enumerate(sorted(rfm[segment_col].unique())):
            sub = rfm[rfm[segment_col] == seg]
            ax4.scatter(
                sub["Recency"], sub["Monetary"],
                c=colors[i], alpha=0.55, s=20, label=seg[:12], edgecolors="none",
            )
    ax4.legend(fontsize=7, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4, ncol=2)

    # Scatter Frequency vs Monetary
    ax5 = fig.add_subplot(gs[1, 1])
    style_ax(ax5, "Frequency vs Monetary", "Frequency (pedidos)", "Monetary (€)")
    
    if method == "kmeans":
        for cid in sorted(rfm[segment_col].unique()):
            sub = rfm[rfm[segment_col] == cid]
            ax5.scatter(
                sub["Frequency"], sub["Monetary"],
                c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
            )
    else:
        for i, seg in enumerate(sorted(rfm[segment_col].unique())):
            sub = rfm[rfm[segment_col] == seg]
            ax5.scatter(
                sub["Frequency"], sub["Monetary"],
                c=colors[i], alpha=0.55, s=20, label=seg[:12], edgecolors="none",
            )
    ax5.legend(fontsize=7, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4, ncol=2)

    # Scatter Recency vs Frequency
    ax6 = fig.add_subplot(gs[1, 2])
    style_ax(ax6, "Recency vs Frequency", "Recency (días)", "Frequency (pedidos)")
    
    if method == "kmeans":
        for cid in sorted(rfm[segment_col].unique()):
            sub = rfm[rfm[segment_col] == cid]
            ax6.scatter(
                sub["Recency"], sub["Frequency"],
                c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
            )
    else:
        for i, seg in enumerate(sorted(rfm[segment_col].unique())):
            sub = rfm[rfm[segment_col] == seg]
            ax6.scatter(
                sub["Recency"], sub["Frequency"],
                c=colors[i], alpha=0.55, s=20, label=seg[:12], edgecolors="none",
            )
    ax6.legend(fontsize=7, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4, ncol=2)

    # Tamaño de segmentos
    ax7 = fig.add_subplot(gs[2, 0])
    style_ax(ax7, "Clientes por Segmento", "Segmento", "Nº de Clientes")
    counts = rfm[segment_col].value_counts().sort_index() if method == "kmeans" else rfm[segment_col].value_counts().sort_values(ascending=False)
    
    if method == "kmeans":
        labels = [f"C{i}" for i in counts.index]
    else:
        labels = [seg[:10] + "..." if len(seg) > 10 else seg for seg in counts.index]
    
    bars = ax7.bar(labels, counts.values, color=colors[:len(counts)], edgecolor=BG, width=0.6)
    
    for bar, val in zip(bars, counts.values):
        ax7.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + counts.max() * 0.02,
            str(val),
            ha="center", va="bottom", color=TEXT_MAIN, fontsize=9, fontweight="bold",
        )
    ax7.set_ylim(0, counts.max() * 1.18)
    if method != "kmeans":
        ax7.tick_params(axis='x', rotation=45)

    # Perfil medio por segmento
    ax8 = fig.add_subplot(gs[2, 1])
    style_ax(ax8, "Perfil Medio por Segmento", "Segmento", "Valor normalizado")

    cluster_profile = rfm.groupby(segment_col).agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean"),
        Clientes=(segment_col, "count"),
    ).round(1)

    metrics = ["Recency", "Frequency", "Monetary"]
    profile_norm = cluster_profile[metrics].copy()
    for col in metrics:
        col_min, col_max = profile_norm[col].min(), profile_norm[col].max()
        profile_norm[col] = (
            (profile_norm[col] - col_min) / (col_max - col_min)
            if col_max != col_min else 0.5
        )

    n_segments_actual = len(cluster_profile)
    n_metrics = len(metrics)
    x = np.arange(n_segments_actual)
    bar_w = 0.22

    metric_colors = [PALETTE[5], PALETTE[2], PALETTE[3]]
    for j, (metric, mc) in enumerate(zip(metrics, metric_colors)):
        offset = (j - n_metrics / 2 + 0.5) * bar_w
        ax8.bar(
            x + offset,
            profile_norm[metric].values,
            width=bar_w,
            color=mc,
            alpha=0.85,
            edgecolor=BG,
            label=metric,
        )

    if method == "kmeans":
        xlabels = [f"C{i}" for i in cluster_profile.index]
    else:
        xlabels = [seg[:8] + "..." if len(seg) > 8 else seg for seg in cluster_profile.index]
    
    ax8.set_xticks(x)
    ax8.set_xticklabels(xlabels, color=TEXT_MAIN, rotation=45)
    ax8.set_ylim(0, 1.25)
    ax8.legend(
        fontsize=8, framealpha=0, labelcolor=TEXT_MAIN,
        loc="upper right",
        title="RFM",
    )

    # TREEMAP - Distribución de Segmentos
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    if SQUARIFY_AVAILABLE:
        segment_counts = rfm[segment_col].value_counts().sort_values(ascending=False)
        
        if method == "kmeans":
            labels_treemap = [f"C{i}\n{segment_counts[i]}\n({segment_counts[i]/len(rfm)*100:.1f}%)" 
                              for i in segment_counts.index]
            colors_treemap = [colors[list(counts.index).index(i)] for i in segment_counts.index]
        else:
            labels_treemap = [f"{seg[:12]}\n{segment_counts[seg]}\n({segment_counts[seg]/len(rfm)*100:.1f}%)" 
                              for seg in segment_counts.index]
            colors_treemap = [colors[list(counts.index).index(seg)] for seg in segment_counts.index]
        
        squarify.plot(
            sizes=segment_counts.values,
            label=labels_treemap,
            color=colors_treemap,
            alpha=0.8,
            ax=ax9,
            text_kwargs={'fontsize': 7, 'color': TEXT_MAIN, 'weight': 'bold'},
            pad=True
        )
        ax9.set_title("Treemap - Distribución", color=TEXT_MAIN, fontsize=11, fontweight="bold", pad=10)
    else:
        ax9.text(0.5, 0.5, "squarify no disponible\npip install squarify", 
                ha='center', va='center', color=TEXT_SUB, fontsize=10)

    # Distribución de Revenue por Segmento
    ax10 = fig.add_subplot(gs[3, :])
    style_ax(ax10, "Distribución de Clientes y Revenue por Segmento", "Segmento", "Porcentaje (%)")
    
    revenue_data = rfm.groupby(segment_col).agg(
        Clientes=(segment_col, 'count'),
        Revenue=('Monetary', 'sum')
    )
    
    # Ordenar por Revenue
    revenue_data = revenue_data.sort_values('Revenue', ascending=False)
    
    revenue_data['% Clientes'] = (revenue_data['Clientes'] / len(rfm) * 100)
    revenue_data['% Revenue'] = (revenue_data['Revenue'] / rfm['Monetary'].sum() * 100)
    
    x_pos = np.arange(len(revenue_data))
    width = 0.35
    
    bars1 = ax10.bar(x_pos - width/2, revenue_data['% Clientes'], width, 
                     label='% Clientes', color=PALETTE[1], alpha=0.8, edgecolor=BG)
    bars2 = ax10.bar(x_pos + width/2, revenue_data['% Revenue'], width,
                     label='% Revenue', color=PALETTE[0], alpha=0.8, edgecolor=BG)
    
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax10.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}%',
                     ha='center', va='bottom', color=TEXT_MAIN, fontsize=8)
    
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax10.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}%',
                     ha='center', va='bottom', color=TEXT_MAIN, fontsize=8)
    
    if method == "kmeans":
        x_labels = [f"C{i}" for i in revenue_data.index]
    else:
        x_labels = [seg[:12] + "..." if len(seg) > 12 else seg for seg in revenue_data.index]
    
    ax10.set_xticks(x_pos)
    ax10.set_xticklabels(x_labels, rotation=45, ha='right')
    ax10.legend(fontsize=10, framealpha=0, labelcolor=TEXT_MAIN)
    ax10.set_ylim(0, max(revenue_data['% Clientes'].max(), revenue_data['% Revenue'].max()) * 1.2)

    return fig, cluster_profile


# ─────────────────────────────────────────────────────────────────
# INICIALIZAR SESSION STATE
# ─────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "df_cleaned" not in st.session_state:
    st.session_state.df_cleaned = None
if "df_with_total" not in st.session_state:
    st.session_state.df_with_total = None
if "df_pedidos" not in st.session_state:
    st.session_state.df_pedidos = None
if "rfm" not in st.session_state:
    st.session_state.rfm = None
if "rfm_base" not in st.session_state:
    st.session_state.rfm_base = None
if "total_col_name" not in st.session_state:
    st.session_state.total_col_name = "total_pedido"
if "segmentation_method" not in st.session_state:
    st.session_state.segmentation_method = None
if "optimal_k" not in st.session_state:
    st.session_state.optimal_k = None
if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "custom_segments" not in st.session_state:
    st.session_state.custom_segments = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "segments_defined" not in st.session_state:
    st.session_state.segments_defined = False

# ─────────────────────────────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────

st.title("📊 RFM Customer Segmentation Tool")
st.markdown("### Herramienta avanzada para segmentación de clientes mediante análisis RFM")

# ═══════════════════════════════════════════════════════════════════
# PASO 0: SELECTOR DE MÉTODO
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("🎯 Selección de Método de Segmentación")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="metric-box">
        <h3 style="color: #E63946; margin-top: 0;">🤖 K-Means Clustering</h3>
        <p style="color: #A8DADC;">
        Algoritmo de machine learning que agrupa clientes automáticamente según similitud en RFM.
        </p>
        <ul style="color: #A8DADC;">
            <li>✅ Detección automática del número óptimo de clusters</li>
            <li>✅ Validación con múltiples métricas</li>
            <li>✅ Ideal para patrones complejos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
        <h3 style="color: #2A9D8F; margin-top: 0;">📊 Segmentación por Cuartiles</h3>
        <p style="color: #A8DADC;">
        Método tradicional que divide clientes en 5 quintiles por cada métrica RFM.
        </p>
        <ul style="color: #A8DADC;">
            <li>✅ Interpretación directa e intuitiva</li>
            <li>✅ Segmentos predefinidos con nombres</li>
            <li>✅ Ideal para equipos de marketing</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("###")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    method_choice = st.radio(
        "Selecciona el método de segmentación:",
        options=["K-Means Clustering", "Segmentación por Cuartiles"],
        horizontal=True,
        key="method_selector"
    )
    
    if method_choice == "K-Means Clustering":
        st.session_state.segmentation_method = "kmeans"
    else:
        st.session_state.segmentation_method = "quartiles"

# ─────────────────────────────────────────────────────────────────
# SIDEBAR: CARGA Y MAPEO DE COLUMNAS
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Configuración")

    uploaded_file = st.file_uploader(
        "📁 Sube tu archivo CSV o Excel",
        type=["csv", "xlsx", "xls"],
        help="Sube el archivo que contiene tus datos de transacciones"
    )

    col_id_usuario = ""
    col_id_pedido = ""
    col_fecha = ""
    col_total = ""
    col_cantidad = ""
    col_precio = ""

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Normalizar columnas object a string
            for c in df.columns:
                if df[c].dtype == "object":
                    try:
                        df[c] = df[c].astype("string")
                    except Exception:
                        df[c] = df[c].astype(str)

            st.session_state.df = df
            st.success(f"✅ {len(df):,} filas, {len(df.columns)} columnas")

            st.markdown("---")
            st.subheader("🗂️ Mapeo de Columnas")

            col_id_usuario = st.selectbox(
                "ID Usuario",
                options=[""] + list(df.columns),
                help="Identificador único del cliente"
            )

            col_id_pedido = st.selectbox(
                "ID Pedido",
                options=[""] + list(df.columns),
                help="Identificador único del pedido/factura"
            )

            col_fecha = st.selectbox(
                "Fecha Pedido",
                options=[""] + list(df.columns),
                help="Fecha en que se realizó el pedido"
            )

            col_total = st.selectbox(
                "Total Pedido (opcional)",
                options=[""] + list(df.columns),
                help="Monto total del pedido"
            )

            st.markdown("---")
            st.markdown("**Para calcular Total:**")

            col_cantidad = st.selectbox(
                "Cantidad",
                options=[""] + list(df.columns),
            )

            col_precio = st.selectbox(
                "Precio Unitario",
                options=[""] + list(df.columns),
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ─────────────────────────────────────────────────────────────────
# ÁREA PRINCIPAL: PROCESAMIENTO
# ─────────────────────────────────────────────────────────────────

if st.session_state.df is not None:
    df = st.session_state.df

    st.markdown("---")
    st.header("1️⃣ Vista Previa de Datos")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Filas", f"{len(df):,}")
    with col2:
        st.metric("📋 Columnas", f"{len(df.columns)}")
    with col3:
        st.metric("💾 Tamaño", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    with st.expander("🔍 Ver datos (primeras 100 filas)"):
        st.dataframe(df.head(100), use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # PASO 2: LIMPIEZA
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.header("2️⃣ Limpieza de Datos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("❌ Nulos")
        nulls = df.isnull().sum()
        nulls_df = pd.DataFrame({
            "Columna": nulls.index,
            "Nulos": nulls.values,
            "%": (nulls.values / len(df) * 100).round(2)
        }).query("Nulos > 0")

        if len(nulls_df) > 0:
            st.dataframe(nulls_df, use_container_width=True)
            st.warning(f"⚠️ {int(df.isnull().sum().sum())} nulos")
        else:
            st.success("✅ Sin nulos")

    with col2:
        st.subheader("➖ Negativos")
        num_cols = df.select_dtypes(include="number").columns

        if len(num_cols) > 0:
            negs = (df[num_cols] < 0).sum()
            negs_df = pd.DataFrame({
                "Columna": negs.index,
                "Negativos": negs.values,
                "%": (negs.values / len(df) * 100).round(2)
            }).query("Negativos > 0")

            if len(negs_df) > 0:
                st.dataframe(negs_df, use_container_width=True)
                st.warning(f"⚠️ {int(negs.sum())} negativos")
            else:
                st.success("✅ Sin negativos")

    clean_options = st.multiselect(
        "Operaciones de limpieza:",
        ["Eliminar filas con nulos", "Eliminar filas con valores negativos"],
        default=["Eliminar filas con nulos", "Eliminar filas con valores negativos"]
    )

    if st.button("🧹 Limpiar Datos", use_container_width=True):
        df_cleaned = df.copy()
        n_inicial = len(df_cleaned)

        if "Eliminar filas con nulos" in clean_options:
            df_cleaned = df_cleaned.dropna()
            st.info(f"🗑️ {n_inicial - len(df_cleaned):,} filas con nulos eliminadas")
            n_inicial = len(df_cleaned)

        if "Eliminar filas con valores negativos" in clean_options:
            num_cols2 = df_cleaned.select_dtypes(include="number").columns
            if len(num_cols2) > 0:
                mask_neg = (df_cleaned[num_cols2] < 0).any(axis=1)
                df_cleaned = df_cleaned.loc[~mask_neg]
                st.info(f"🗑️ {n_inicial - len(df_cleaned):,} filas con negativos eliminadas")

        st.session_state.df_cleaned = df_cleaned
        st.success(f"✅ {len(df_cleaned):,} filas resultantes")
        st.rerun()

    # ══════════════════════════════════════════════════════════════
    # PASO 3: CALCULAR TOTAL
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_cleaned is not None:
        df_cleaned = st.session_state.df_cleaned

        st.markdown("---")
        st.header("3️⃣ Calcular Total del Pedido")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Cantidad:** `{col_cantidad if col_cantidad else 'No seleccionada'}`")
        with col2:
            st.markdown(f"**Precio:** `{col_precio if col_precio else 'No seleccionada'}`")

        if col_cantidad and col_precio:
            nombre_total = st.text_input(
                "Nombre columna total:",
                value=st.session_state.get("total_col_name", "total_pedido")
            )

            if st.button("💰 Calcular Total", use_container_width=True):
                df_with_total = df_cleaned.copy()
                df_with_total[nombre_total] = df_with_total[col_cantidad] * df_with_total[col_precio]

                n_antes = len(df_with_total)
                df_with_total = df_with_total[df_with_total[nombre_total] > 0]
                n_despues = len(df_with_total)

                st.session_state.df_with_total = df_with_total
                st.session_state.total_col_name = nombre_total

                st.success(f"✅ Columna `{nombre_total}` creada")
                st.info(f"🗑️ {n_antes - n_despues:,} filas ≤ 0 eliminadas")
                st.rerun()

    # ══════════════════════════════════════════════════════════════
    # PASO 4: AGRUPACIÓN
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_with_total is not None or col_total:
        st.markdown("---")
        st.header("4️⃣ Agrupación de Pedidos")

        if st.session_state.df_with_total is not None:
            df_trabajo = st.session_state.df_with_total
            col_total_usar = st.session_state.get("total_col_name", "total_pedido")
        else:
            df_trabajo = st.session_state.df_cleaned
            col_total_usar = col_total

        if not all([col_id_usuario, col_id_pedido, col_fecha, col_total_usar]):
            st.warning("⚠️ Selecciona todas las columnas en el sidebar")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**Usuario:** `{col_id_usuario}`")
            with col2:
                st.markdown(f"**Pedido:** `{col_id_pedido}`")
            with col3:
                st.markdown(f"**Fecha:** `{col_fecha}`")
            with col4:
                st.markdown(f"**Total:** `{col_total_usar}`")

            if st.button("📦 Agrupar Pedidos", use_container_width=True):
                try:
                    df_trabajo = df_trabajo.copy()
                    df_trabajo[col_fecha] = pd.to_datetime(df_trabajo[col_fecha])

                    df_pedidos = df_trabajo.groupby(
                        [col_id_usuario, col_id_pedido, col_fecha],
                        as_index=False
                    ).agg({col_total_usar: "sum"})

                    df_pedidos.columns = ["id_usuario", "id_pedido", "fecha_pedido", "total_pedido"]

                    n_antes = len(df_pedidos)
                    df_pedidos = df_pedidos[df_pedidos["total_pedido"] > 0]
                    n_despues = len(df_pedidos)

                    st.session_state.df_pedidos = df_pedidos

                    st.success(f"✅ {len(df_pedidos):,} pedidos únicos")
                    if n_antes != n_despues:
                        st.info(f"🗑️ {n_antes - n_despues:,} pedidos ≤ 0 eliminados")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ══════════════════════════════════════════════════════════════
    # PASO 5: CÁLCULO RFM Y SEGMENTACIÓN
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_pedidos is not None and st.session_state.segmentation_method is not None:
        st.markdown("---")
        st.header("5️⃣ Análisis RFM y Segmentación")

        df_pedidos = st.session_state.df_pedidos

        if st.session_state.segmentation_method == "kmeans":
            st.info("🎯 Se evaluarán múltiples k y se seleccionará el óptimo")

            col1, col2 = st.columns([1, 3])
            with col1:
                k_max = st.slider(
                    "Máximo clusters:",
                    min_value=3,
                    max_value=15,
                    value=10
                )

            if st.button("🚀 Calcular RFM y Validar", use_container_width=True, type="primary"):
                with st.spinner("Calculando..."):
                    fecha_referencia = df_pedidos["fecha_pedido"].max() + pd.Timedelta(days=1)

                    rfm = df_pedidos.groupby("id_usuario").agg(
                        Recency=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
                        Frequency=("id_pedido", "nunique"),
                        Monetary=("total_pedido", "sum"),
                    ).reset_index()

                    scaler = StandardScaler()
                    rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])

                    optimal_k, results_df = auto_select_k(rfm_scaled, k_min=2, k_max=k_max)

                    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                    rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

                    st.session_state.rfm_base = rfm.copy()
                    st.session_state.rfm = rfm
                    st.session_state.optimal_k = optimal_k
                    st.session_state.results_df = results_df
                    st.session_state.rfm_scaled = rfm_scaled
                    st.session_state.segments_defined = False
                    st.session_state.show_results = False

                    st.success(f"✅ k óptimo = {optimal_k}")
                    st.rerun()

        else:  # quartiles
            st.info("📊 Segmentación por quintiles (1-5)")

            if st.button("🚀 Calcular RFM", use_container_width=True, type="primary"):
                with st.spinner("Calculando..."):
                    fecha_referencia = df_pedidos["fecha_pedido"].max() + pd.Timedelta(days=1)

                    rfm = df_pedidos.groupby("id_usuario").agg(
                        Recency=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
                        Frequency=("id_pedido", "nunique"),
                        Monetary=("total_pedido", "sum"),
                    ).reset_index()

                    rfm = rfm_quantiles(rfm)

                    st.session_state.rfm_base = rfm.copy()
                    st.session_state.rfm = None  # No asignar aún
                    st.session_state.segments_defined = False
                    st.session_state.show_results = False

                    st.success("✅ RFM calculado")
                    st.rerun()

        # ══════════════════════════════════════════════════════════════
        # VALIDACIÓN (solo K-Means)
        # ══════════════════════════════════════════════════════════════
        if st.session_state.segmentation_method == "kmeans" and st.session_state.results_df is not None:
            st.markdown("---")
            st.subheader("🔍 Validación de Clusters")

            results_df = st.session_state.results_df
            optimal_k = st.session_state.optimal_k

            optimal_metrics = results_df[results_df['k'] == optimal_k].iloc[0]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Silhouette", f"{optimal_metrics['silhouette']:.3f}")
            with col2:
                st.metric("Davies-Bouldin", f"{optimal_metrics['davies_bouldin']:.3f}")
            with col3:
                st.metric("Calinski-Harabasz", f"{optimal_metrics['calinski_harabasz']:.1f}")
            with col4:
                st.metric("Score Combinado", f"{optimal_metrics['combined_score']:.3f}")

            with st.expander("📊 Ver todas las configuraciones"):
                display_df = results_df.copy().round(3)
                st.dataframe(display_df, use_container_width=True)

            with st.spinner("Generando dashboard de validación..."):
                fig_validation = create_validation_dashboard(results_df)
                st.pyplot(fig_validation)

        # ══════════════════════════════════════════════════════════════
        # DEFINICIÓN DE SEGMENTOS
        # ══════════════════════════════════════════════════════════════
        if st.session_state.rfm_base is not None:
            st.markdown("---")
            st.header("6️⃣ Definición de Segmentos")

            if st.session_state.segmentation_method == "kmeans":
                st.info("💡 Asigna nombres personalizados a cada cluster")

                rfm_base = st.session_state.rfm_base
                
                cluster_names = {}
                for cluster_id in sorted(rfm_base["Cluster"].unique()):
                    cluster_data = rfm_base[rfm_base["Cluster"] == cluster_id]
                    
                    profile = f"R:{cluster_data['Recency'].mean():.0f}d | F:{cluster_data['Frequency'].mean():.1f} | M:€{cluster_data['Monetary'].mean():,.0f}"
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**Cluster {cluster_id}**")
                        st.caption(profile)
                    with col2:
                        cluster_name = st.text_input(
                            f"Nombre:",
                            value=f"Cluster {cluster_id}",
                            key=f"cluster_name_{cluster_id}",
                            placeholder="Ej: Champions, VIP, En riesgo..."
                        )
                        cluster_names[cluster_id] = cluster_name

                if st.button("💾 Aplicar Nombres", use_container_width=True, type="primary"):
                    rfm_copy = rfm_base.copy()
                    rfm_copy["Segmento"] = rfm_copy["Cluster"].map(cluster_names)
                    st.session_state.rfm = rfm_copy
                    st.session_state.segments_defined = True
                    st.success("✅ Segmentos definidos")
                    st.rerun()

            else:  # quartiles
                st.info("💡 Define los segmentos según patrones RFM (formato: [R][F][M])")
                
                st.markdown("""
                **Guía rápida:**
                - Scores: 1 (peor) → 5 (mejor)
                - `[4-5][4-5][4-5]` = Alto en todo (Champions)
                - `[1-2][1-2][1-2]` = Bajo en todo (Perdidos)
                """)

                # Segmentos estándar más comunes
                default_segments = {
                    r"^[4-5][4-5][4-5]$": "Champions",
                    r"^[1-2][4-5][4-5]$": "Cant Lose Them",   # antes fueron buenos, ahora no recientes
                    r"^[3-5][1-3][4-5]$": "Big Spenders",     # gastan mucho
                    r"^[3-5][3-5][1-5]$": "Loyal Customers",  # muy frecuentes y bastante recientes
                    r"^[4-5][1-2][1-3]$": "New Customers",    # nuevos: muy recientes, poca frecuencia
                    r"^[1-3][1-2][1-5]$": "At Risk",          # baja recencia o baja frecuencia
                    r"^[1-2][1-2][1-2]$": "Lost",             # todo bajo
                }


                st.markdown("**Segmentos Predefinidos** (puedes editarlos o agregar nuevos):")
                
                edited_segments = {}
                for i, (pattern, name) in enumerate(default_segments.items()):
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        new_pattern = st.text_input(
                            f"Patrón {i+1}",
                            value=pattern,
                            key=f"pattern_{i}"
                        )
                    with col2:
                        new_name = st.text_input(
                            f"Nombre {i+1}",
                            value=name,
                            key=f"name_{i}"
                        )
                    with col3:
                        keep = st.checkbox("✓", value=True, key=f"keep_{i}")
                    
                    if keep:
                        edited_segments[new_pattern] = new_name

                # Agregar nuevo
                st.markdown("**Agregar Nuevo Segmento:**")
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    new_pattern = st.text_input("Patrón nuevo", key="new_pattern", placeholder="[3-4][3-4][3-4]")
                with col2:
                    new_name = st.text_input("Nombre nuevo", key="new_name", placeholder="Segmento Custom")
                with col3:
                    if st.button("➕"):
                        if new_pattern and new_name:
                            edited_segments[new_pattern] = new_name
                            st.success("✅ Agregado")

                if st.button("💾 Aplicar Segmentos", use_container_width=True, type="primary"):
                    rfm_base = st.session_state.rfm_base
                    rfm_segmented = apply_segment_mapping(rfm_base, edited_segments)
                    st.session_state.rfm = rfm_segmented
                    st.session_state.custom_segments = edited_segments.copy()
                    st.session_state.segments_defined = True
                    st.success(f"✅ {rfm_segmented['Segmento'].nunique()} segmentos creados")
                    st.rerun()

        # ══════════════════════════════════════════════════════════════
        # VISUALIZAR RESULTADOS
        # ══════════════════════════════════════════════════════════════
        if st.session_state.segments_defined and st.session_state.rfm is not None:
            st.markdown("---")
            
            if not st.session_state.show_results:
                if st.button("📊 VISUALIZAR RESULTADOS", use_container_width=True, type="primary", key="show_viz"):
                    st.session_state.show_results = True
                    st.rerun()

        if st.session_state.show_results and st.session_state.rfm is not None:
            rfm = st.session_state.rfm

            st.header("📈 Resultados de la Segmentación")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Clientes", f"{len(rfm):,}")
            with col2:
                if st.session_state.segmentation_method == "kmeans":
                    st.metric("🎯 Clusters", f"{st.session_state.optimal_k}")
                else:
                    st.metric("🎯 Segmentos", f"{rfm['Segmento'].nunique()}")
            with col3:
                st.metric("📅 Recency Media", f"{rfm['Recency'].mean():.0f} días")
            with col4:
                st.metric("💰 Monetary Media", f"€{rfm['Monetary'].mean():,.2f}")

            st.markdown("###")
            st.subheader("📊 Perfiles de Segmentos")

            if st.session_state.segmentation_method == "kmeans":
                segment_col = "Cluster"
            else:
                segment_col = "Segmento"

            cluster_profile = rfm.groupby(segment_col).agg(
                Clientes=(segment_col, "count"),
                Recency_Media=("Recency", "mean"),
                Frequency_Media=("Frequency", "mean"),
                Monetary_Media=("Monetary", "mean"),
                Monetary_Total=("Monetary", "sum"),
            ).round(2)

            cluster_profile["% Clientes"] = (cluster_profile["Clientes"] / len(rfm) * 100).round(1)
            cluster_profile["% Revenue"] = (cluster_profile["Monetary_Total"] / rfm["Monetary"].sum() * 100).round(1)

            # Ordenar por Revenue
            cluster_profile = cluster_profile.sort_values("Monetary_Total", ascending=False)

            st.dataframe(
                cluster_profile.style.format({
                    "Recency_Media": "{:.0f}",
                    "Frequency_Media": "{:.1f}",
                    "Monetary_Media": "€{:,.2f}",
                    "Monetary_Total": "€{:,.2f}",
                    "% Clientes": "{:.1f}%",
                    "% Revenue": "{:.1f}%",
                }),
                use_container_width=True
            )

            st.markdown("###")
            st.subheader("📊 Dashboard Completo")

            with st.spinner("Generando visualizaciones..."):
                fig, profile = create_segmentation_dashboard(
                    rfm,
                    method=st.session_state.segmentation_method
                )
                st.pyplot(fig)

            st.markdown("###")
            st.subheader("💾 Descargar Resultados")

            col1, col2, col3 = st.columns(3)

            with col1:
                csv_buffer = BytesIO()
                rfm.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)

                st.download_button(
                    label="📥 CSV Completo",
                    data=csv_buffer,
                    file_name="rfm_segmentacion.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col2:
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight", facecolor=BG)
                img_buffer.seek(0)

                st.download_button(
                    label="📥 Dashboard PNG",
                    data=img_buffer,
                    file_name="rfm_dashboard.png",
                    mime="image/png",
                    use_container_width=True
                )

            with col3:
                if st.session_state.segmentation_method == "kmeans" and st.session_state.results_df is not None:
                    validation_csv = BytesIO()
                    st.session_state.results_df.to_csv(validation_csv, index=False)
                    validation_csv.seek(0)

                    st.download_button(
                        label="📥 Métricas CSV",
                        data=validation_csv,
                        file_name="validation_metrics.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

else:
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h2 style='color: #E63946;'>👋 Bienvenido</h2>
        <p style='color: #A8DADC; font-size: 1.2rem;'>
            Comienza subiendo tu archivo CSV o Excel desde el panel lateral
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 📊 Paso 1
        **Elige tu método**
        K-Means o Cuartiles
        """)

    with col2:
        st.markdown("""
        ### 🧹 Paso 2
        **Procesa datos**
        Carga, limpia y agrupa
        """)

    with col3:
        st.markdown("""
        ### 🎯 Paso 3
        **Define y visualiza**
        Personaliza segmentos
        """)