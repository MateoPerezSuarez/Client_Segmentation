import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from io import BytesIO

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


def auto_select_k(rfm_scaled, k_min: int = 2, k_max: int = 10) -> tuple[int, list]:
    """
    Calcula WCSS para k en [1, k_max] y elige automáticamente el k óptimo
    usando la segunda derivada de la curva (punto de máxima curvatura / codo).
    """
    wcss = []
    for k in range(1, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(rfm_scaled)
        wcss.append(km.inertia_)

    wcss_arr   = np.array(wcss)
    deltas     = np.diff(wcss_arr)
    curvature  = np.diff(deltas)
    codo_idx   = int(np.argmax(curvature))
    optimal_k  = max(k_min, codo_idx + 2)

    return optimal_k, wcss


def create_dashboard(rfm, wcss, optimal_k):
    """Crea el dashboard de visualización"""
    colors = [PALETTE[i % len(PALETTE)] for i in range(optimal_k)]
    k_range = range(1, len(wcss) + 1)

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
        top=0.93, bottom=0.06,
    )

    # ── Elbow + codo marcado ────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    style_ax(ax1, "Método del Codo (WCSS)", "k (nº de clusters)", "WCSS")
    ax1.plot(k_range, wcss, marker="o", color=TEXT_SUB, linewidth=2, zorder=3)
    ax1.axvline(optimal_k, color=ACCENT, linestyle="--", linewidth=1.8, label=f"k = {optimal_k}")
    ax1.scatter([optimal_k], [wcss[optimal_k-1]], color=ACCENT, s=100, zorder=5)
    ax1.set_xticks(list(k_range))
    ax1.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

    # ── Distribución de Recency ─────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    style_ax(ax2, "Distribución de Recency", "Días desde última compra", "Clientes")
    ax2.hist(rfm["Recency"], bins=30, color=PALETTE[1], edgecolor=BG, alpha=0.85)
    mean_recency = rfm["Recency"].mean()
    ax2.axvline(mean_recency, color=ACCENT, linestyle="--", linewidth=1.5, label=f"Media: {mean_recency:.0f} días")
    ax2.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN)

    # ── Tamaño de clusters ──────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    style_ax(ax3, "Clientes por Cluster", "Cluster", "Nº de Clientes")
    counts = rfm["Cluster"].value_counts().sort_index()
    bars = ax3.bar(
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

    # ── Scatter Recency vs Monetary ────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    style_ax(ax4, "Recency vs Monetary", "Recency (días)", "Monetary (€)")
    for cid in sorted(rfm["Cluster"].unique()):
        sub = rfm[rfm["Cluster"] == cid]
        ax4.scatter(
            sub["Recency"], sub["Monetary"],
            c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
        )
    ax4.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

    # ── Scatter Frequency vs Monetary ──────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    style_ax(ax5, "Frequency vs Monetary", "Frequency (pedidos)", "Monetary (€)")
    for cid in sorted(rfm["Cluster"].unique()):
        sub = rfm[rfm["Cluster"] == cid]
        ax5.scatter(
            sub["Frequency"], sub["Monetary"],
            c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
        )
    ax5.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

    # ── Scatter Recency vs Frequency ───────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    style_ax(ax6, "Recency vs Frequency", "Recency (días)", "Frequency (pedidos)")
    for cid in sorted(rfm["Cluster"].unique()):
        sub = rfm[rfm["Cluster"] == cid]
        ax6.scatter(
            sub["Recency"], sub["Frequency"],
            c=colors[cid], alpha=0.55, s=20, label=f"C{cid}", edgecolors="none",
        )
    ax6.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN, markerscale=1.4)

    # ── Radar / Barras agrupadas de perfiles ────────────────────
    ax7 = fig.add_subplot(gs[2, :])
    style_ax(ax7, "Perfil medio de cada Cluster (valores normalizados 0-1)", "Cluster", "Valor normalizado")

    cluster_profile = rfm.groupby("Cluster").agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean"),
        Clientes=("Cluster", "count"),
    ).round(1)

    metrics = ["Recency", "Frequency", "Monetary"]
    profile_norm = cluster_profile[metrics].copy()
    for col in metrics:
        col_min, col_max = profile_norm[col].min(), profile_norm[col].max()
        profile_norm[col] = (
            (profile_norm[col] - col_min) / (col_max - col_min)
            if col_max != col_min else 0.5
        )

    n_clusters = len(cluster_profile)
    n_metrics = len(metrics)
    x = np.arange(n_clusters)
    bar_w = 0.22

    metric_colors = [PALETTE[5], PALETTE[2], PALETTE[3]]
    for j, (metric, mc) in enumerate(zip(metrics, metric_colors)):
        offset = (j - n_metrics / 2 + 0.5) * bar_w
        ax7.bar(
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

    return fig, cluster_profile


# ─────────────────────────────────────────────────────────────────
# APLICACIÓN STREAMLIT
# ─────────────────────────────────────────────────────────────────

st.title("📊 RFM Customer Segmentation Tool")
st.markdown("### Herramienta automatizada para segmentación de clientes mediante análisis RFM")

# Inicializar session_state
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
if "total_col_name" not in st.session_state:
    st.session_state.total_col_name = "total_pedido"

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

    # Defaults (para que existan aunque no haya archivo)
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

            # ✅ FIX Arrow: normaliza columnas object a string (evita StockCode int/str mezclado)
            for c in df.columns:
                if df[c].dtype == "object":
                    try:
                        df[c] = df[c].astype("string")
                    except Exception:
                        df[c] = df[c].astype(str)

            st.session_state.df = df
            st.success(f"✅ Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

            st.markdown("---")
            st.subheader("🗂️ Mapeo de Columnas")
            st.markdown("Selecciona las columnas correspondientes:")

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
                help="Monto total del pedido. Si no existe, se calculará después"
            )

            st.markdown("---")
            st.markdown("**Para calcular Total Pedido** *(opcional)*:")

            col_cantidad = st.selectbox(
                "Cantidad",
                options=[""] + list(df.columns),
                help="Cantidad de productos"
            )

            col_precio = st.selectbox(
                "Precio Unitario",
                options=[""] + list(df.columns),
                help="Precio unitario del producto"
            )

        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")

# ─────────────────────────────────────────────────────────────────
# ÁREA PRINCIPAL
# ─────────────────────────────────────────────────────────────────

if st.session_state.df is not None:
    df = st.session_state.df

    st.markdown("---")
    st.header("1️⃣ Vista Previa de Datos")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total de Filas", f"{len(df):,}")
    with col2:
        st.metric("📋 Total de Columnas", f"{len(df.columns)}")
    with col3:
        st.metric("💾 Tamaño", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    with st.expander("🔍 Ver datos originales (primeras 100 filas)", expanded=False):
        st.dataframe(df.head(100), width="stretch")

    # ══════════════════════════════════════════════════════════════
    # PASO 2: LIMPIEZA DE DATOS
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.header("2️⃣ Limpieza de Datos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("❌ Valores Nulos")
        nulls = df.isnull().sum()
        nulls_df = pd.DataFrame({
            "Columna": nulls.index,
            "Nulos": nulls.values,
            "% Nulos": (nulls.values / len(df) * 100).round(2)
        }).query("Nulos > 0")

        if len(nulls_df) > 0:
            st.dataframe(nulls_df, width="stretch")
            st.warning(f"⚠️ Se encontraron {int(df.isnull().sum().sum())} valores nulos")
        else:
            st.success("✅ No hay valores nulos")

    with col2:
        st.subheader("➖ Valores Negativos")
        num_cols = df.select_dtypes(include="number").columns

        if len(num_cols) > 0:
            negs = (df[num_cols] < 0).sum()
            negs_df = pd.DataFrame({
                "Columna": negs.index,
                "Negativos": negs.values,
                "% Negativos": (negs.values / len(df) * 100).round(2)
            }).query("Negativos > 0")

            if len(negs_df) > 0:
                st.dataframe(negs_df, width="stretch")
                st.warning(f"⚠️ Se encontraron {int(negs.sum())} valores negativos")
            else:
                st.success("✅ No hay valores negativos")
        else:
            st.info("ℹ️ No hay columnas numéricas")

    st.markdown("###")
    clean_options = st.multiselect(
        "Selecciona las operaciones de limpieza:",
        ["Eliminar filas con nulos", "Eliminar filas con valores negativos"],
        default=["Eliminar filas con nulos", "Eliminar filas con valores negativos"]
    )

    if st.button("🧹 Limpiar Datos", width="stretch"):
        df_cleaned = df.copy()
        n_inicial = len(df_cleaned)

        if "Eliminar filas con nulos" in clean_options:
            df_cleaned = df_cleaned.dropna()
            st.info(f"🗑️ Eliminadas {n_inicial - len(df_cleaned):,} filas con nulos")
            n_inicial = len(df_cleaned)

        if "Eliminar filas con valores negativos" in clean_options:
            num_cols2 = df_cleaned.select_dtypes(include="number").columns
            if len(num_cols2) > 0:
                mask_neg = (df_cleaned[num_cols2] < 0).any(axis=1)
                df_cleaned = df_cleaned.loc[~mask_neg]
                st.info(f"🗑️ Eliminadas {n_inicial - len(df_cleaned):,} filas con negativos")

        st.session_state.df_cleaned = df_cleaned
        st.success(f"✅ Limpieza completada. Filas resultantes: {len(df_cleaned):,}")
        st.rerun()

    # ══════════════════════════════════════════════════════════════
    # PASO 3: CALCULAR TOTAL PEDIDO
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_cleaned is not None:
        df_cleaned = st.session_state.df_cleaned

        st.markdown("---")
        st.header("3️⃣ Calcular Total del Pedido")

        st.info("💡 Si ya tienes una columna con el total, puedes omitir este paso y mapearla en el sidebar.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Columna Cantidad:** `{col_cantidad if col_cantidad else 'No seleccionada'}`")
        with col2:
            st.markdown(f"**Columna Precio:** `{col_precio if col_precio else 'No seleccionada'}`")

        if col_cantidad and col_precio:
            nombre_total = st.text_input(
                "Nombre de la nueva columna de total:",
                value=st.session_state.get("total_col_name", "total_pedido")
            )

            if st.button("💰 Calcular Total (Cantidad × Precio)", width="stretch"):
                df_with_total = df_cleaned.copy()
                df_with_total[nombre_total] = df_with_total[col_cantidad] * df_with_total[col_precio]

                n_antes = len(df_with_total)
                df_with_total = df_with_total[df_with_total[nombre_total] > 0]
                n_despues = len(df_with_total)

                st.session_state.df_with_total = df_with_total
                st.session_state.total_col_name = nombre_total  # ✅ guardar nombre real

                st.success(f"✅ Columna `{nombre_total}` creada correctamente")
                st.info(f"🗑️ Eliminadas {n_antes - n_despues:,} filas con {nombre_total} ≤ 0")

                with st.expander("📊 Ver estadísticas del total calculado"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Media", f"€{df_with_total[nombre_total].mean():.2f}")
                    with col2:
                        st.metric("Mediana", f"€{df_with_total[nombre_total].median():.2f}")
                    with col3:
                        st.metric("Mínimo", f"€{df_with_total[nombre_total].min():.2f}")
                    with col4:
                        st.metric("Máximo", f"€{df_with_total[nombre_total].max():.2f}")

                st.rerun()
        else:
            st.warning("⚠️ Debes seleccionar las columnas de Cantidad y Precio en el sidebar")

    # ══════════════════════════════════════════════════════════════
    # PASO 4: AGRUPACIÓN DE PEDIDOS
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_with_total is not None or col_total:
        st.markdown("---")
        st.header("4️⃣ Agrupación de Pedidos")

        if st.session_state.df_with_total is not None:
            df_trabajo = st.session_state.df_with_total
            col_total_usar = st.session_state.get("total_col_name", "total_pedido")  # ✅ usar el nombre real
        else:
            df_trabajo = st.session_state.df_cleaned
            col_total_usar = col_total

        if not all([col_id_usuario, col_id_pedido, col_fecha, col_total_usar]):
            st.warning("⚠️ Debes seleccionar todas las columnas necesarias en el sidebar (ID Usuario, ID Pedido, Fecha, Total)")
        else:
            st.info("📋 Se agruparán los datos por ID Usuario, ID Pedido y Fecha, sumando el Total.")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**ID Usuario:** `{col_id_usuario}`")
            with col2:
                st.markdown(f"**ID Pedido:** `{col_id_pedido}`")
            with col3:
                st.markdown(f"**Fecha:** `{col_fecha}`")
            with col4:
                st.markdown(f"**Total:** `{col_total_usar}`")

            if st.button("📦 Agrupar Pedidos", width="stretch"):
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

                    st.success(f"✅ Agrupación completada: {len(df_pedidos):,} pedidos únicos")
                    if n_antes != n_despues:
                        st.info(f"🗑️ Eliminados {n_antes - n_despues:,} pedidos con total ≤ 0")

                    with st.expander("📊 Ver pedidos agrupados (primeras 100 filas)", expanded=True):
                        st.dataframe(df_pedidos.head(100), width="stretch")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error en la agrupación: {str(e)}")

    # ══════════════════════════════════════════════════════════════
    # PASO 5: CÁLCULO RFM Y SEGMENTACIÓN
    # ══════════════════════════════════════════════════════════════
    if st.session_state.df_pedidos is not None:
        st.markdown("---")
        st.header("5️⃣ Análisis RFM y Segmentación")

        df_pedidos = st.session_state.df_pedidos

        st.info("🎯 Se calculará automáticamente el número óptimo de clusters mediante el método del codo")

        col1, col2 = st.columns([1, 3])
        with col1:
            k_max = st.slider(
                "Máximo de clusters a evaluar:",
                min_value=3,
                max_value=15,
                value=10,
                help="El algoritmo evaluará desde 2 hasta este número"
            )

        if st.button("🚀 Calcular RFM y Segmentar", width="stretch", type="primary"):
            with st.spinner("Calculando RFM y segmentando clientes..."):
                fecha_referencia = df_pedidos["fecha_pedido"].max() + pd.Timedelta(days=1)

                rfm = df_pedidos.groupby("id_usuario").agg(
                    Recency=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
                    Frequency=("id_pedido", "nunique"),
                    Monetary=("total_pedido", "sum"),
                ).reset_index()

                scaler = StandardScaler()
                rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])

                optimal_k, wcss = auto_select_k(rfm_scaled, k_min=2, k_max=k_max)

                kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

                st.session_state.rfm = rfm
                st.session_state.optimal_k = optimal_k
                st.session_state.wcss = wcss

                st.success(f"✅ Segmentación completada con **k = {optimal_k}** clusters")
                st.rerun()

        if st.session_state.rfm is not None:
            rfm = st.session_state.rfm
            optimal_k = st.session_state.optimal_k
            wcss = st.session_state.wcss

            st.markdown("---")
            st.header("📈 Resultados de la Segmentación")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Total Clientes", f"{len(rfm):,}")
            with col2:
                st.metric("🎯 Clusters", f"{optimal_k}")
            with col3:
                st.metric("📅 Recency Media", f"{rfm['Recency'].mean():.0f} días")
            with col4:
                st.metric("💰 Monetary Media", f"€{rfm['Monetary'].mean():.2f}")

            st.markdown("###")
            st.subheader("📊 Perfiles de Clusters")

            cluster_profile = rfm.groupby("Cluster").agg(
                Clientes=("Cluster", "count"),
                Recency_Media=("Recency", "mean"),
                Frequency_Media=("Frequency", "mean"),
                Monetary_Media=("Monetary", "mean"),
                Monetary_Total=("Monetary", "sum"),
            ).round(2)

            cluster_profile["% Clientes"] = (cluster_profile["Clientes"] / len(rfm) * 100).round(1)
            cluster_profile["% Revenue"] = (cluster_profile["Monetary_Total"] / rfm["Monetary"].sum() * 100).round(1)

            st.dataframe(
                cluster_profile.style.format({
                    "Recency_Media": "{:.0f}",
                    "Frequency_Media": "{:.1f}",
                    "Monetary_Media": "€{:,.2f}",
                    "Monetary_Total": "€{:,.2f}",
                    "% Clientes": "{:.1f}%",
                    "% Revenue": "{:.1f}%",
                }),
                width="stretch"
            )

            st.markdown("###")
            st.subheader("📊 Dashboard de Visualización")

            with st.spinner("Generando dashboard..."):
                fig, profile = create_dashboard(rfm, wcss, optimal_k)
                st.pyplot(fig)

            st.markdown("###")
            st.subheader("💾 Descargar Resultados")

            col1, col2 = st.columns(2)

            with col1:
                csv_buffer = BytesIO()
                rfm.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)

                st.download_button(
                    label="📥 Descargar RFM + Clusters (CSV)",
                    data=csv_buffer,
                    file_name="rfm_segmentacion.csv",
                    mime="text/csv",
                    width="stretch"
                )

            with col2:
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight", facecolor=BG)
                img_buffer.seek(0)

                st.download_button(
                    label="📥 Descargar Dashboard (PNG)",
                    data=img_buffer,
                    file_name="rfm_dashboard.png",
                    mime="image/png",
                    width="stretch"
                )

else:
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h2 style='color: #E63946; margin-bottom: 1rem;'>👋 Bienvenido</h2>
        <p style='color: #A8DADC; font-size: 1.2rem;'>
            Comienza subiendo tu archivo CSV o Excel desde el panel lateral
        </p>
        <p style='color: #6D6875; margin-top: 2rem;'>
            📌 Tu archivo debe contener datos de transacciones o pedidos<br>
            📌 Necesitarás columnas para: ID Usuario, ID Pedido, Fecha y Total
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 📊 Paso 1
        **Sube tu archivo**
        CSV o Excel con datos de transacciones
        """)

    with col2:
        st.markdown("""
        ### 🧹 Paso 2
        **Limpia tus datos**
        Elimina nulos y valores negativos
        """)

    with col3:
        st.markdown("""
        ### 🎯 Paso 3
        **Segmenta clientes**
        Análisis RFM automático con K-Means
        """)
