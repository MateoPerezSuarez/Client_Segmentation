"""Script para tratar el input estandar de datos:

1- Leer el input, con pandas tradicional.
2- Ajustar por valores de similitud, palabras parecidas,.... Las columnas que queremos para el modelo de datos.
    2.1- Modelo de datos -> campos requeridos para hacer el analisis:
        2.1.1 - CustomerID(Id del cliente)
        2.1.2 - InvoiceDate(Fecha de la compra)
        2.1.3 - InvoiceID(Id de la compra)
        2.1.4 - Amount(Total de la compra) -> para este mirar como tratar otros datasets y juntarlos para evitar procesos.
"""""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from datetime import datetime


class DatasetMapper:
    """
    Mapea automáticamente columnas de un dataset a un esquema objetivo
    usando similitud de texto y validación de tipos de datos.
    """
    
    def __init__(self):
        # Modelo de datos objetivo para segmentación de clientes
        self.target_schema = {
            'id_usuario': {
                'type': 'string',
                'aliases': ['user_id', 'usuario', 'cliente', 'customer_id', 
                           'client_id', 'user', 'cliente_id', 'id_cliente']
            },
            'id_pedido': {
                'type': 'string',
                'aliases': ['order_id', 'pedido', 'orden', 'order', 
                           'num_pedido', 'numero_pedido', 'id_orden','invoice_id']
            },
            'total_pedido': {
                'type': 'number',
                'aliases': ['total', 'amount', 'importe', 'total_price', 'totalprice',
                           'monto', 'valor', 'total_order', 'importe_total', 'total_amount',
                           'order_total', 'order_amount', 'invoice_total', 'grand_total','precio_total']
            },
            'fecha_pedido': {
                'type': 'date',
                'aliases': ['fecha', 'date', 'created_at', 'order_date', 
                           'fecha_orden', 'timestamp', 'fecha_creacion']
            }
        }
    
    def _calculate_similarity(self, str1, str2):
        """Calcula similitud entre dos strings"""
        str1 = str1.lower().replace('_', '').replace('-', '').replace(' ', '')
        str2 = str2.lower().replace('_', '').replace('-', '').replace(' ', '')
        
        # Coincidencia exacta
        if str1 == str2:
            return 1.0
        
        # Contiene
        if str1 in str2 or str2 in str1:
            return 0.85
        
        # Similitud de secuencia
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _validate_type(self, series, expected_type):
        """Valida que una serie coincida con el tipo esperado"""
        if len(series) == 0:
            return 0.5
        
        # Tomar muestra de valores no nulos
        sample = series.dropna().head(10)
        if len(sample) == 0:
            return 0.5
        
        valid_count = 0
        
        for value in sample:
            if expected_type == 'number':
                try:
                    float(value)
                    valid_count += 1
                except (ValueError, TypeError):
                    pass
            
            elif expected_type == 'date':
                if self._is_date(value):
                    valid_count += 1
            
            elif expected_type == 'string':
                if isinstance(value, (str, int, float)):
                    valid_count += 1
        
        return valid_count / len(sample)
    
    def _is_date(self, value):
        """Verifica si un valor es una fecha"""
        if pd.isna(value):
            return False
        
        # Si ya es datetime
        if isinstance(value, (pd.Timestamp, datetime)):
            return True
        
        # Intentar parsear como fecha
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def auto_map(self, df, confidence_threshold=0.5):
        """
        Mapea automáticamente las columnas del dataframe al esquema objetivo
        
        Args:
            df: DataFrame a mapear
            confidence_threshold: Umbral mínimo de confianza (0-1)
        
        Returns:
            dict: Mapeo {columna_objetivo: columna_original}
        """
        # Primero calculamos todos los scores posibles
        all_scores = {}
        
        for target_col, config in self.target_schema.items():
            all_scores[target_col] = {}
            
            for source_col in df.columns:
                # Calcular similitud con el nombre objetivo
                score = self._calculate_similarity(source_col, target_col)
                
                # Calcular similitud con aliases
                for alias in config['aliases']:
                    alias_score = self._calculate_similarity(source_col, alias)
                    score = max(score, alias_score)
                
                # Validar tipo de dato
                type_validity = self._validate_type(df[source_col], config['type'])
                
                # Score final ponderado
                final_score = score * 0.7 + type_validity * 0.3
                
                if final_score >= confidence_threshold:
                    all_scores[target_col][source_col] = final_score
        
        # Asignar columnas evitando duplicados (cada columna solo se asigna una vez)
        mapping = {}
        confidence_scores = {}
        used_columns = set()
        
        # Ordenar por mejor score para asignar primero los matches más seguros
        candidates = []
        for target_col, scores in all_scores.items():
            for source_col, score in scores.items():
                candidates.append((score, target_col, source_col))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        # Asignar columnas de mayor a menor confianza
        for score, target_col, source_col in candidates:
            # Solo asignar si la columna fuente no ha sido usada y el target no tiene asignación
            if source_col not in used_columns and target_col not in mapping:
                mapping[target_col] = source_col
                confidence_scores[target_col] = score
                used_columns.add(source_col)
        
        return mapping, confidence_scores
    
    def transform(self, df, mapping=None, auto_map_threshold=0.5):
        """
        Transforma el dataframe al esquema objetivo
        
        Args:
            df: DataFrame a transformar
            mapping: Mapeo manual opcional {col_objetivo: col_original}
            auto_map_threshold: Umbral para mapeo automático si no se provee mapping
        
        Returns:
            DataFrame transformado con las columnas objetivo
        """
        if mapping is None:
            mapping, scores = self.auto_map(df, auto_map_threshold)
            print("Mapeo automático:")
            for target, source in mapping.items():
                print(f"  {target} <- {source} (confianza: {scores[target]:.2f})")
        
        # Verificar columnas faltantes
        missing = set(self.target_schema.keys()) - set(mapping.keys())
        if missing:
            print(f"\n⚠️ Advertencia: Columnas no mapeadas: {missing}")
        
        # Crear nuevo dataframe con columnas mapeadas
        result = pd.DataFrame()
        
        for target_col, source_col in mapping.items():
            result[target_col] = df[source_col].copy()
            
            # Convertir tipos
            expected_type = self.target_schema[target_col]['type']
            
            if expected_type == 'number':
                result[target_col] = pd.to_numeric(result[target_col], errors='coerce')
            elif expected_type == 'date':
                result[target_col] = pd.to_datetime(result[target_col], errors='coerce')
            elif expected_type == 'string':
                result[target_col] = result[target_col].astype(str)
        
        return result
