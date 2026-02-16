import pandas as pd
import matplotlib.pyplot as plt
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
print("PLOT: primeras 5 filas (tabla)")
print("-"*60)

# Plot como tabla (rápido y claro para scripts)
head5 = df.head(5)

fig, ax = plt.subplots(figsize=(12, 2.5))
ax.axis("off")
table = ax.table(
    cellText=head5.values,
    colLabels=head5.columns,
    loc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.2)
plt.tight_layout()
plt.show()

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
print("PLOT ÚLTIMA COMPRA (OPCIONAL)")
print("="*60)

promedio_ultima_compra = df_std["fecha_pedido"].max() - pd.to_timedelta(rfm["Recency"].mean(), unit="D")

plt.figure(figsize=(8, 5))
plt.axvline(promedio_ultima_compra, color="r", linestyle="--", label="Promedio Última Compra")

ultimas_fechas = df_pedidos.groupby("id_usuario")["fecha_pedido"].max()
plt.hist(ultimas_fechas, bins=30, edgecolor="black")

plt.title("Distribución de la Fecha de la Última Compra")
plt.xlabel("Fecha de la Última Compra")
plt.ylabel("Número de Clientes")
plt.legend()
plt.tight_layout()
plt.show()


# =========================
# 7) SCORES RFM + SEGMENTACIÓN
# =========================

print("\n" + "="*60)
print("SCORES RFM + SEGMENTACIÓN")
print("="*60)

def rfm_quantiles(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    - Recency -> 5 = más reciente, 1 = menos reciente
    - Frequency -> 5 = más frecuente, 1 = menos frecuente
    - Monetary -> 5 = mayor gasto, 1 = menor gasto
    """
    dfq = dataframe.copy()
    dfq["Recency_score"] = pd.qcut(dfq["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    dfq["Frequency_score"] = pd.qcut(dfq["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    dfq["Monetary_score"] = pd.qcut(dfq["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    dfq["RFM_Score"] = (
        dfq["Recency_score"].astype(str)
        + dfq["Frequency_score"].astype(str)
        + dfq["Monetary_score"].astype(str)
    )
    return dfq

rfm = rfm_quantiles(rfm)

mapa_segmentos = {
    r"[4-5][4-5][4-5]": "Champions",
    r"[2-3][4-5][4-5]": "Loyal Customers",
    r"[4-5][2-5][4-5]": "Potential Loyalists",
    r"[4-5][2-5][1-3]": "Recent Customers",
    r"[2-3][2-3][4-5]": "Ocasional Customers",
    r"[2-4][1-5][1-4]": "Potential Customers",
    r"[2-3][4-5][2-3]": "Economic Loyalists",
    r"[1][4-5][4-5]": "Risky Customers",
    r"[1-2][1-3][4-5]": "Nearly Lost",
    r"[1-2][4-5][1-3]": "Need Attention",
    r"[3-4][1-3][1-3]": "Average Customers",
    r"[1-3][1-3][1-3]": "Non active",
    r"[1-3][1-3][1-2]": "Sleeping",
    r"[4-5][1][1-5]": "New Customers",
    r"[1][1][1]": "Lost",
}

rfm["Segmento"] = rfm["RFM_Score"].replace(mapa_segmentos, regex=True)

print("\nRFM con segmentos (5 primeras filas):")
print(rfm.head(5))

print("\nConteo de segmentos:")
print(rfm["Segmento"].value_counts())

# =========================
# 8) TREEMAP – DISTRIBUCIÓN DE SEGMENTOS
# =========================

print("\n" + "="*60)
print("TREEMAP – DISTRIBUCIÓN DE SEGMENTOS RFM")
print("="*60)

try:
    import squarify

    # Conteo de segmentos
    segment_counts = rfm["Segmento"].value_counts()

    print("\nConteo de segmentos:")
    print(segment_counts)

    plt.figure(figsize=(10, 6))

    squarify.plot(
        sizes=segment_counts.values,
        label=[
            f"{seg}\n{val}"
            for seg, val in zip(segment_counts.index, segment_counts.values)
        ],
        pad=True
    )

    plt.axis("off")
    plt.title("Distribución de Segmentos RFM")
    plt.tight_layout()
    plt.show()

except ImportError:
    print("\n⚠️ No se pudo importar 'squarify'")
    print("Instálalo con: pip install squarify")



