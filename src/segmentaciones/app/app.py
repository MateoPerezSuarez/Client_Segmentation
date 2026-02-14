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
# INICIALIZAR SESSION STATE
# ─────────────────────────────────────────────────────────────────
if "paso_actual" not in st.session_state:
    st.session_state.paso_actual = 1
if "df_original" not in st.session_state:
    st.session_state.df_original = None
if "df_limpio" not in st.session_state:
    st.session_state.df_limpio = None
if "df_pedidos" not in st.session_state:
    st.session_state.df_pedidos = None
if "rfm" not in st.session_state:
    st.session_state.rfm = None
if "columnas_asignadas" not in st.session_state:
    st.session_state.columnas_asignadas = False

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
    .paso-completado {
        background: linear-gradient(135deg, #2A9D8F 0%, #1F7A6E 100%);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: white;
        margin-bottom: 1rem;
    }
    .paso-actual {
        background: linear-gradient(135deg, #E63946 0%, #A8324B 100%);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: white;
        margin-bottom: 1rem;
    }
    .paso-pendiente {
        background: #1A1D27;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: #6D6875;
        margin-bottom: 1rem;
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
    style_ax(ax7, "Perfil Promedio por Cluster", "Cluster", "Valor Normalizado")

    profile = rfm.groupby("Cluster")[["Recency", "Frequency", "Monetary"]].mean()
    profile_norm = (profile - profile.min()) / (profile.max() - profile.min())

    x = np.arange(len(profile_norm))
    width = 0.25
    for i, col in enumerate(["Recency", "Frequency", "Monetary"]):
        offset = (i - 1) * width
        bars = ax7.bar(
            x + offset, profile_norm[col],
            width, label=col, color=PALETTE[i+2], edgecolor=BG, alpha=0.85
        )

    ax7.set_xticks(x)
    ax7.set_xticklabels([f"C{i}" for i in profile_norm.index])
    ax7.legend(fontsize=9, framealpha=0, labelcolor=TEXT_MAIN, loc="upper left")
    ax7.set_ylim(0, 1.15)

    plt.close()
    return fig, profile


def mostrar_indicador_pasos():
    """Muestra el indicador visual de pasos"""
    paso = st.session_state.paso_actual
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if paso > 1:
            st.markdown('<div class="paso-completado">✅ Paso 1: Datos Cargados</div>', unsafe_allow_html=True)
        elif paso == 1:
            st.markdown('<div class="paso-actual">📊 Paso 1: Cargar Datos</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="paso-pendiente">⏸️ Paso 1: Cargar Datos</div>', unsafe_allow_html=True)
    
    with col2:
        if paso > 2:
            st.markdown('<div class="paso-completado">✅ Paso 2: Datos Limpios</div>', unsafe_allow_html=True)
        elif paso == 2:
            st.markdown('<div class="paso-actual">🧹 Paso 2: Limpiar Datos</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="paso-pendiente">⏸️ Paso 2: Limpiar Datos</div>', unsafe_allow_html=True)
    
    with col3:
        if paso > 3:
            st.markdown('<div class="paso-completado">✅ Paso 3: Columnas Asignadas</div>', unsafe_allow_html=True)
        elif paso == 3:
            st.markdown('<div class="paso-actual">🎯 Paso 3: Asignar Columnas</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="paso-pendiente">⏸️ Paso 3: Asignar Columnas</div>', unsafe_allow_html=True)
    
    with col4:
        if paso > 3 and st.session_state.rfm is not None:
            st.markdown('<div class="paso-completado">✅ Paso 4: Segmentación Lista</div>', unsafe_allow_html=True)
        elif paso == 4 or (paso > 3 and st.session_state.columnas_asignadas):
            st.markdown('<div class="paso-actual">🚀 Paso 4: Segmentar</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="paso-pendiente">⏸️ Paso 4: Segmentar</div>', unsafe_allow_html=True)
    
    st.markdown("---")


# ═════════════════════════════════════════════════════════════════
# INTERFAZ PRINCIPAL
# ═════════════════════════════════════════════════════════════════

st.title("📊 RFM Segmentation Tool")
st.markdown("### Análisis de segmentación de clientes por pasos")

mostrar_indicador_pasos()

# ═════════════════════════════════════════════════════════════════
# PASO 1: CARGAR DATOS
# ═════════════════════════════════════════════════════════════════
if st.session_state.paso_actual >= 1:
    st.header("1️⃣ Cargar Datos")
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo CSV o Excel",
        type=["csv", "xlsx", "xls"],
        help="El archivo debe contener datos de transacciones o pedidos"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.df_original = df
            
            st.success(f"✅ Archivo cargado: {len(df):,} filas × {len(df.columns)} columnas")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total de Filas", f"{len(df):,}")
            with col2:
                st.metric("📋 Total de Columnas", f"{len(df.columns)}")
            with col3:
                st.metric("💾 Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
            
            with st.expander("👁️ Vista previa de los datos (primeras 100 filas)", expanded=True):
                st.dataframe(df.head(100), use_container_width=True)
            
            with st.expander("📊 Información de columnas"):
                info_df = pd.DataFrame({
                    'Columna': df.columns,
                    'Tipo': df.dtypes.astype(str),
                    'Nulos': df.isnull().sum(),
                    '% Nulos': (df.isnull().sum() / len(df) * 100).round(2)
                })
                st.dataframe(info_df, use_container_width=True)
            
            if st.button("➡️ Continuar a Limpieza de Datos", type="primary"):
                st.session_state.paso_actual = 2
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error al cargar el archivo: {str(e)}")

# ═════════════════════════════════════════════════════════════════
# PASO 2: LIMPIAR DATOS
# ═════════════════════════════════════════════════════════════════
if st.session_state.paso_actual >= 2 and st.session_state.df_original is not None:
    st.markdown("---")
    st.header("2️⃣ Limpiar Datos")
    
    df = st.session_state.df_original.copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("📋 **Acciones de limpieza disponibles:**")
        eliminar_nulos = st.checkbox("Eliminar filas con valores nulos", value=True)
        eliminar_duplicados = st.checkbox("Eliminar filas duplicadas", value=True)
    
    with col2:
        st.info("🔍 **Estado actual de los datos:**")
        st.metric("Filas con nulos", f"{df.isnull().any(axis=1).sum():,}")
        st.metric("Filas duplicadas", f"{df.duplicated().sum():,}")
    
    if st.button("🧹 Limpiar Datos", type="primary"):
        df_limpio = df.copy()
        
        filas_iniciales = len(df_limpio)
        
        if eliminar_nulos:
            df_limpio = df_limpio.dropna()
        
        if eliminar_duplicados:
            df_limpio = df_limpio.drop_duplicates()
        
        filas_finales = len(df_limpio)
        filas_eliminadas = filas_iniciales - filas_finales
        
        st.session_state.df_limpio = df_limpio
        
        st.success(f"✅ Datos limpios: {filas_finales:,} filas ({filas_eliminadas:,} filas eliminadas)")
        
        with st.expander("👁️ Vista previa de datos limpios (primeras 100 filas)", expanded=True):
            st.dataframe(df_limpio.head(100), use_container_width=True)
        
        if st.button("➡️ Continuar a Asignación de Columnas", type="primary"):
            st.session_state.paso_actual = 3
            st.rerun()

# ═════════════════════════════════════════════════════════════════
# PASO 3: ASIGNAR COLUMNAS Y AGRUPAR
# ═════════════════════════════════════════════════════════════════
if st.session_state.paso_actual >= 3 and st.session_state.df_limpio is not None:
    st.markdown("---")
    st.header("3️⃣ Asignar Columnas")
    
    df = st.session_state.df_limpio
    columnas = list(df.columns)
    
    st.info("📌 Selecciona las columnas correspondientes a cada campo necesario para el análisis RFM")
    
    col1, col2 = st.columns(2)
    
    with col1:
        col_id_usuario = st.selectbox(
            "🆔 ID de Usuario/Cliente",
            [""] + columnas,
            help="Columna que identifica únicamente a cada cliente"
        )
        
        col_fecha = st.selectbox(
            "📅 Fecha del Pedido",
            [""] + columnas,
            help="Columna con la fecha de cada transacción"
        )
    
    with col2:
        col_id_pedido = st.selectbox(
            "📦 ID de Pedido/Transacción",
            [""] + columnas,
            help="Columna que identifica únicamente cada pedido"
        )
        
        # Opciones para el total
        st.markdown("**💰 Total del Pedido**")
        
        # Detectar si hay columnas que parezcan cantidad o total
        col_cantidad = None
        col_total = None
        
        for col in columnas:
            col_lower = col.lower()
            if 'cantidad' in col_lower or 'qty' in col_lower or 'quantity' in col_lower:
                col_cantidad = col
            if 'total' in col_lower or 'importe' in col_lower or 'amount' in col_lower or 'price' in col_lower:
                col_total = col
        
        # Radio button para elegir el método
        metodo_total = st.radio(
            "¿Cómo quieres calcular el total?",
            ["Usar columna de Total directamente", "Multiplicar Cantidad × Precio"],
            help="Elige el método según la estructura de tus datos"
        )
        
        if metodo_total == "Usar columna de Total directamente":
            col_total_usar = st.selectbox(
                "Columna de Total",
                [""] + columnas,
                index=columnas.index(col_total) + 1 if col_total and col_total in columnas else 0,
                help="Columna con el valor total de cada línea/pedido"
            )
            col_cantidad_selec = None
            col_precio_selec = None
        else:
            col_cantidad_selec = st.selectbox(
                "Columna de Cantidad",
                [""] + columnas,
                index=columnas.index(col_cantidad) + 1 if col_cantidad and col_cantidad in columnas else 0,
                help="Columna con la cantidad de productos"
            )
            col_precio_selec = st.selectbox(
                "Columna de Precio Unitario",
                [""] + columnas,
                help="Columna con el precio por unidad"
            )
            col_total_usar = None
    
    # Verificar que todas las columnas necesarias estén seleccionadas
    columnas_completas = False
    
    if metodo_total == "Usar columna de Total directamente":
        columnas_completas = all([col_id_usuario, col_id_pedido, col_fecha, col_total_usar])
    else:
        columnas_completas = all([col_id_usuario, col_id_pedido, col_fecha, col_cantidad_selec, col_precio_selec])
    
    if not columnas_completas:
        st.warning("⚠️ Debes seleccionar todas las columnas necesarias antes de continuar")
    else:
        st.success("✅ Todas las columnas asignadas correctamente")
        
        # Mostrar resumen
        with st.expander("📋 Resumen de columnas asignadas", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**🆔 Usuario:** `{col_id_usuario}`")
            with col2:
                st.markdown(f"**📦 Pedido:** `{col_id_pedido}`")
            with col3:
                st.markdown(f"**📅 Fecha:** `{col_fecha}`")
            with col4:
                if metodo_total == "Usar columna de Total directamente":
                    st.markdown(f"**💰 Total:** `{col_total_usar}`")
                else:
                    st.markdown(f"**💰 Total:** `{col_cantidad_selec} × {col_precio_selec}`")
        
        if st.button("📦 Agrupar Pedidos y Calcular Totales", type="primary"):
            try:
                df_trabajo = df.copy()
                
                # Convertir fecha
                df_trabajo[col_fecha] = pd.to_datetime(df_trabajo[col_fecha])
                
                # Calcular el total según el método elegido
                if metodo_total == "Usar columna de Total directamente":
                    df_trabajo['total_calculado'] = df_trabajo[col_total_usar]
                else:
                    df_trabajo['total_calculado'] = df_trabajo[col_cantidad_selec] * df_trabajo[col_precio_selec]
                
                # Agrupar por pedido
                df_pedidos = df_trabajo.groupby(
                    [col_id_usuario, col_id_pedido, col_fecha],
                    as_index=False
                ).agg({'total_calculado': 'sum'})
                
                df_pedidos.columns = ["id_usuario", "id_pedido", "fecha_pedido", "total_pedido"]
                
                # Eliminar pedidos con total <= 0
                n_antes = len(df_pedidos)
                df_pedidos = df_pedidos[df_pedidos["total_pedido"] > 0]
                n_despues = len(df_pedidos)
                
                st.session_state.df_pedidos = df_pedidos
                st.session_state.columnas_asignadas = True
                st.session_state.paso_actual = 4
                
                st.success(f"✅ Pedidos agrupados: {n_despues:,} pedidos únicos")
                
                if n_antes != n_despues:
                    st.info(f"🗑️ Eliminados {n_antes - n_despues:,} pedidos con total ≤ 0")
                
                with st.expander("📊 Vista previa de pedidos agrupados (primeras 100 filas)", expanded=True):
                    st.dataframe(df_pedidos.head(100), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📦 Total Pedidos", f"{len(df_pedidos):,}")
                with col2:
                    st.metric("👥 Clientes Únicos", f"{df_pedidos['id_usuario'].nunique():,}")
                with col3:
                    st.metric("💰 Revenue Total", f"€{df_pedidos['total_pedido'].sum():,.2f}")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al agrupar pedidos: {str(e)}")

# ═════════════════════════════════════════════════════════════════
# PASO 4: SEGMENTACIÓN RFM
# ═════════════════════════════════════════════════════════════════
if st.session_state.paso_actual >= 4 and st.session_state.df_pedidos is not None:
    st.markdown("---")
    st.header("4️⃣ Análisis RFM y Segmentación")
    
    df_pedidos = st.session_state.df_pedidos
    
    st.info("🎯 Se calculará automáticamente el número óptimo de clusters mediante el método del codo")
    
    k_max = st.slider(
        "Máximo de clusters a evaluar:",
        min_value=3,
        max_value=15,
        value=10,
        help="El algoritmo evaluará desde 2 hasta este número"
    )
    
    if st.button("🚀 Calcular RFM y Segmentar Clientes", type="primary"):
        with st.spinner("Calculando RFM y segmentando clientes..."):
            # Calcular RFM
            fecha_referencia = df_pedidos["fecha_pedido"].max() + pd.Timedelta(days=1)
            
            rfm = df_pedidos.groupby("id_usuario").agg(
                Recency=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
                Frequency=("id_pedido", "nunique"),
                Monetary=("total_pedido", "sum"),
            ).reset_index()
            
            # Escalar datos
            scaler = StandardScaler()
            rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
            
            # Encontrar k óptimo
            optimal_k, wcss = auto_select_k(rfm_scaled, k_min=2, k_max=k_max)
            
            # Aplicar K-Means
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)
            
            # Guardar en session state
            st.session_state.rfm = rfm
            st.session_state.optimal_k = optimal_k
            st.session_state.wcss = wcss
            
            st.success(f"✅ Segmentación completada con **k = {optimal_k}** clusters")
            st.rerun()

# ═════════════════════════════════════════════════════════════════
# MOSTRAR RESULTADOS
# ═════════════════════════════════════════════════════════════════
if st.session_state.rfm is not None:
    rfm = st.session_state.rfm
    optimal_k = st.session_state.optimal_k
    wcss = st.session_state.wcss
    
    st.markdown("---")
    st.header("📈 Resultados de la Segmentación")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Clientes", f"{len(rfm):,}")
    with col2:
        st.metric("🎯 Clusters", f"{optimal_k}")
    with col3:
        st.metric("📅 Recency Media", f"{rfm['Recency'].mean():.0f} días")
    with col4:
        st.metric("💰 Monetary Media", f"€{rfm['Monetary'].mean():.2f}")
    
    # Tabla de perfiles
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
        use_container_width=True
    )
    
    # Dashboard
    st.markdown("###")
    st.subheader("📊 Dashboard de Visualización")
    
    with st.spinner("Generando dashboard..."):
        fig, profile = create_dashboard(rfm, wcss, optimal_k)
        st.pyplot(fig)
    
    # Descargas
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
            use_container_width=True
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
            use_container_width=True
        )

# ═════════════════════════════════════════════════════════════════
# PANTALLA DE BIENVENIDA
# ═════════════════════════════════════════════════════════════════
if st.session_state.df_original is None:
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h2 style='color: #E63946; margin-bottom: 1rem;'>👋 Bienvenido</h2>
        <p style='color: #A8DADC; font-size: 1.2rem;'>
            Comienza subiendo tu archivo CSV o Excel
        </p>
        <p style='color: #6D6875; margin-top: 2rem;'>
            📌 Tu archivo debe contener datos de transacciones o pedidos<br>
            📌 Necesitarás columnas para: ID Usuario, ID Pedido, Fecha y Total/Cantidad×Precio
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 📊 Paso 1
        **Carga tu archivo**
        CSV o Excel con datos de transacciones
        """)
    
    with col2:
        st.markdown("""
        ### 🧹 Paso 2
        **Limpia los datos**
        Elimina nulos y duplicados
        """)
    
    with col3:
        st.markdown("""
        ### 🎯 Paso 3
        **Asigna columnas**
        Configura qué columnas usar
        """)
    
    with col4:
        st.markdown("""
        ### 🚀 Paso 4
        **Segmenta clientes**
        Análisis RFM automático
        """)