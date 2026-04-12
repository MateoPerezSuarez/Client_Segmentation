import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from seleccionador_columnas import DatasetMapper


# =========================
# 1) LECTURA + PRIMERA VISTA
# =========================

print("\n" + "="*60)
print("LECTURA DE LOS DATOS")
print("="*60)

df = pd.read_excel("data/online+retail/Online Retail.xlsx")

print("\nDatos insertados (primeras 5 filas):")
print(df.head(5))

print("\n" + "-"*60)
print("Vista previa guardada para dashboard final")
print("-"*60)

print("\n" + "="*60)
print("CALIDAD DE DATOS: NULOS Y NEGATIVOS")
print("="*60)

# -------------------------
# NULOS
# -------------------------
nulls_por_col = df.isnull().sum()
total_nulos = int(nulls_por_col.sum())

# Si vas a eliminar filas con algún nulo:
filas_con_nulos = int(df.isnull().any(axis=1).sum())

print("\nNulos por columna:")
print(nulls_por_col)

print("\nResumen nulos:")
print(f" - Total de valores nulos (celdas): {total_nulos}")
print(f" - Filas que tienen al menos 1 nulo (si las vas a eliminar): {filas_con_nulos}")

# -------------------------
# NEGATIVOS
# -------------------------
# Recuento de negativos SOLO en columnas numéricas
num = df.select_dtypes(include="number")

negativos_por_col = (num < 0).sum().sort_values(ascending=False)
total_negativos = int((num < 0).sum().sum())

# Si vas a eliminar filas que tengan algún valor numérico < 0:
filas_con_negativos = int((num < 0).any(axis=1).sum())

print("\nNegativos por columna (solo numéricas):")
print(negativos_por_col)

print("\nResumen negativos:")
print(f" - Total de valores < 0 (celdas numéricas): {total_negativos}")
print(f" - Filas con algún valor numérico < 0 (si las vas a eliminar): {filas_con_negativos}")

print("\n" + "-"*60)
print("Fin sección 1")
print("-"*60)

# -------------------------
# Correcciones de los valores negativos y nulos
# -------------------------

print("\n" + "="*60)
print("LIMPIEZA DE DATOS")
print("="*60)

n_inicial = len(df)
print(f"\nFilas iniciales: {n_inicial:,}")

# -------------------------
# 2.1) ELIMINAR NULOS (FILAS)
# -------------------------
print("\n" + "-"*60)
print("2.1) Eliminación de nulos")
print("-"*60)

filas_con_nulos = int(df.isnull().any(axis=1).sum())
print(f"Filas con al menos 1 nulo: {filas_con_nulos:,}")

df_sin_nulos = df.dropna().copy()
n_post_nulos = len(df_sin_nulos)

print(f"Filas tras dropna(): {n_post_nulos:,}")
print(f"Filas eliminadas por nulos: {n_inicial - n_post_nulos:,}")

# -------------------------
# 2.2) ELIMINAR NEGATIVOS (CASO TÍPICO ONLINE RETAIL)
# -------------------------
print("\n" + "-"*60)
print("2.2) Eliminación de negativos")
print("-"*60)

# Columnas típicas a revisar en Online Retail
cols_neg = [c for c in ["Quantity", "UnitPrice"] if c in df_sin_nulos.columns]

if not cols_neg:
    print("No se encontraron columnas típicas ['Quantity', 'UnitPrice'] para revisar negativos.")
    df_limpio = df_sin_nulos.copy()
else:
    # Cuántas filas tienen negativos en esas columnas
    mask_neg = (df_sin_nulos[cols_neg] < 0).any(axis=1)
    filas_con_neg = int(mask_neg.sum())

    print(f"Columnas revisadas para < 0: {cols_neg}")
    for c in cols_neg:
        print(f" - {c}: {(df_sin_nulos[c] < 0).sum():,} filas con {c} < 0")

    print(f"Filas con algún negativo en {cols_neg}: {filas_con_neg:,}")

    df_limpio = df_sin_nulos.loc[~mask_neg].copy()
    n_post_neg = len(df_limpio)

    print(f"Filas tras eliminar negativos: {n_post_neg:,}")
    print(f"Filas eliminadas por negativos: {n_post_nulos - n_post_neg:,}")

# -------------------------
# 2.3) RESUMEN FINAL
# -------------------------
print("\n" + "="*60)
print("RESUMEN LIMPIEZA")
print("="*60)

print(f"Filas iniciales: {n_inicial:,}")
print(f"Filas finales:   {len(df_limpio):,}")
print(f"Total eliminadas:{n_inicial - len(df_limpio):,}")

print("\n" + "-"*60)
print("Vista rápida del dataframe limpio (5 primeras filas):")
print("-"*60)
print(df_limpio.head(5))


