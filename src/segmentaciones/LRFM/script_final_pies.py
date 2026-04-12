"""
SEGMENTACIÓN DE CLIENTES CON MODELO LRFMS Y SERIES TEMPORALES
=============================================================

Implementación correcta según el paper:
Wang, S., Sun, L. & Yu, Y. (2024). 
A dynamic customer segmentation approach by combining LRFMS 
and multivariate time series clustering.
Scientific Reports, 14, 17491.

DIFERENCIA CLAVE:
- NO es un análisis estático (un solo valor de LRFMS por cliente)
- SÍ son SERIES TEMPORALES (valores de LRFMS que evolucionan en el tiempo)
- Cada cliente tiene una secuencia de valores L, R', F, M a lo largo de múltiples intervalos
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from pathlib import Path

# Configuración
import os
script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
output_dir = script_dir / 'outputs'
output_dir.mkdir(exist_ok=True)


print("="*80)
print("SEGMENTACIÓN DINÁMICA CON LRFMS Y SERIES TEMPORALES")
print("="*80)
print("""
Este script implementa correctamente el modelo del paper donde:
1. Los datos se dividen en intervalos temporales (ej: cada 2 meses)
2. Para cada cliente y cada intervalo, se calcula LRFMS
3. Cada cliente queda representado como una SERIE TEMPORAL multivariada
4. El clustering se realiza sobre estas series temporales (no sobre valores estáticos)
""")


# ===========================================================================
# 1) CARGAR DATOS
# ===========================================================================
print("\n" + "="*80)
print("1) CARGA DE DATOS")
print("="*80)

try:
    # Intentar cargar el archivo
    df = pd.read_excel("data/online+retail/Online Retail.xlsx")
    print(f"✓ Datos cargados: {df.shape}")
    print(f"  Columnas: {df.columns.tolist()}")
except FileNotFoundError:
    print("⚠ Archivo no encontrado. Por favor verifica la ruta.")
    print("  Esperado: data/online+retail/Online Retail.xlsx")
    exit(1)


# ===========================================================================
# 2) LIMPIEZA BÁSICA
# ===========================================================================
print("\n" + "="*80)
print("2) LIMPIEZA DE DATOS")
print("="*80)

n_inicial = len(df)
print(f"Registros iniciales: {n_inicial:,}")

# Eliminar nulos
df = df.dropna()
print(f"Tras eliminar nulos: {len(df):,} (eliminados: {n_inicial - len(df):,})")

# Eliminar negativos en Quantity y UnitPrice
if 'Quantity' in df.columns and 'UnitPrice' in df.columns:
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    print(f"Tras eliminar negativos: {len(df):,}")

# Crear total_price
if 'Quantity' in df.columns and 'UnitPrice' in df.columns:
    df['total_price'] = df['Quantity'] * df['UnitPrice']
    df = df[df['total_price'] > 0]
    print(f"Tras filtrar total_price > 0: {len(df):,}")


# ===========================================================================
# 3) MAPEO DE COLUMNAS (asumiendo que tienes tu DatasetMapper)
# ===========================================================================
print("\n" + "="*80)
print("3) MAPEO DE COLUMNAS")
print("="*80)

try:
    from seleccionador_columnas import DatasetMapper
    mapper = DatasetMapper()
    df_std = mapper.transform(df, auto_map_threshold=0.55, verbose=True)
    print(f"✓ Columnas mapeadas: {df_std.columns.tolist()}")
except ImportError:
    print("⚠ DatasetMapper no disponible, usando mapeo manual...")
    # Mapeo manual básico para el dataset Online Retail
    df_std = df.rename(columns={
        'CustomerID': 'id_usuario',
        'InvoiceNo': 'id_pedido',
        'InvoiceDate': 'fecha_pedido',
        'total_price': 'total_pedido'
    })
    # Asegurar que fecha_pedido sea datetime
    if not pd.api.types.is_datetime64_any_dtype(df_std['fecha_pedido']):
        df_std['fecha_pedido'] = pd.to_datetime(df_std['fecha_pedido'])

print(f"Columnas finales: {df_std.columns.tolist()}")


# ===========================================================================
# 4) AGREGAR A NIVEL PEDIDO
# ===========================================================================
print("\n" + "="*80)
print("4) AGREGACIÓN A NIVEL PEDIDO")
print("="*80)

df_pedidos = df_std.groupby(
    ["id_usuario", "id_pedido", "fecha_pedido"],
    as_index=False
).agg({"total_pedido": "sum"})

df_pedidos = df_pedidos[df_pedidos["total_pedido"] > 0].copy()
print(f"✓ Pedidos agregados: {df_pedidos.shape}")
print(f"  Clientes únicos: {df_pedidos['id_usuario'].nunique():,}")
print(f"  Pedidos únicos: {df_pedidos['id_pedido'].nunique():,}")


# ===========================================================================
# 5) CONFIGURACIÓN DE INTERVALOS TEMPORALES
# ===========================================================================
print("\n" + "="*80)
print("5) CONFIGURACIÓN DE SERIES TEMPORALES")
print("="*80)

# PARÁMETRO CONFIGURABLE: Intervalo temporal
# '2W' = 2 semanas (como en el paper original)
# '1M' = 1 mes
# '2M' = 2 meses (más apropiado para datasets con menor frecuencia)
TIEMPO_INTERVALO = '2M'  # ← CAMBIA ESTO SEGÚN TUS NECESIDADES

# PARÁMETRO P: número de transacciones recientes para R'
P = 3

print(f"""
CONFIGURACIÓN:
- Intervalo temporal: {TIEMPO_INTERVALO}
- Parámetro P (Recency'): {P}
- Según el paper: "transaction data is aggregated into bins based on a two-week time interval"
- Aquí usamos {TIEMPO_INTERVALO} por conveniencia (puedes cambiar a '2W' si tienes suficientes datos)
""")

# Obtener rango de fechas
fecha_min = df_pedidos["fecha_pedido"].min()
fecha_max = df_pedidos["fecha_pedido"].max()

print(f"Rango de fechas:")
print(f"  Desde: {fecha_min}")
print(f"  Hasta: {fecha_max}")
print(f"  Duración: {(fecha_max - fecha_min).days} días")

# Crear bins temporales
bins_temporales = pd.date_range(
    start=fecha_min,
    end=fecha_max + pd.Timedelta(days=1),
    freq=TIEMPO_INTERVALO
)

n_intervalos = len(bins_temporales) - 1
print(f"\n✓ Intervalos temporales creados: {n_intervalos}")
print(f"  Primeros bins: {bins_temporales[:3].tolist()}")
print(f"  Últimos bins: {bins_temporales[-2:].tolist()}")

# Asignar cada pedido a un intervalo
df_pedidos["intervalo"] = pd.cut(
    df_pedidos["fecha_pedido"],
    bins=bins_temporales,
    labels=range(n_intervalos),
    include_lowest=True
)

# Eliminar pedidos sin intervalo asignado
df_pedidos = df_pedidos.dropna(subset=["intervalo"])
df_pedidos["intervalo"] = df_pedidos["intervalo"].astype(int)

print(f"  Pedidos con intervalo asignado: {len(df_pedidos):,}")


# ===========================================================================
# 6) FUNCIÓN PARA CALCULAR LRFMS POR INTERVALO
# ===========================================================================

def calcular_lrfms_intervalo(grupo, fecha_fin_intervalo, p_value):
    """
    Calcula LRFMS para un cliente en UN intervalo temporal.
    
    Parámetros:
    -----------
    grupo : DataFrame
        Pedidos del cliente en ese intervalo específico
    fecha_fin_intervalo : datetime
        Fecha de fin del intervalo
    p_value : int
        Número de transacciones recientes para R'
    
    Retorna:
    --------
    Series con Length, Recency_Prime, Frequency, Monetary
    """
    if len(grupo) == 0:
        return pd.Series({
            'Length': 0,
            'Recency_Prime': np.nan,
            'Frequency': 0,
            'Monetary': 0
        })
    
    fechas_ordenadas = grupo["fecha_pedido"].sort_values()
    
    # Length: tiempo entre primera y última transacción en ESTE intervalo
    if len(fechas_ordenadas) > 1:
        length = (fechas_ordenadas.iloc[-1] - fechas_ordenadas.iloc[0]).days
    else:
        length = 0
    
    # Recency': promedio desde fin de intervalo hasta últimas P transacciones
    p_actual = min(p_value, len(fechas_ordenadas))
    ultimas_p = fechas_ordenadas.tail(p_actual)
    recency_prime = sum((fecha_fin_intervalo - fecha).days for fecha in ultimas_p) / p_actual
    
    # Frequency: número de pedidos
    frequency = len(grupo)
    
    # Monetary: suma total
    monetary = grupo["total_pedido"].sum()
    
    return pd.Series({
        'Length': length,
        'Recency_Prime': recency_prime,
        'Frequency': frequency,
        'Monetary': monetary
    })


# ===========================================================================
# 7) CALCULAR SERIES TEMPORALES PARA TODOS LOS CLIENTES
# ===========================================================================
print("\n" + "="*80)
print("6) CÁLCULO DE SERIES TEMPORALES LRFMS")
print("="*80)

lrfms_series_list = []
clientes_unicos = df_pedidos["id_usuario"].unique()
total_clientes = len(clientes_unicos)

print(f"Procesando {total_clientes:,} clientes...")
print("(Esto puede tardar un momento...)\n")

for idx, cliente_id in enumerate(clientes_unicos):
    if (idx + 1) % 500 == 0 or (idx + 1) == total_clientes:
        print(f"  Procesados: {idx + 1:,}/{total_clientes:,} clientes ({100*(idx+1)/total_clientes:.1f}%)")
    
    pedidos_cliente = df_pedidos[df_pedidos["id_usuario"] == cliente_id]
    
    # Para cada intervalo temporal
    for intervalo_idx in range(n_intervalos):
        pedidos_intervalo = pedidos_cliente[pedidos_cliente["intervalo"] == intervalo_idx]
        
        fecha_inicio = bins_temporales[intervalo_idx]
        fecha_fin = bins_temporales[intervalo_idx + 1]
        
        lrfms_vals = calcular_lrfms_intervalo(pedidos_intervalo, fecha_fin, P)
        
        lrfms_series_list.append({
            'id_usuario': cliente_id,
            'intervalo': intervalo_idx,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'Length': lrfms_vals['Length'],
            'Recency_Prime': lrfms_vals['Recency_Prime'],
            'Frequency': lrfms_vals['Frequency'],
            'Monetary': lrfms_vals['Monetary']
        })

# Convertir a DataFrame
lrfms_series = pd.DataFrame(lrfms_series_list)

print(f"\n✓ SERIES TEMPORALES GENERADAS")
print(f"  Total de puntos temporales: {len(lrfms_series):,}")
print(f"  Clientes: {lrfms_series['id_usuario'].nunique():,}")
print(f"  Intervalos por cliente: {n_intervalos}")

print("\nPrimeras filas de las series temporales:")
print(lrfms_series.head(15))

print("\nEstadísticas descriptivas:")
print(lrfms_series[['Length', 'Recency_Prime', 'Frequency', 'Monetary']].describe())


# ===========================================================================
# 8) VISUALIZACIÓN: CLIENTE ALEATORIO
# ===========================================================================
print("\n" + "="*80)
print("7) VISUALIZACIÓN DE SERIE TEMPORAL - CLIENTE EJEMPLO")
print("="*80)

# Seleccionar un cliente con actividad significativa
clientes_activos = lrfms_series.groupby('id_usuario')['Frequency'].sum()
clientes_con_actividad = clientes_activos[clientes_activos >= 5].index.tolist()

if len(clientes_con_actividad) == 0:
    # Si no hay clientes con mucha actividad, usar todos
    clientes_con_actividad = lrfms_series['id_usuario'].unique().tolist()

cliente_ejemplo = np.random.choice(clientes_con_actividad)
datos_cliente = lrfms_series[lrfms_series['id_usuario'] == cliente_ejemplo].copy()

print(f"\nCliente seleccionado: {cliente_ejemplo}")
print(f"Intervalos con datos: {len(datos_cliente)}")
print(f"Actividad total:")
print(f"  - Length máximo: {datos_cliente['Length'].max():.0f} días")
print(f"  - Frecuencia total: {datos_cliente['Frequency'].sum():.0f} pedidos")
print(f"  - Gasto total: ${datos_cliente['Monetary'].sum():,.2f}")

# Crear visualización
fig, axes = plt.subplots(2, 2, figsize=(18, 11))
fig.suptitle(
    f'Serie Temporal LRFMS - Cliente {cliente_ejemplo}\n'
    f'Intervalos de {TIEMPO_INTERVALO} | Total: {n_intervalos} periodos',
    fontsize=15, fontweight='bold', y=0.995
)

# Preparar eje X
x_values = range(len(datos_cliente))
x_labels = datos_cliente['fecha_inicio'].dt.strftime('%Y-%m').tolist()

# 1) Length
ax1 = axes[0, 0]
ax1.plot(x_values, datos_cliente['Length'], marker='o', linewidth=2.5, 
         markersize=7, color='purple', label='Length')
ax1.fill_between(x_values, datos_cliente['Length'], alpha=0.25, color='purple')
ax1.set_xlabel('Intervalo Temporal', fontsize=11, fontweight='bold')
ax1.set_ylabel('Length (días)', fontsize=11, fontweight='bold')
ax1.set_title('(A) Length - Lealtad del Cliente\nTiempo entre 1ª y última compra por periodo', 
              fontsize=12, fontweight='bold', pad=10)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_xticks(x_values[::max(1, len(x_values)//8)])
ax1.set_xticklabels(x_labels[::max(1, len(x_labels)//8)], rotation=45, ha='right')

# 2) Recency'
ax2 = axes[0, 1]
recency_plot = datos_cliente['Recency_Prime'].fillna(0)
ax2.plot(x_values, recency_plot, marker='s', linewidth=2.5, 
         markersize=7, color='steelblue', label="Recency'")
ax2.fill_between(x_values, recency_plot, alpha=0.25, color='steelblue')
ax2.set_xlabel('Intervalo Temporal', fontsize=11, fontweight='bold')
ax2.set_ylabel("Recency' (días)", fontsize=11, fontweight='bold')
ax2.set_title("(B) Recency' - Actividad Reciente\nPromedio desde últimas P={} compras".format(P), 
              fontsize=12, fontweight='bold', pad=10)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_xticks(x_values[::max(1, len(x_values)//8)])
ax2.set_xticklabels(x_labels[::max(1, len(x_labels)//8)], rotation=45, ha='right')

# 3) Frequency
ax3 = axes[1, 0]
ax3.plot(x_values, datos_cliente['Frequency'], marker='^', linewidth=2.5, 
         markersize=7, color='coral', label='Frequency')
ax3.fill_between(x_values, datos_cliente['Frequency'], alpha=0.25, color='coral')
ax3.set_xlabel('Intervalo Temporal', fontsize=11, fontweight='bold')
ax3.set_ylabel('Frequency (# pedidos)', fontsize=11, fontweight='bold')
ax3.set_title('(C) Frequency - Número de Transacciones\nActividad de compra por periodo', 
              fontsize=12, fontweight='bold', pad=10)
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_xticks(x_values[::max(1, len(x_values)//8)])
ax3.set_xticklabels(x_labels[::max(1, len(x_labels)//8)], rotation=45, ha='right')

# 4) Monetary
ax4 = axes[1, 1]
ax4.plot(x_values, datos_cliente['Monetary'], marker='D', linewidth=2.5, 
         markersize=7, color='mediumseagreen', label='Monetary')
ax4.fill_between(x_values, datos_cliente['Monetary'], alpha=0.25, color='mediumseagreen')
ax4.set_xlabel('Intervalo Temporal', fontsize=11, fontweight='bold')
ax4.set_ylabel('Monetary (valor)', fontsize=11, fontweight='bold')
ax4.set_title('(D) Monetary - Gasto Total\nValor monetario por periodo', 
              fontsize=12, fontweight='bold', pad=10)
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.set_xticks(x_values[::max(1, len(x_values)//8)])
ax4.set_xticklabels(x_labels[::max(1, len(x_labels)//8)], rotation=45, ha='right')

plt.tight_layout()

# Guardar
plot_path = output_dir / 'serie_temporal_lrfms_cliente_ejemplo.png'
plt.savefig(plot_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"\n✓ Gráfico guardado en: {plot_path}")

plt.show()

print("\n" + "-"*80)
print("DATOS DEL CLIENTE EJEMPLO:")
print("-"*80)
print(datos_cliente[['intervalo', 'fecha_inicio', 'fecha_fin', 
                      'Length', 'Recency_Prime', 'Frequency', 'Monetary']].to_string())


# ===========================================================================
# 9) GUARDAR SERIES TEMPORALES
# ===========================================================================
print("\n" + "="*80)
print("8) GUARDANDO RESULTADOS")
print("="*80)

# Guardar series temporales completas
series_path = output_dir / 'lrfms_series_temporales.csv'
lrfms_series.to_csv(series_path, index=False, encoding='utf-8-sig')
print(f"✓ Series temporales guardadas en: {series_path}")

# Guardar resumen
resumen_path = output_dir / 'resumen_series_temporales.txt'
with open(resumen_path, 'w', encoding='utf-8') as f:
    f.write("RESUMEN - SERIES TEMPORALES LRFMS\n")
    f.write("="*80 + "\n\n")
    f.write(f"Intervalo temporal: {TIEMPO_INTERVALO}\n")
    f.write(f"Parámetro P (Recency'): {P}\n")
    f.write(f"Total clientes: {lrfms_series['id_usuario'].nunique():,}\n")
    f.write(f"Número de intervalos: {n_intervalos}\n")
    f.write(f"Total puntos temporales: {len(lrfms_series):,}\n")
    f.write(f"Rango de fechas: {fecha_min} a {fecha_max}\n\n")
    f.write("Estadísticas descriptivas:\n")
    f.write("-"*80 + "\n")
    f.write(lrfms_series[['Length', 'Recency_Prime', 'Frequency', 'Monetary']].describe().to_string())

print(f"✓ Resumen guardado en: {resumen_path}")


# ===========================================================================
# 10) PREPARAR DATOS PARA CLUSTERING MULTIVARIADO
# ===========================================================================
print("\n" + "="*80)
print("9) PREPARACIÓN PARA CLUSTERING MULTIVARIADO")
print("="*80)

print("""
Las series temporales se pueden organizar como una matriz 3D:
  Dimensión 1: Clientes (n_clientes)
  Dimensión 2: Tiempo (n_intervalos)  
  Dimensión 3: Features (4: Length, Recency', Frequency, Monetary)

Esto permite aplicar clustering de series temporales multivariadas.
""")

# Crear pivots
metrics = ['Length', 'Recency_Prime', 'Frequency', 'Monetary']
matrices = {}

for metric in metrics:
    matriz = lrfms_series.pivot(
        index='id_usuario',
        columns='intervalo',
        values=metric
    ).fillna(0)  # Intervalos sin actividad = 0
    matrices[metric] = matriz

# Obtener orden de clientes
clientes_idx = matrices['Length'].index

# Crear matriz 3D
n_clientes = len(clientes_idx)
n_intervalos_real = matrices['Length'].shape[1]
n_features = len(metrics)

matriz_3d = np.zeros((n_clientes, n_intervalos_real, n_features))

for i, metric in enumerate(metrics):
    matriz_3d[:, :, i] = matrices[metric].values

print(f"✓ Matriz 3D creada:")
print(f"  Shape: {matriz_3d.shape}")
print(f"  ({n_clientes} clientes, {n_intervalos_real} intervalos, {n_features} features)")

# Guardar matriz para clustering posterior
matriz_path = output_dir / 'matriz_3d_lrfms.npy'
np.save(matriz_path, matriz_3d)
print(f"\n✓ Matriz 3D guardada en: {matriz_path}")

# Guardar índice de clientes
clientes_path = output_dir / 'clientes_indice.csv'
pd.DataFrame({'id_usuario': clientes_idx}).to_csv(clientes_path, index=False)
print(f"✓ Índice de clientes guardado en: {clientes_path}")


# ===========================================================================
# FINALIZACIÓN
# ===========================================================================
print("\n" + "="*80)
print("✓ PROCESO COMPLETADO EXITOSAMENTE")
print("="*80)

print(f"""
ARCHIVOS GENERADOS en {output_dir}:
1. serie_temporal_lrfms_cliente_ejemplo.png - Visualización de ejemplo
2. lrfms_series_temporales.csv - Serie temporal completa de todos los clientes
3. resumen_series_temporales.txt - Resumen estadístico
4. matriz_3d_lrfms.npy - Matriz 3D para clustering
5. clientes_indice.csv - Índice de clientes

PRÓXIMOS PASOS:
1. Revisar la visualización del cliente ejemplo
2. Analizar las series temporales generadas
3. Aplicar algoritmos de clustering multivariado (DTW-D, SBD, CID)
4. Interpretar los clusters resultantes

NOTA IMPORTANTE:
Este enfoque es diferente del RFM tradicional:
- RFM tradicional: 1 valor por cliente (estático)
- LRFMS con series temporales: N valores por cliente (dinámico)
- Permite capturar la EVOLUCIÓN del comportamiento del cliente
""")