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
# 5) CÁLCULO RFM
# =========================

print("\n" + "="*60)
print("CÁLCULO RFM")
print("="*60)

fecha_referencia = df_std["fecha_pedido"].max() + pd.Timedelta(days=1)
print(f"\nFecha referencia: {fecha_referencia}")

rfm = df_pedidos.groupby("id_usuario").agg(
    Recency=("fecha_pedido", lambda x: (fecha_referencia - x.max()).days),
    Frequency=("id_pedido", "nunique"),
    Monetary=("total_pedido", "sum"),
).reset_index()

print("\nRFM (5 primeras filas):")
print(rfm.head(5))
print("\nDescribe RFM:")
print(rfm[["Recency", "Frequency", "Monetary"]].describe())


# =========================
# 6) PLOT: distribución última compra (opcional)
# =========================

print("\n" + "="*60)
print("DATOS PREPARADOS PARA DASHBOARD")
print("="*60)

promedio_ultima_compra = df_std["fecha_pedido"].max() - pd.to_timedelta(rfm["Recency"].mean(), unit="D")
ultimas_fechas = df_pedidos.groupby("id_usuario")["fecha_pedido"].max()

print("Datos de última compra calculados")


# ===========================================================================
# 7) CLUSTERING: PREPARACIÓN DE DATOS
# ===========================================================================

print("\n" + "="*60)
print("PREPARACIÓN DE DATOS PARA CLUSTERING")
print("="*60)

scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[['Recency', 'Frequency', 'Monetary']])

print("Datos RFM escalados con StandardScaler")
print(f"Shape: {rfm_scaled.shape}")


# ===========================================================================
# 8) MÉTODO DEL CODO (ELBOW METHOD)
# ===========================================================================

print("\n" + "="*60)
print("MÉTODO DEL CODO (ELBOW METHOD)")
print("="*60)

wcss = []  # Within-cluster sum of squares
k_range = range(2, 11)  # Testing k from 2 to 10

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(rfm_scaled)
    wcss.append(kmeans.inertia_)  # Inertia is WCSS

print("WCSS calculado para k de 2 a 10")


# ===========================================================================
# 9) MÉTODO DE SILUETA (SILHOUETTE METHOD) - NUEVO
# ===========================================================================

print("\n" + "="*60)
print("MÉTODO DE SILUETA (SILHOUETTE METHOD)")
print("="*60)

silhouette_scores = []

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    cluster_labels = kmeans.fit_predict(rfm_scaled)
    silhouette_avg = silhouette_score(rfm_scaled, cluster_labels)
    silhouette_scores.append(silhouette_avg)
    print(f"Para k={k}: Silhouette Score = {silhouette_avg:.4f}")

# Encontrar el k óptimo según silueta
optimal_k_silhouette = k_range[np.argmax(silhouette_scores)]
print(f"\nNúmero óptimo de clusters según Silhouette: k={optimal_k_silhouette}")
print(f"Silhouette Score máximo: {max(silhouette_scores):.4f}")


# ===========================================================================
# 10) APLICACIÓN DE K-MEANS CON K ÓPTIMO
# ===========================================================================

print("\n" + "="*60)
print("APLICACIÓN DE K-MEANS CON K ÓPTIMO")
print("="*60)

# Puedes elegir el k basado en tu análisis visual o usar el de silueta
# Aquí usaremos el de silueta, pero puedes cambiarlo manualmente
optimal_k = optimal_k_silhouette  # O puedes poner: optimal_k = 4

print(f"Usando k={optimal_k} clusters")

# Apply K-Means clustering with the optimal number of clusters
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

# Calcular el silhouette score final
final_silhouette = silhouette_score(rfm_scaled, rfm['Cluster'])
print(f"Silhouette Score final con k={optimal_k}: {final_silhouette:.4f}")


# ===========================================================================
# 11) PERFILES DE CLUSTERS
# ===========================================================================

print("\n" + "="*60)
print("PERFILES DE CLUSTERS")
print("="*60)

# Examine cluster profiles
cluster_profile = rfm.groupby('Cluster').agg({
    'Recency': 'mean',
    'Frequency': 'mean',
    'Monetary': 'mean',
    'id_usuario': 'count'  # Añadimos el conteo de clientes por cluster
}).round(1)

cluster_profile.rename(columns={'id_usuario': 'Num_Clientes'}, inplace=True)

print("\nPerfiles de Clusters:")
print(cluster_profile)

# Calcular porcentaje de clientes por cluster
cluster_profile['Porcentaje'] = (cluster_profile['Num_Clientes'] / cluster_profile['Num_Clientes'].sum() * 100).round(1)

print("\nDistribución de clientes por cluster:")
print(cluster_profile[['Num_Clientes', 'Porcentaje']])


# ===========================================================================
# 12) VISUALIZACIÓN: DASHBOARD COMPLETO
# ===========================================================================

print("\n" + "="*60)
print("GENERANDO DASHBOARD COMPLETO")
print("="*60)

# Crear figura principal con subplots
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

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

# ============ FILA 2: VISUALIZACIÓN DE CLUSTERS ============