# =========================
# 3) CREACIÓN DE TOTAL (total_price) + FILTRO
# =========================

print("\n" + "="*60)
print("CREACIÓN DE COLUMNA TOTAL (Quantity * UnitPrice)")
print("="*60)

required_cols = ["Quantity", "UnitPrice"]
if not all(c in df_limpio.columns for c in required_cols):
    faltan = [c for c in required_cols if c not in df_limpio.columns]
    raise KeyError(f"Faltan columnas necesarias para crear total_price: {faltan}")

# Crear total_price (nombre como en el notebook, para que el mapper lo pille fácil)
df_limpio["total_price"] = df_limpio["Quantity"] * df_limpio["UnitPrice"]

# Contar cuántos quedarían fuera por no ser > 0
n_no_positivos = int((df_limpio["total_price"] <= 0).sum())
print(f"Filas con total_price <= 0 a eliminar: {n_no_positivos:,}")

# Filtrar
n_antes = len(df_limpio)
df_limpio = df_limpio[df_limpio["total_price"] > 0].copy()
n_despues = len(df_limpio)

print(f"Filas antes del filtro:  {n_antes:,}")
print(f"Filas después del filtro:{n_despues:,}")
print(f"Eliminadas por total_price <= 0: {n_antes - n_despues:,}")

print("\nVista rápida (5 filas) con total_price:")
print(df_limpio[["Quantity", "UnitPrice", "total_price"]].head(5))

mapper = DatasetMapper()
df_std = mapper.transform(df_limpio, auto_map_threshold=0.55, verbose=True)

# =========================
# 4) AGRUPACIÓN A NIVEL PEDIDO (df_pedidos)
# =========================

print("\n" + "="*60)
print("AGRUPACIÓN A NIVEL PEDIDO")
print("="*60)

required_std = ["id_usuario", "id_pedido", "fecha_pedido", "total_pedido"]
missing_std = [c for c in required_std if c not in df_std.columns]
if missing_std:
    raise KeyError(f"Faltan columnas en df_std para construir df_pedidos: {missing_std}")

df_pedidos = df_std.groupby(
    ["id_usuario", "id_pedido", "fecha_pedido"],
    as_index=False
).agg({"total_pedido": "sum"})

print("\nPedidos agregados (5 primeras filas):")
print(df_pedidos.head(5))
print(f"\nShape df_pedidos: {df_pedidos.shape}")

# Filtro extra (como en el notebook)
n_no_pos = int((df_pedidos["total_pedido"] <= 0).sum())
print(f"Filas con total_pedido <= 0 a eliminar: {n_no_pos:,}")

df_pedidos = df_pedidos[df_pedidos["total_pedido"] > 0].copy()
print(f"Shape df_pedidos tras filtro: {df_pedidos.shape}")


# =========================
# 5) CÁLCULO LRFMS (según paper Scientific Reports 2024)
# =========================

print("\n" + "="*60)
print("CÁLCULO LRFMS - Modelo Mejorado según Paper Científico")
print("="*60)

fecha_referencia = df_std["fecha_pedido"].max() + pd.Timedelta(days=1)
print(f"\nFecha referencia: {fecha_referencia}")

# Parámetro P: número de transacciones más recientes a considerar para R'
# Según el paper, P representa "the number of transactions closest to the end of the interval"
P = 3  # Puedes ajustar este valor según tus necesidades
print(f"Parámetro P (transacciones recientes para R'): {P}")

def calculate_lrfms(group, fecha_ref, p_value):
    """
    Calcula métricas LRFMS para un grupo de pedidos de un cliente.
    
    Según el paper (Wang et al., 2024):
    - Length (L): Li = last_i1 - first_i
      Tiempo entre primera y última transacción en el intervalo
      
    - Recency (R'): R'i = (1/P) * Σ(end_i - last_il) 
      Promedio del tiempo entre fin de intervalo y últimas P transacciones
      (Mejora sobre R tradicional que solo usa la última transacción)
      
    - Frequency (F): count(data)
      Número de transacciones únicas
      
    - Monetary (M): sum(price)
      Suma total de compras
      
    - Satisfaction (S): α×CQ + β×CD + γ×CS (OPCIONAL)
      Combinación ponderada de satisfacción con calidad, entrega y servicio
    """
    fechas_ordenadas = group["fecha_pedido"].sort_values()
    
    # Length: tiempo entre primera y última transacción (en días)
    # Refleja la lealtad del cliente según el paper
    if len(fechas_ordenadas) > 1:
        length = (fechas_ordenadas.iloc[-1] - fechas_ordenadas.iloc[0]).days
    else:
        length = 0
    
    # Recency mejorado (R'): promedio de tiempo desde las últimas P transacciones
    # Reduce la aleatoriedad del indicador R tradicional
    # Si hay menos de P transacciones, usa todas las disponibles
    p_actual = min(p_value, len(fechas_ordenadas))
    ultimas_p_fechas = fechas_ordenadas.tail(p_actual)
    recency_prime = sum((fecha_ref - fecha).days for fecha in ultimas_p_fechas) / p_actual
    
    # Frequency: número único de pedidos
    frequency = group["id_pedido"].nunique()
    
    # Monetary: suma total de gastos
    monetary = group["total_pedido"].sum()
    
    return pd.Series({
        'Length': length,
        'Recency_Prime': recency_prime,
        'Frequency': frequency,
        'Monetary': monetary
    })

