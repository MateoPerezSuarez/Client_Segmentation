from google.cloud import storage
import os

def subir_archivo_a_bucket(nombre_bucket, ruta_archivo_local, nombre_blob_destino, ruta_clave_json):
    """
    Sube un archivo a un bucket de Google Cloud Storage.
    """
    try:
        # 1. Autenticación explícita usando el archivo JSON
        # Esta es la forma más sencilla para pruebas locales
        storage_client = storage.Client.from_service_account_json(ruta_clave_json)

        # 2. Obtener el bucket
        bucket = storage_client.bucket(nombre_bucket)

        # 3. Crear un 'blob' (el objeto que contendrá el archivo en la nube)
        blob = bucket.blob(nombre_blob_destino)

        # 4. Subir el archivo
        print(f"Subiendo {ruta_archivo_local} a {nombre_bucket}...")
        blob.upload_from_filename(ruta_archivo_local)

        print(f"¡Éxito! El archivo se subió como: {nombre_blob_destino}")

    except Exception as e:
        print(f"Ocurrió un error: {e}")

# --- CONFIGURACIÓN ---
# Cambia estos valores por los tuyos
MI_BUCKET = "proyecto_segmentacion"  # Ej: mi-proyecto-datos
MI_ARCHIVO_LOCAL = "data/fashion_ecommerce/dataset_fashion_store_salesitems.csv"          # El archivo en tu ordenador
NOMBRE_EN_NUBE = "fashion_ecommerce/dataset_fashion_store_salesitems.csv"
MI_CLAVE_JSON = "cl/elite-firefly-480109-c9-fc816fd492b2.json" 

# Ejecutar la función
if __name__ == "__main__":
    # Verificamos que el archivo local exista antes de intentar subirlo
    if os.path.exists(MI_ARCHIVO_LOCAL):
        subir_archivo_a_bucket(MI_BUCKET, MI_ARCHIVO_LOCAL, NOMBRE_EN_NUBE, MI_CLAVE_JSON)
    else:
        print(f"Error: No encuentro el archivo {MI_ARCHIVO_LOCAL}")