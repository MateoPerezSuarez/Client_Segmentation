import pandas as pd
import numpy as np

df = pd.read_csv('../../../data/thelook/procesado/orders_price_client.csv')
df = df.dropna()
df['created_at'] = pd.to_datetime(df['created_at'])
df['month_period'] = df['created_at'].dt.to_period('M')

def calculate_lrfm_metrics(group):
    period = group.name[1]
    month_end = period.to_timestamp(how='E')
    
    f = group['order_id'].nunique() # Frequency
    m = group['sale_price'].sum()    # Monetary
    l = (group['created_at'].max() - group['created_at'].min()).days # Length [cite: 153]
    
    # R' (Recency) corregida: tiempo desde el fin del mes hasta la última compra [cite: 156]
    r_prime = (month_end - group['created_at'].max()).days
    
    return pd.Series({'L': l, 'R_prime': r_prime, 'F': f, 'M': m})

lrfm_monthly = df.groupby(['user_id', 'month_period']).apply(calculate_lrfm_metrics).reset_index()

max_date = df['created_at'].max().to_period('M')
user_series = []

for user, first_m in lrfm_monthly.groupby('user_id')['month_period'].min().items():
    # Generamos todos los meses desde su primera compra hasta el final del dataset
    all_user_months = pd.period_range(start=first_m, end=max_date, freq='M')
    for m in all_user_months:
        user_series.append((user, m))


import pandas as pd
import numpy as np

# --- FASE 1: CREACIÓN DE LA SERIE TEMPORAL PLANA ---
# (Usando tu lógica de ffill para R' y relleno de ceros)

# 1. Rellenamos meses vacíos y calculamos R_prime
full_index = pd.MultiIndex.from_tuples(user_series, names=['user_id', 'month_period'])
df_ts = pd.DataFrame(index=full_index).reset_index()
df_ts = df_ts.merge(lrfm_monthly, on=['user_id', 'month_period'], how='left')

df_ts[['F', 'M', 'L']] = df_ts[['F', 'M', 'L']].fillna(0)

last_dates = df.groupby(['user_id', 'month_period'])['created_at'].max().reset_index()
df_ts = df_ts.merge(last_dates, on=['user_id', 'month_period'], how='left')
df_ts['created_at'] = df_ts.groupby('user_id')['created_at'].ffill()
df_ts['month_end'] = df_ts['month_period'].dt.to_timestamp(how='E')
df_ts['R_prime'] = (df_ts['month_end'] - df_ts['created_at']).dt.days

# Dataset base
final_ts = df_ts[['user_id', 'month_period', 'L', 'R_prime', 'F', 'M']].sort_values(['user_id', 'month_period'])

# --- FASE 2: NORMALIZACIÓN Y PESOS ---

# 2. Normalización Min-Max (Antes de crear las matrices) 
cols_to_norm = ['L', 'R_prime', 'F', 'M']
df_norm = final_ts.copy()

for col in cols_to_norm:
    min_val = df_norm[col].min()
    max_val = df_norm[col].max()
    df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)

# 3. Cálculo de Pesos (W) según la Ec. 16 
deviations = {}
for col in cols_to_norm:
    mean_val = df_norm[col].mean()
    deviations[col] = np.sum(np.abs(df_norm[col] - mean_val))

total_deviation = sum(deviations.values())
weights = {col: dev / total_deviation for col, dev in deviations.items()}
print("Pesos estratégicos (W):", weights)

# --- REPRESENTACIÓN FINAL (MATRICES MTS) ---

# 4. Ahora sí, creamos las matrices a partir de los datos NORMALIZADOS
matrices_clientes = []
user_ids = []

for user_id, group in df_norm.groupby('user_id'):
    # Cada matriz X_i tiene forma (meses, 4 dimensiones) 
    matriz_usuario = group[cols_to_norm].values
    matrices_clientes.append(matriz_usuario)
    user_ids.append(user_id)

print(f"Total de objetos MTS (clientes): {len(matrices_clientes)}")
print(f"Ejemplo de matriz normalizada del primer cliente:\n{matrices_clientes[0][:3]}")









import numpy as np
from tslearn.metrics import dtw as dtw_metric
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import MinMaxScaler

# 1. Función para DTW Multivariante (DTW-D) [cite: 209]
def calculate_dtw_d_matrix(matrices):
    """Calcula la distancia DTW multivariante entre series."""
    # Nota: tslearn maneja matrices (T, dimensions) automáticamente
    n = len(matrices)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = dtw_metric(matrices[i], matrices[j])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d
    return dist_matrix

# 2. Distancia CID (Complexity-Invariant Dissimilarity) [cite: 220]
def calculate_ce(series):
    """Estimador de complejidad de una serie (Eq. 14)."""
    return np.sqrt(np.sum(np.diff(series)**2))

def calculate_cid_dist(x, y):
    """Distancia CID corregida por complejidad (Eq. 12)."""
    ed = euclidean(x, y)
    ce_x = calculate_ce(x)
    ce_y = calculate_ce(y)
    # Factor de corrección CF
    cf = max(ce_x, ce_y) / (min(ce_x, ce_y) + 1e-9)
    return cf * ed

# 3. Lógica para la Matriz de Membresía Difusa (Eq. 19) [cite: 285]
def get_fuzzy_membership(dist_matrix, centers_idx):
    """
    Calcula la membresía difusa f_ij de cada objeto a los centros.
    dist_matrix: Distancias entre todos los objetos.
    centers_idx: Índices de los clientes elegidos como centros (vía DPC).
    """
    n = dist_matrix.shape[0]
    k = len(centers_idx)
    f_matrix = np.zeros((n, k))
    
    for i in range(n):
        for j in range(k):
            # Usamos la fórmula del paper: inv_dist ^ (1/2)
            # sumatoria sobre todos los centros (Eq. 19)
            dist_to_j = dist_matrix[i, centers_idx[j]] + 1e-9
            
            numerator = (1.0 / dist_to_j)**0.5
            denominator = sum([(1.0 / (dist_matrix[i, centers_idx[s]] + 1e-9))**0.5 
                               for s in range(k)])
            
            f_matrix[i, j] = numerator / denominator
    return f_matrix

# 4. Integración según el Algoritmo 2 [cite: 319]
def compute_composite_fuzzy_matrix(matrices, weights, centers_idx, option='dtw_d'):
    """
    Combina las métricas según la opción elegida.
    """
    # Matriz base con DTW-D
    dist_dtw = calculate_dtw_d_matrix(matrices)
    f_dtw = get_fuzzy_membership(dist_dtw, centers_idx)
    
    if option == 'dtw_d':
        return f_dtw
    
    # Si la opción incluye SBD o CID, se calcula por dimensión y se pondera con W
    z = len(weights)
    f_combined_dim = np.zeros_like(f_dtw)
    
    # Ejemplo para cada dimensión l con sus respectivos pesos w_l [cite: 305]
    # (Aquí implementarías la lógica de SBD/CID por columna de la matriz)
    # F_combined = F_dtw + (sum(w_l * F_l) / z)
    
    return f_dtw # Por ahora retornamos la base para validación