# Calcular LRFM para cada cliente
lrfm = df_pedidos.groupby("id_usuario").apply(
    lambda x: calculate_lrfms(x, fecha_referencia, P)
).reset_index()

print(f"\n✓ LRFM calculado (primeras 5 filas):")
print(lrfm.head(5))
print("\n✓ Estadísticas descriptivas LRFM:")
print(lrfm[["Length", "Recency_Prime", "Frequency", "Monetary"]].describe())

print("\n" + "="*60)
print("MEJORAS DEL MODELO LRFMS vs RFM TRADICIONAL")
print("="*60)
print("""
1. Length (L): Captura la lealtad del cliente
   - Clientes nuevos tendrán L pequeño
   - Clientes leales tendrán L grande
   - Elimina confusión entre clientes nuevos y leales

2. Recency' (R'): Promedio de últimas P transacciones
   - Reduce aleatoriedad del R tradicional
   - Un cliente leal puede tener R alto por casualidad
   - R' da una visión más estable del comportamiento reciente

3. Perspectiva del cliente: Con S opcional
   - RFM tradicional: solo perspectiva de la empresa
   - LRFMS: incluye satisfacción del cliente
""")

# Opción para agregar Satisfaction (S) si tienes datos de encuestas
print("\n" + "-"*60)
print("SATISFACTION (S) - Componente Opcional")
print("-"*60)

# Intentar detectar si hay columnas de satisfacción
satisfaction_cols = [col for col in df_std.columns if 'satisf' in col.lower() or 'rating' in col.lower()]

if satisfaction_cols:
    print(f"\n✓ Se detectaron columnas relacionadas con satisfacción: {satisfaction_cols}")
    print("\nPara agregar Satisfaction, descomenta el código correspondiente")
else:
    print("\n✗ No se detectaron columnas de satisfacción")
    print("  Continuando solo con LRFM (sin S)")

print("""
Si tienes datos de satisfacción, puedes calcular S como:
  S = α × CQ + β × CD + γ × CS
donde:
  - CQ = satisfacción con calidad del producto
  - CD = satisfacción con puntualidad de entrega  
  - CS = satisfacción con servicio post-venta
  - α, β, γ = pesos (el paper usa 1/3 para cada uno)

Ejemplo de código:
# Si tus columnas se llaman 'satisfaccion_producto', 'satisfaccion_entrega', etc.
satisfaction = df_std.groupby("id_usuario").agg(
    Satisfaction=lambda x: (
        x['satisfaccion_producto'].mean() / 3 +
        x['satisfaccion_entrega'].mean() / 3 +
        x['satisfaccion_servicio'].mean() / 3
    )
).reset_index()

lrfm = lrfm.merge(satisfaction, on='id_usuario', how='left')
""")

# Crear versión compatible con el resto del código
# Para usar en clustering necesitamos normalizar los nombres
rfm = lrfm.copy()
rfm['Recency'] = rfm['Recency_Prime']  # Crear alias para compatibilidad

# Mostrar comparación con RFM tradicional
print("\n" + "="*60)
print("COMPARACIÓN: RFM Tradicional vs LRFMS")
print("="*60)

# Calcular RFM tradicional para comparar
rfm_tradicional = df_pedidos.groupby("id_usuario").agg(
    Recency_Trad=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
    Frequency_Trad=("id_pedido", "nunique"),
    Monetary_Trad=("total_pedido", "sum"),
).reset_index()

comparacion = lrfm.merge(rfm_tradicional, on='id_usuario')

# Mostrar algunos ejemplos donde LRFMS da información adicional
print("\nEjemplos donde LRFMS aporta más información:")
print("\nClientes con mismo R tradicional pero diferente L (lealtad):")
sample_comparison = comparacion.nlargest(3, 'Length')[
    ['id_usuario', 'Length', 'Recency_Prime', 'Recency_Trad', 'Frequency', 'Monetary']
]
print(sample_comparison)

print("\n✓ Modelo LRFMS aplicado correctamente")


# =========================
# 6) DATOS PARA VISUALIZACIÓN
# =========================

print("\n" + "="*60)
print("DATOS PREPARADOS PARA DASHBOARD")
print("="*60)

