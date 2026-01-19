import pandas as pd
import numpy as np
from typing import Dict, Optional, List
# from modelo_datos import MODELO_DATOS  # Descomentar cuando uses archivos separados


class EstandarizadorDatos:
    """
    Clase para estandarizar datasets de clientes a un modelo de datos común.
    Permite mapear columnas con diferentes nombres y validar tipos de datos.
    """
    
    def __init__(self, modelo_datos: Dict):
        """
        Inicializa el estandarizador con el modelo de datos.
        
        Args:
            modelo_datos: Diccionario con la definición del modelo de datos
        """
        self.modelo_datos = modelo_datos
        self.validacion_report = {}
    
    def estandarizar_dataset(self, 
                            df: pd.DataFrame, 
                            mapeo_columnas: Dict,
                            validar: bool = True) -> pd.DataFrame:
        """
        Estandariza un dataset según el mapeo de columnas proporcionado.
        
        Args:
            df: DataFrame original del cliente
            mapeo_columnas: Diccionario {nombre_estandar: nombre_columna_cliente}
            validar: Si True, valida el dataset estandarizado
            
        Returns:
            DataFrame estandarizado
        """
        print("=" * 60)
        print("INICIANDO ESTANDARIZACIÓN DE DATOS")
        print("=" * 60)
        
        # 1. Verificar columnas necesarias
        self._verificar_columnas_necesarias(df, mapeo_columnas)
        
        # 2. Renombrar columnas según mapeo
        df_estandarizado = self._renombrar_columnas(df, mapeo_columnas)
        
        # 3. Convertir tipos de datos
        df_estandarizado = self._convertir_tipos(df_estandarizado)
        
        # 4. Validar datos si se solicita
        if validar:
            self._validar_datos(df_estandarizado)
        
        print("\n✓ Estandarización completada exitosamente")
        print(f"✓ Registros procesados: {len(df_estandarizado)}")
        
        return df_estandarizado
    
    def _verificar_columnas_necesarias(self, df: pd.DataFrame, mapeo: Dict):
        """Verifica que todas las columnas requeridas estén en el mapeo."""
        print("\n1. Verificando columnas requeridas...")
        
        columnas_requeridas = [
            col for col, config in self.modelo_datos.items() 
            if config.get("required", False)
        ]
        
        columnas_faltantes = []
        for col_estandar in columnas_requeridas:
            if col_estandar not in mapeo:
                columnas_faltantes.append(col_estandar)
            elif mapeo[col_estandar] not in df.columns:
                columnas_faltantes.append(f"{col_estandar} (mapeada como '{mapeo[col_estandar]}')")
        
        if columnas_faltantes:
            raise ValueError(f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
        
        print(f"   ✓ Todas las columnas requeridas están presentes")
    
    def _renombrar_columnas(self, df: pd.DataFrame, mapeo: Dict) -> pd.DataFrame:
        """Renombra las columnas según el mapeo proporcionado."""
        print("\n2. Renombrando columnas...")
        
        # Invertir el mapeo para usar con rename
        mapeo_invertido = {v: k for k, v in mapeo.items()}
        
        # Seleccionar solo las columnas que están en el mapeo
        columnas_a_mantener = list(mapeo.values())
        df_filtrado = df[columnas_a_mantener].copy()
        
        # Renombrar
        df_renombrado = df_filtrado.rename(columns=mapeo_invertido)
        
        print(f"   ✓ {len(mapeo)} columnas renombradas")
        for estandar, original in mapeo.items():
            if estandar != original:
                print(f"      '{original}' → '{estandar}'")
        
        return df_renombrado
    
    def _convertir_tipos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convierte los tipos de datos según el modelo."""
        print("\n3. Convirtiendo tipos de datos...")
        
        df_convertido = df.copy()
        
        for col, config in self.modelo_datos.items():
            if col not in df_convertido.columns:
                continue
            
            dtype_objetivo = config["dtype"]
            
            try:
                if dtype_objetivo == "datetime64[ns]":
                    df_convertido[col] = pd.to_datetime(df_convertido[col], errors='coerce')
                    print(f"   ✓ '{col}' → datetime")
                    
                elif dtype_objetivo == "float64":
                    df_convertido[col] = pd.to_numeric(df_convertido[col], errors='coerce')
                    print(f"   ✓ '{col}' → float64")
                    
                elif dtype_objetivo == "int64":
                    df_convertido[col] = pd.to_numeric(df_convertido[col], errors='coerce').astype('Int64')
                    print(f"   ✓ '{col}' → int64")
                    
                elif dtype_objetivo == "string":
                    df_convertido[col] = df_convertido[col].astype(str)
                    print(f"   ✓ '{col}' → string")
                    
            except Exception as e:
                print(f"   ⚠ Error convirtiendo '{col}': {str(e)}")
        
        return df_convertido
    
    def _validar_datos(self, df: pd.DataFrame):
        """Valida la calidad de los datos estandarizados."""
        print("\n4. Validando calidad de datos...")
        
        self.validacion_report = {
            "total_registros": len(df),
            "columnas": {},
            "errores": []
        }
        
        for col in df.columns:
            nulos = df[col].isna().sum()
            pct_nulos = (nulos / len(df)) * 100
            
            self.validacion_report["columnas"][col] = {
                "nulos": nulos,
                "pct_nulos": round(pct_nulos, 2),
                "valores_unicos": df[col].nunique()
            }
            
            if nulos > 0:
                print(f"   ⚠ '{col}': {nulos} valores nulos ({pct_nulos:.2f}%)")
                
                if self.modelo_datos[col].get("required", False) and pct_nulos > 10:
                    self.validacion_report["errores"].append(
                        f"Columna requerida '{col}' tiene {pct_nulos:.2f}% de nulos"
                    )
        
        if not self.validacion_report["errores"]:
            print("   ✓ Validación exitosa")
        else:
            print("\n   ⚠ ADVERTENCIAS:")
            for error in self.validacion_report["errores"]:
                print(f"      - {error}")
    
    def obtener_reporte_validacion(self) -> Dict:
        """Retorna el reporte de validación."""
        return self.validacion_report
    
    def mostrar_resumen(self, df: pd.DataFrame):
        """Muestra un resumen del dataset estandarizado."""
        print("\n" + "=" * 60)
        print("RESUMEN DEL DATASET ESTANDARIZADO")
        print("=" * 60)
        print(f"\nDimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
        print(f"\nColumnas: {', '.join(df.columns)}")
        print("\nPrimeras filas:")
        print(df.head())
        print("\nTipos de datos:")
        print(df.dtypes)
        print("\nEstadísticas descriptivas:")
        print(df.describe())