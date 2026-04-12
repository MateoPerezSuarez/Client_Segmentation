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
        # Esquema objetivo — añade o edita columnas aquí
        self.target_schema = {
            'id_usuario': {
                'type': 'string',
                'aliases': [
                    'user_id', 'usuario', 'cliente', 'customer_id',
                    'client_id', 'user', 'cliente_id', 'id_cliente',
                    'userid', 'customerid', 'clientid'
                ]
            },
            'id_pedido': {
                'type': 'string',
                'aliases': [
                    'order_id', 'pedido', 'orden', 'order',
                    'num_pedido', 'numero_pedido', 'id_orden',
                    'orderid', 'order_number', 'numero_orden'
                ]
            },
            'total_pedido': {
                'type': 'number',
                'aliases': [
                    'total', 'amount', 'importe', 'total_price', 'totalprice',
                    'monto', 'valor', 'total_order', 'importe_total', 'total_amount',
                    'order_total', 'order_amount', 'invoice_total', 'grand_total',
                    'precio_total', 'price', 'precio', 'subtotal'
                ]
            },
            'fecha_pedido': {
                'type': 'date',
                'aliases': [
                    'fecha', 'date', 'created_at', 'order_date',
                    'fecha_orden', 'timestamp', 'fecha_creacion',
                    'purchase_date', 'fecha_compra', 'order_timestamp',
                    'created_date', 'fecha_registro'
                ]
            },
            # ─── AÑADE AQUÍ TU QUINTA COLUMNA ───────────────────────────────
            # 'nombre_columna': {
            #     'type': 'string',   # 'string' | 'number' | 'date'
            #     'aliases': ['alias1', 'alias2', ...]
            # },
            # ────────────────────────────────────────────────────────────────
        }

    # ──────────────────────────────────────────────────────────────────────────
    # INTERNALS
    # ──────────────────────────────────────────────────────────────────────────

    def _normalize(self, text: str) -> str:
        """Normaliza un string eliminando separadores y pasando a minúsculas."""
        return text.lower().replace('_', '').replace('-', '').replace(' ', '')

    def _calculate_similarity(self, col_name: str, reference: str) -> float:
        """
        Calcula similitud entre el nombre de una columna y una referencia.
        Devuelve un score entre 0 y 1.
        """
        a = self._normalize(col_name)
        b = self._normalize(reference)

        if a == b:
            return 1.0
        if a in b or b in a:
            return 0.85
        return SequenceMatcher(None, a, b).ratio()

    def _best_name_score(self, col_name: str, target_col: str, aliases: list) -> float:
        """Devuelve el mejor score de nombre entre el target y todos sus aliases."""
        score = self._calculate_similarity(col_name, target_col)
        for alias in aliases:
            score = max(score, self._calculate_similarity(col_name, alias))
        return score

    @staticmethod
    def _is_date_value(value) -> bool:
        """Comprueba si un valor individual puede interpretarse como fecha."""
        if pd.isna(value):
            return False
        if isinstance(value, (pd.Timestamp, datetime)):
            return True
        try:
            pd.to_datetime(value)
            return True
        except Exception:
            return False

    def _validate_type(self, series: pd.Series, expected_type: str) -> float:
        """
        Valida qué porcentaje de los valores de la serie son del tipo esperado.
        Devuelve un score entre 0 y 1.
        """
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return 0.5  # No podemos saber, damos beneficio de la duda

        hits = 0
        for value in sample:
            if expected_type == 'number':
                try:
                    float(value)
                    hits += 1
                except (ValueError, TypeError):
                    pass
            elif expected_type == 'date':
                if self._is_date_value(value):
                    hits += 1
            elif expected_type == 'string':
                # Casi cualquier cosa puede ser string, pero penalizamos
                # columnas que son puramente numéricas
                if isinstance(value, str):
                    hits += 1
                elif isinstance(value, (int, float)):
                    # Los IDs pueden ser numéricos; los contamos igual
                    hits += 1

        return hits / len(sample)

    # ──────────────────────────────────────────────────────────────────────────
    # MAPEO
    # ──────────────────────────────────────────────────────────────────────────

    def auto_map(self, df: pd.DataFrame, confidence_threshold: float = 0.5):
        """
        Mapea automáticamente las columnas del DataFrame al esquema objetivo.

        Devuelve:
            mapping          — dict {col_objetivo: col_original}
            confidence_scores — dict {col_objetivo: score}
        """
        # 1. Calcular score para cada par (target, source)
        all_scores: dict[str, dict[str, float]] = {}

        for target_col, config in self.target_schema.items():
            all_scores[target_col] = {}
            for source_col in df.columns:
                name_score = self._best_name_score(
                    source_col, target_col, config['aliases']
                )
                type_score = self._validate_type(df[source_col], config['type'])

                # Ponderación: nombre tiene más peso que tipo
                final_score = name_score * 0.7 + type_score * 0.3

                if final_score >= confidence_threshold:
                    all_scores[target_col][source_col] = final_score

        # 2. Resolver asignación sin duplicados (greedy por score descendente)
        candidates = [
            (score, target_col, source_col)
            for target_col, scores in all_scores.items()
            for source_col, score in scores.items()
        ]
        candidates.sort(reverse=True, key=lambda x: x[0])

        mapping: dict[str, str] = {}
        confidence_scores: dict[str, float] = {}
        used_columns: set[str] = set()

        for score, target_col, source_col in candidates:
            if source_col not in used_columns and target_col not in mapping:
                mapping[target_col] = source_col
                confidence_scores[target_col] = score
                used_columns.add(source_col)

        return mapping, confidence_scores

    def print_mapping_report(self, mapping: dict, scores: dict):
        """Imprime un resumen del mapeo realizado."""
        print("\n" + "=" * 50)
        print("  INFORME DE MAPEO")
        print("=" * 50)

        all_targets = set(self.target_schema.keys())
        mapped = set(mapping.keys())
        missing = all_targets - mapped

        for target_col, source_col in mapping.items():
            score = scores[target_col]
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            tag = "✅" if score >= 0.7 else "⚠️ "
            print(f"  {tag} {target_col:<20} ← {source_col:<25} [{bar}] {score:.0%}")

        if missing:
            print()
            for col in missing:
                print(f"  ❌ {col:<20} ← (no encontrada)")

        print("=" * 50 + "\n")

    # ──────────────────────────────────────────────────────────────────────────
    # TRANSFORMACIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def transform(
        self,
        df: pd.DataFrame,
        mapping: dict = None,
        auto_map_threshold: float = 0.5,
        verbose: bool = True
    ) -> pd.DataFrame:

        if mapping is None:
            mapping, scores = self.auto_map(df, auto_map_threshold)
            if verbose:
                self.print_mapping_report(mapping, scores)
        else:
            # Calcular scores SOLO para lo que hayas pasado en mapping manual
            scores = {}
            for target_col, source_col in mapping.items():
                if source_col not in df.columns or target_col not in self.target_schema:
                    scores[target_col] = 0.0
                    continue

                cfg = self.target_schema[target_col]
                name_score = self._best_name_score(source_col, target_col, cfg["aliases"])
                type_score = self._validate_type(df[source_col], cfg["type"])
                scores[target_col] = name_score * 0.7 + type_score * 0.3

            if verbose:
                self.print_mapping_report(mapping, scores)

        # Construir DataFrame resultado (conserva índice)
        result = pd.DataFrame(index=df.index)

        for target_col, source_col in mapping.items():
            if source_col not in df.columns:
                print(f"  ⚠️  '{source_col}' no existe en el DataFrame — se omite")
                continue
            if target_col not in self.target_schema:
                print(f"  ⚠️  '{target_col}' no está en target_schema — se omite")
                continue

            result[target_col] = df[source_col].copy()
            expected_type = self.target_schema[target_col]['type']

            if expected_type == 'number':
                result[target_col] = pd.to_numeric(result[target_col], errors='coerce')
            elif expected_type == 'date':
                result[target_col] = pd.to_datetime(result[target_col], errors='coerce')
            elif expected_type == 'string':
                result[target_col] = result[target_col].astype(str)

        return result