promedio_ultima_compra = df_std["fecha_pedido"].max() - pd.to_timedelta(rfm["Recency"].mean(), unit="D")
ultimas_fechas = df_pedidos.groupby("id_usuario")["fecha_pedido"].max()

print("✓ Datos de última compra calculados")


# ===========================================================================
# 7) CLUSTERING: PREPARACIÓN DE DATOS
# ===========================================================================

print("\n" + "="*60)
print("PREPARACIÓN DE DATOS PARA CLUSTERING")
print("="*60)

# Usar LRFM para clustering (sin S por ahora)
# Si tienes S, agrégalo aquí: ['Length', 'Recency_Prime', 'Frequency', 'Monetary', 'Satisfaction']
features_clustering = ['Length', 'Recency_Prime', 'Frequency', 'Monetary']

scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[features_clustering])

print(f"✓ Datos escalados con StandardScaler")
print(f"  Features utilizados: {features_clustering}")
print(f"  Shape: {rfm_scaled.shape}")


# ===========================================================================
# 8) MÉTODO DEL CODO (ELBOW METHOD)
# ===========================================================================

print("\n" + "="*60)
print("MÉTODO DEL CODO (ELBOW METHOD)")
print("="*60)

wcss = []  # Within-cluster sum of squares
k_range = range(2, 11)  # Testing k from 2 to 10

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(rfm_scaled)
    wcss.append(kmeans.inertia_)

print("✓ WCSS calculado para k de 2 a 10")


# ===========================================================================
# 9) MÉTODO DE SILUETA (SILHOUETTE METHOD)
# ===========================================================================

print("\n" + "="*60)
print("MÉTODO DE SILUETA (SILHOUETTE METHOD)")
print("="*60)

silhouette_scores = []

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(rfm_scaled)
    silhouette_avg = silhouette_score(rfm_scaled, cluster_labels)
    silhouette_scores.append(silhouette_avg)
    print(f"  Para k={k}: Silhouette Score = {silhouette_avg:.4f}")

# Encontrar el k óptimo según silueta
optimal_k_silhouette = k_range[np.argmax(silhouette_scores)]
print(f"\n✓ Número óptimo de clusters según Silhouette: k={optimal_k_silhouette}")
print(f"  Silhouette Score máximo: {max(silhouette_scores):.4f}")


# ===========================================================================
# 10) APLICACIÓN DE K-MEANS CON K ÓPTIMO
# ===========================================================================

print("\n" + "="*60)
print("APLICACIÓN DE K-MEANS CON K ÓPTIMO")
print("="*60)

optimal_k = optimal_k_silhouette

print(f"Usando k={optimal_k} clusters")

# Apply K-Means clustering with the optimal number of clusters
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

# Calcular el silhouette score final
final_silhouette = silhouette_score(rfm_scaled, rfm['Cluster'])
print(f"✓ Silhouette Score final con k={optimal_k}: {final_silhouette:.4f}")


# ===========================================================================
# 11) PERFILES DE CLUSTERS
# ===========================================================================

print("\n" + "="*60)
print("PERFILES DE CLUSTERS (LRFMS)")
print("="*60)

# Examine cluster profiles
cluster_profile = rfm.groupby('Cluster').agg({
    'Length': 'mean',
    'Recency_Prime': 'mean',
    'Frequency': 'mean',
    'Monetary': 'mean',
    'id_usuario': 'count'
}).round(1)

cluster_profile.rename(columns={'id_usuario': 'Num_Clientes'}, inplace=True)

print("\nPerfiles de Clusters (con modelo LRFMS):")
print(cluster_profile)

# Calcular porcentaje de clientes por cluster
cluster_profile['Porcentaje'] = (cluster_profile['Num_Clientes'] / cluster_profile['Num_Clientes'].sum() * 100).round(1)

print("\nDistribución de clientes por cluster:")
print(cluster_profile[['Num_Clientes', 'Porcentaje']])


# ===========================================================================
# 12) INTERPRETACIÓN DE CLUSTERS (según LRFMS)
# ===========================================================================

print("\n" + "="*60)
print("INTERPRETACIÓN DE CLUSTERS CON LRFMS")
print("="*60)

print("""
Gracias al modelo LRFMS, podemos distinguir mejor:

1. CLIENTES NUEVOS vs LEALES (por Length):
   - Length bajo + Recency' bajo = Cliente nuevo activo
   - Length alto + Recency' bajo = Cliente leal activo
   
2. COMPORTAMIENTO RECIENTE ESTABLE (por Recency'):
   - R' da una visión más estable que R tradicional
   - Menos afectado por la aleatoriedad de una sola compra
   
3. VALOR DEL CLIENTE (por Frequency y Monetary):
   - Como en RFM tradicional pero con mejor contexto
""")