# 2.1) Clusters Recency vs Monetary
ax4 = fig.add_subplot(gs[1, :2])
scatter = ax4.scatter(rfm['Recency'], rfm['Monetary'], c=rfm['Cluster'], 
                     cmap='viridis', alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax4.set_xlabel('Recency (días)', fontsize=10)
ax4.set_ylabel('Monetary Value', fontsize=10)
ax4.set_title(f'Segmentación de Clientes (k={optimal_k}) - Recency vs Monetary\nSilhouette Score: {final_silhouette:.4f}', 
          fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Cluster', fontsize=10)

# 2.2) Distribución de Clientes por Cluster (Pie Chart)
ax5 = fig.add_subplot(gs[1, 2])
colors = plt.cm.viridis(np.linspace(0, 1, optimal_k))
wedges, texts, autotexts = ax5.pie(cluster_profile['Num_Clientes'], 
                                     labels=[f'Cluster {i}' for i in cluster_profile.index],
                                     autopct='%1.1f%%', 
                                     startangle=90, 
                                     colors=colors,
                                     textprops={'fontsize': 9})
ax5.set_title('Distribución de Clientes', fontsize=12, fontweight='bold')

# ============ FILA 3: MÉTRICAS POR CLUSTER ============

# 3.1) Recency Media por Cluster
ax6 = fig.add_subplot(gs[2, 0])
bars1 = ax6.bar(cluster_profile.index, cluster_profile['Recency'], color='steelblue', edgecolor='black', alpha=0.8)
ax6.set_xlabel('Cluster', fontsize=10)
ax6.set_ylabel('Recency Media (días)', fontsize=10)
ax6.set_title('Recency Media por Cluster', fontsize=12, fontweight='bold')
ax6.grid(axis='y', alpha=0.3)
# Añadir valores en las barras
for bar in bars1:
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 3.2) Frequency Media por Cluster
ax7 = fig.add_subplot(gs[2, 1])
bars2 = ax7.bar(cluster_profile.index, cluster_profile['Frequency'], color='coral', edgecolor='black', alpha=0.8)
ax7.set_xlabel('Cluster', fontsize=10)
ax7.set_ylabel('Frequency Media', fontsize=10)
ax7.set_title('Frequency Media por Cluster', fontsize=12, fontweight='bold')
ax7.grid(axis='y', alpha=0.3)
# Añadir valores en las barras
for bar in bars2:
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 3.3) Monetary Media por Cluster
ax8 = fig.add_subplot(gs[2, 2])
bars3 = ax8.bar(cluster_profile.index, cluster_profile['Monetary'], color='mediumseagreen', edgecolor='black', alpha=0.8)
ax8.set_xlabel('Cluster', fontsize=10)
ax8.set_ylabel('Monetary Media', fontsize=10)
ax8.set_title('Monetary Media por Cluster', fontsize=12, fontweight='bold')
ax8.grid(axis='y', alpha=0.3)
# Añadir valores en las barras
for bar in bars3:
    height = bar.get_height()
    ax8.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}',
            ha='center', va='bottom', fontsize=8)

# Título principal del dashboard
fig.suptitle('DASHBOARD DE SEGMENTACIÓN DE CLIENTES - ANÁLISIS RFM', 
             fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout()
plt.show()

print("\nDashboard generado exitosamente")


# ===========================================================================
# 11) APLICACIÓN DE K-MEANS CON K ÓPTIMO
# ===========================================================================

print("\n" + "="*60)
print("APLICACIÓN DE K-MEANS CON K ÓPTIMO")
print("="*60)

# Puedes elegir el k basado en tu análisis visual o usar el de silueta
# Aquí usaremos el de silueta, pero puedes cambiarlo manualmente
optimal_k = optimal_k_silhouette  # O puedes poner: optimal_k = 4

print(f"Usando k={optimal_k} clusters")

# Apply K-Means clustering with the optimal number of clusters
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

# Calcular el silhouette score final
final_silhouette = silhouette_score(rfm_scaled, rfm['Cluster'])
print(f"Silhouette Score final con k={optimal_k}: {final_silhouette:.4f}")


# ===========================================================================
# 12) PERFILES DE CLUSTERS
# ===========================================================================

print("\n" + "="*60)
print("PERFILES DE CLUSTERS")
print("="*60)

# Examine cluster profiles
cluster_profile = rfm.groupby('Cluster').agg({
    'Recency': 'mean',
    'Frequency': 'mean',
    'Monetary': 'mean',
    'id_usuario': 'count'  # Añadimos el conteo de clientes por cluster
}).round(1)

cluster_profile.rename(columns={'id_usuario': 'Num_Clientes'}, inplace=True)

print("\nPerfiles de Clusters:")
print(cluster_profile)

# Calcular porcentaje de clientes por cluster
cluster_profile['Porcentaje'] = (cluster_profile['Num_Clientes'] / cluster_profile['Num_Clientes'].sum() * 100).round(1)

print("\nDistribución de clientes por cluster:")
print(cluster_profile[['Num_Clientes', 'Porcentaje']])

# ===========================================================================
# 13) ANÁLISIS COMPLETADO
# ===========================================================================

print("\n" + "="*60)
print("ANÁLISIS COMPLETADO")
print("="*60)
print("\nTodos los gráficos han sido consolidados en un dashboard único.")
print(f"Número óptimo de clusters: {optimal_k}")
print(f"Silhouette Score: {final_silhouette:.4f}")
print(f"Total de clientes segmentados: {len(rfm):,}")