# Análisis automático de clusters
for cluster_id in sorted(rfm['Cluster'].unique()):
    cluster_data = cluster_profile.loc[cluster_id]
    print(f"\n--- CLUSTER {cluster_id} ({cluster_data['Porcentaje']:.1f}% de clientes) ---")
    
    # Interpretación basada en métricas LRFMS
    length_val = cluster_data['Length']
    recency_val = cluster_data['Recency_Prime']
    freq_val = cluster_data['Frequency']
    mon_val = cluster_data['Monetary']
    
    # Clasificar el cluster
    if length_val < rfm['Length'].median():
        if recency_val < rfm['Recency_Prime'].median():
            tipo = "CLIENTES NUEVOS ACTIVOS"
            desc = "Clientes recientes que han comenzado a comprar"
        else:
            tipo = "CLIENTES NUEVOS INACTIVOS"
            desc = "Clientes nuevos que no han vuelto a comprar"
    else:
        if recency_val < rfm['Recency_Prime'].median():
            if mon_val > rfm['Monetary'].median():
                tipo = "CLIENTES VIP/LEALES"
                desc = "Clientes de alto valor y lealtad demostrada"
            else:
                tipo = "CLIENTES LEALES"
                desc = "Clientes fieles pero de menor valor"
        else:
            tipo = "CLIENTES EN RIESGO"
            desc = "Clientes leales que están dejando de comprar"
    
    print(f"  Tipo: {tipo}")
    print(f"  Descripción: {desc}")
    print(f"  Métricas promedio:")
    print(f"    - Length (lealtad): {length_val:.1f} días")
    print(f"    - Recency' (actividad reciente): {recency_val:.1f} días")
    print(f"    - Frequency: {freq_val:.1f} compras")
    print(f"    - Monetary: ${mon_val:,.2f}")


# ===========================================================================
# 13) VISUALIZACIÓN: DASHBOARD COMPLETO CON LRFMS
# ===========================================================================

print("\n" + "="*60)
print("GENERANDO DASHBOARD COMPLETO CON LRFMS")
print("="*60)

# Crear directorio de outputs si no existe
import os
from pathlib import Path

# Obtener la ruta del script actual
script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
output_dir = script_dir / 'outputs'
output_dir.mkdir(exist_ok=True)

print(f"✓ Directorio de outputs: {output_dir}")

# Crear figura principal con subplots
fig = plt.figure(figsize=(24, 14))
gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

# ============ FILA 1: MÉTODOS DE SELECCIÓN ============

# 1.1) Elbow Method
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(k_range, wcss, marker='o', linestyle='-', color='b', linewidth=2, markersize=8)
ax1.set_xlabel('Número de Clusters (k)', fontsize=10)
ax1.set_ylabel('WCSS', fontsize=10)
ax1.set_title('Método del Codo', fontsize=12, fontweight='bold')
ax1.set_xticks(k_range)
ax1.grid(True, alpha=0.3)

# 1.2) Silhouette Method
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(k_range, silhouette_scores, marker='o', linestyle='-', color='green', linewidth=2, markersize=8)
ax2.axhline(y=np.mean(silhouette_scores), color='r', linestyle='--', alpha=0.5, label='Promedio')
ax2.scatter(optimal_k_silhouette, max(silhouette_scores), color='red', s=200, zorder=5, 
            label=f'Óptimo: k={optimal_k_silhouette}')
ax2.set_xlabel('Número de Clusters (k)', fontsize=10)
ax2.set_ylabel('Silhouette Score', fontsize=10)
ax2.set_title('Método de Silueta', fontsize=12, fontweight='bold')
ax2.set_xticks(k_range)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8)

# 1.3) Distribución de Última Compra
ax3 = fig.add_subplot(gs[0, 2])
ax3.axvline(promedio_ultima_compra, color='r', linestyle='--', linewidth=2, label='Promedio Última Compra')
ax3.hist(ultimas_fechas, bins=30, edgecolor="black", alpha=0.7, color='steelblue')
ax3.set_xlabel('Fecha de la Última Compra', fontsize=10)
ax3.set_ylabel('Número de Clientes', fontsize=10)
ax3.set_title('Distribución Última Compra', fontsize=12, fontweight='bold')
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3, axis='y')
ax3.tick_params(axis='x', rotation=45, labelsize=8)

# ============ FILA 2: VISUALIZACIÓN LRFMS ============

# 2.1) Length vs Recency' (característica única de LRFMS)
ax4 = fig.add_subplot(gs[1, :2])
scatter = ax4.scatter(rfm['Length'], rfm['Recency_Prime'], c=rfm['Cluster'], 
                     cmap='viridis', alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax4.set_xlabel('Length - Lealtad (días)', fontsize=10)
ax4.set_ylabel("Recency' - Actividad Reciente (días)", fontsize=10)
ax4.set_title(f'Segmentación LRFMS (k={optimal_k}) - Length vs Recency\'\nDiferenciación entre clientes nuevos y leales', 
          fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Cluster', fontsize=10)

# 2.2) Distribución de Clientes por Cluster
ax5 = fig.add_subplot(gs[1, 2])
colors = plt.cm.viridis(np.linspace(0, 1, optimal_k))
wedges, texts, autotexts = ax5.pie(cluster_profile['Num_Clientes'], 
                                     labels=[f'Cluster {i}' for i in cluster_profile.index],
                                     autopct='%1.1f%%', 
                                     startangle=90, 
                                     colors=colors,
                                     textprops={'fontsize': 9})
ax5.set_title('Distribución de Clientes', fontsize=12, fontweight='bold')

# ============ FILA 3: MÉTRICAS LRFMS ============

# 3.1) Length Media por Cluster (NUEVO en LRFMS)
ax6 = fig.add_subplot(gs[2, 0])
bars1 = ax6.bar(cluster_profile.index, cluster_profile['Length'], color='purple', edgecolor='black', alpha=0.8)
ax6.set_xlabel('Cluster', fontsize=10)
ax6.set_ylabel('Length Media (días)', fontsize=10)
ax6.set_title('Length (Lealtad) por Cluster\n[NUEVO en LRFMS]', fontsize=12, fontweight='bold')
ax6.grid(axis='y', alpha=0.3)
for bar in bars1:
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 3.2) Recency' Media por Cluster (MEJORADO en LRFMS)
ax7 = fig.add_subplot(gs[2, 1])
bars2 = ax7.bar(cluster_profile.index, cluster_profile['Recency_Prime'], color='steelblue', edgecolor='black', alpha=0.8)
ax7.set_xlabel('Cluster', fontsize=10)
ax7.set_ylabel("Recency' Media (días)", fontsize=10)
ax7.set_title("Recency' por Cluster\n[MEJORADO: promedio últimas P compras]", fontsize=12, fontweight='bold')
ax7.grid(axis='y', alpha=0.3)
for bar in bars2:
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 3.3) Frequency Media por Cluster
ax8 = fig.add_subplot(gs[2, 2])
bars3 = ax8.bar(cluster_profile.index, cluster_profile['Frequency'], color='coral', edgecolor='black', alpha=0.8)
ax8.set_xlabel('Cluster', fontsize=10)
ax8.set_ylabel('Frequency Media', fontsize=10)
ax8.set_title('Frequency Media por Cluster', fontsize=12, fontweight='bold')
ax8.grid(axis='y', alpha=0.3)
for bar in bars3:
    height = bar.get_height()
    ax8.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# ============ FILA 4: COMPARACIÓN Y MONETARY ============

# 4.1) Monetary Media por Cluster
ax9 = fig.add_subplot(gs[3, 0])
bars4 = ax9.bar(cluster_profile.index, cluster_profile['Monetary'], color='mediumseagreen', edgecolor='black', alpha=0.8)
ax9.set_xlabel('Cluster', fontsize=10)
ax9.set_ylabel('Monetary Media', fontsize=10)
ax9.set_title('Monetary Media por Cluster', fontsize=12, fontweight='bold')
ax9.grid(axis='y', alpha=0.3)
for bar in bars4:
    height = bar.get_height()
    ax9.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}',
            ha='center', va='bottom', fontsize=8)

# 4.2) Comparación Length vs Frequency (interacción LRFMS)
ax10 = fig.add_subplot(gs[3, 1])
scatter2 = ax10.scatter(rfm['Length'], rfm['Frequency'], c=rfm['Cluster'], 
                       cmap='viridis', alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax10.set_xlabel('Length - Lealtad (días)', fontsize=10)
ax10.set_ylabel('Frequency', fontsize=10)
ax10.set_title('Length vs Frequency\nRelación lealtad-actividad', fontsize=12, fontweight='bold')
ax10.grid(True, alpha=0.3)

# 4.3) Recency' vs Monetary
ax11 = fig.add_subplot(gs[3, 2])
scatter3 = ax11.scatter(rfm['Recency_Prime'], rfm['Monetary'], c=rfm['Cluster'], 
                       cmap='viridis', alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax11.set_xlabel("Recency' (días)", fontsize=10)
ax11.set_ylabel('Monetary Value', fontsize=10)
ax11.set_title("Recency' vs Monetary\nActividad reciente vs valor", fontsize=12, fontweight='bold')
ax11.grid(True, alpha=0.3)

# Título principal del dashboard
fig.suptitle('DASHBOARD DE SEGMENTACIÓN - MODELO LRFMS MEJORADO\nWang et al. (2024) - Scientific Reports', 
             fontsize=16, fontweight='bold', y=0.998)

# Ajustar espaciado manualmente en lugar de tight_layout
plt.subplots_adjust(top=0.96, bottom=0.05, left=0.05, right=0.98)

# Guardar dashboard
dashboard_path = output_dir / 'lrfms_dashboard.png'
plt.savefig(dashboard_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"\n✓ Dashboard guardado en: {dashboard_path}")
plt.show()


# ===========================================================================
# 14) GUARDAR RESULTADOS Y REPORTES
# ===========================================================================

print("\n" + "="*60)
print("GUARDANDO RESULTADOS Y REPORTES")
print("="*60)

# 1) Guardar datos de clientes con clusters
rfm_output = rfm.copy()
rfm_output_path = output_dir / 'clientes_segmentados_lrfms.csv'
rfm_output.to_csv(rfm_output_path, index=False, encoding='utf-8-sig')
print(f"✓ Clientes segmentados guardados en: {rfm_output_path}")

# 2) Guardar perfiles de clusters
cluster_profile_path = output_dir / 'perfiles_clusters_lrfms.csv'
cluster_profile.to_csv(cluster_profile_path, encoding='utf-8-sig')
print(f"✓ Perfiles de clusters guardados en: {cluster_profile_path}")

# 3) Crear reporte detallado en texto
reporte_path = output_dir / 'reporte_segmentacion_lrfms.txt'
with open(reporte_path, 'w', encoding='utf-8') as f:
    f.write("="*70 + "\n")
    f.write("REPORTE DE SEGMENTACIÓN DE CLIENTES - MODELO LRFMS\n")
    f.write("="*70 + "\n\n")
    
    f.write(f"Fecha de análisis: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Fecha de referencia: {fecha_referencia.strftime('%Y-%m-%d')}\n")
    f.write(f"Parámetro P (Recency'): {P}\n")
    f.write(f"Total de clientes: {len(rfm):,}\n")
    f.write(f"Número de clusters: {optimal_k}\n")
    f.write(f"Silhouette Score: {final_silhouette:.4f}\n\n")
    
    f.write("="*70 + "\n")
    f.write("PERFILES DE CLUSTERS\n")
    f.write("="*70 + "\n\n")
    f.write(cluster_profile.to_string())
    f.write("\n\n")
    
    f.write("="*70 + "\n")
    f.write("INTERPRETACIÓN POR CLUSTER\n")
    f.write("="*70 + "\n\n")
    
    for cluster_id in sorted(rfm['Cluster'].unique()):
        cluster_data = cluster_profile.loc[cluster_id]
        f.write(f"\n--- CLUSTER {cluster_id} ({cluster_data['Porcentaje']:.1f}% de clientes, n={int(cluster_data['Num_Clientes'])}) ---\n")
        
        length_val = cluster_data['Length']
        recency_val = cluster_data['Recency_Prime']
        freq_val = cluster_data['Frequency']
        mon_val = cluster_data['Monetary']
        
        # Clasificar el cluster
        if length_val < rfm['Length'].median():
            if recency_val < rfm['Recency_Prime'].median():
                tipo = "CLIENTES NUEVOS ACTIVOS"
                desc = "Clientes recientes que han comenzado a comprar"
            else:
                tipo = "CLIENTES NUEVOS INACTIVOS"
                desc = "Clientes nuevos que no han vuelto a comprar"
        else:
            if recency_val < rfm['Recency_Prime'].median():
                if mon_val > rfm['Monetary'].median():
                    tipo = "CLIENTES VIP/LEALES"
                    desc = "Clientes de alto valor y lealtad demostrada"
                else:
                    tipo = "CLIENTES LEALES"
                    desc = "Clientes fieles pero de menor valor"
            else:
                tipo = "CLIENTES EN RIESGO"
                desc = "Clientes leales que están dejando de comprar"
        
        f.write(f"Tipo: {tipo}\n")
        f.write(f"Descripción: {desc}\n")
        f.write(f"Métricas promedio:\n")
        f.write(f"  - Length (lealtad): {length_val:.1f} días\n")
        f.write(f"  - Recency' (actividad reciente): {recency_val:.1f} días\n")
        f.write(f"  - Frequency: {freq_val:.1f} compras\n")
        f.write(f"  - Monetary: ${mon_val:,.2f}\n\n")
    
    f.write("\n" + "="*70 + "\n")
    f.write("VENTAJAS DEL MODELO LRFMS\n")
    f.write("="*70 + "\n\n")
    f.write("1. Length (L): Distingue clientes nuevos de clientes leales\n")
    f.write("   - Elimina confusión entre clientes nuevos y clientes que vuelven\n\n")
    f.write("2. Recency' (R'): Más estable que Recency tradicional\n")
    f.write(f"   - Usa promedio de últimas {P} compras en lugar de solo la última\n")
    f.write("   - Reduce falsos positivos en detección de clientes en riesgo\n\n")
    f.write("3. Base científica:\n")
    f.write("   Wang, S., Sun, L. & Yu, Y. (2024).\n")
    f.write("   Scientific Reports, 14, 17491.\n")

print(f"✓ Reporte detallado guardado en: {reporte_path}")

# 4) Guardar resumen ejecutivo
resumen_path = output_dir / 'resumen_ejecutivo_lrfms.txt'
with open(resumen_path, 'w', encoding='utf-8') as f:
    f.write("RESUMEN EJECUTIVO - SEGMENTACIÓN LRFMS\n")
    f.write("="*50 + "\n\n")
    
    f.write(f"Total de clientes: {len(rfm):,}\n")
    f.write(f"Clusters identificados: {optimal_k}\n")
    f.write(f"Calidad de segmentación (Silhouette): {final_silhouette:.4f}\n\n")
    
    f.write("DISTRIBUCIÓN DE CLIENTES:\n")
    f.write("-"*50 + "\n")
    for cluster_id in sorted(rfm['Cluster'].unique()):
        num_clientes = int(cluster_profile.loc[cluster_id, 'Num_Clientes'])
        porcentaje = cluster_profile.loc[cluster_id, 'Porcentaje']
        f.write(f"Cluster {cluster_id}: {num_clientes:,} clientes ({porcentaje:.1f}%)\n")
    
    f.write("\n")
    top_cluster = cluster_profile.nlargest(1, 'Monetary').index[0]
    f.write(f"Cluster de mayor valor: Cluster {top_cluster}\n")
    f.write(f"Valor promedio: ${cluster_profile.loc[top_cluster, 'Monetary']:,.2f}\n")

print(f"✓ Resumen ejecutivo guardado en: {resumen_path}")

# 5) Guardar estadísticas comparativas
stats_path = output_dir / 'estadisticas_lrfms.csv'
stats_df = pd.DataFrame({
    'Métrica': ['Total Clientes', 'Número de Clusters', 'Silhouette Score', 
                'Parámetro P', 'Length Media (días)', 'Recency\' Media (días)',
                'Frequency Media', 'Monetary Medio'],
    'Valor': [
        f"{len(rfm):,}",
        optimal_k,
        f"{final_silhouette:.4f}",
        P,
        f"{rfm['Length'].mean():.1f}",
        f"{rfm['Recency_Prime'].mean():.1f}",
        f"{rfm['Frequency'].mean():.1f}",
        f"${rfm['Monetary'].mean():,.2f}"
    ]
})
stats_df.to_csv(stats_path, index=False, encoding='utf-8-sig')
print(f"✓ Estadísticas guardadas en: {stats_path}")

print("\n" + "="*60)
print("ARCHIVOS GENERADOS")
print("="*60)
print(f"""
1. {dashboard_path.name}
   → Dashboard visual con todos los gráficos

2. {rfm_output_path.name}
   → Datos de todos los clientes con su cluster asignado

3. {cluster_profile_path.name}
   → Perfiles promedio de cada cluster

4. {reporte_path.name}
   → Reporte detallado con interpretaciones

5. {resumen_path.name}
   → Resumen ejecutivo breve

6. {stats_path.name}
   → Estadísticas principales del análisis
""")

print("\n" + "="*60)
print("ANÁLISIS LRFMS COMPLETADO EXITOSAMENTE")
print("="*60)
print(f"""
✅ Modelo LRFMS aplicado correctamente
  - Número óptimo de clusters: {optimal_k}
  - Silhouette Score: {final_silhouette:.4f}
  - Total de clientes segmentados: {len(rfm):,}
  - Features utilizados: {features_clustering}

📁 TODOS LOS RESULTADOS EN:
  {output_dir.absolute()}

🎯 VENTAJAS DE LRFMS SOBRE RFM TRADICIONAL:
  1. Length (L): Distingue clientes nuevos de leales
  2. Recency' (R'): Más estable que R (usa últimas {P} compras)
  3. Base científica: Publicado en Scientific Reports (2024)

📚 REFERENCIA:
  Wang, S., Sun, L. & Yu, Y. (2024). 
  A dynamic customer segmentation approach by combining LRFMS 
  and multivariate time series clustering. 
  Scientific Reports, 14, 17491.
  https://doi.org/10.1038/s41598-024-68621-2

💡 PRÓXIMOS PASOS SUGERIDOS:
  1. Revisa el dashboard visual (PNG)
  2. Analiza los perfiles de clusters (CSV)
  3. Define estrategias de marketing por cluster
  4. Si tienes datos de satisfacción, agrega la métrica S

¡Análisis finalizado! Todos los archivos están en la carpeta outputs/
""")