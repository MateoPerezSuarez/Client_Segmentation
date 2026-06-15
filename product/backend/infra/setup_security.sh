#!/bin/bash
#
# Fase 0 — Seguridad. Operaciones de IAM/infra en Google Cloud.
#
# Idempotente donde es posible. Ejecutar una sola vez (o cuando cambie algo).
# Requiere: gcloud autenticado con permisos de admin en el proyecto.
#
#   bash product/backend/infra/setup_security.sh
#
set -e

PROJECT_ID="segmentacion-491208"
REGION="europe-west1"
AR_REPO="containers"
RUNTIME_SA_NAME="client-segmentation-run"
RUNTIME_SA="$RUNTIME_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "▶ 1/4 · Artifact Registry repo ($AR_REPO)…"
gcloud artifacts repositories create "$AR_REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Imágenes de Client Segmentation" \
  --project="$PROJECT_ID" 2>/dev/null \
  && echo "   creado" \
  || echo "   ya existe (ok)"

echo "▶ 2/4 · Service account de runtime de mínimo privilegio ($RUNTIME_SA_NAME)…"
gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
  --display-name="Client Segmentation — Cloud Run runtime" \
  --project="$PROJECT_ID" 2>/dev/null \
  && echo "   creada" \
  || echo "   ya existe (ok)"

echo "▶ 3/4 · Roles mínimos para la SA (leer + ejecutar jobs + escribir resultados)…"
# Lectura de datos y ejecución de consultas. Si quieres acotar más, sustituye los
# bindings a nivel proyecto por grants a nivel de dataset / bucket concretos.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/bigquery.dataViewer" \
  --condition=None >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/bigquery.jobUser" \
  --condition=None >/dev/null
# Escritura del resultado de la segmentación (tabla + vista _latest) y export a GCS.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/bigquery.dataEditor" \
  --condition=None >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/storage.objectAdmin" \
  --condition=None >/dev/null
echo "   roles asignados"

echo "▶ 4/4 · Lectura de Artifact Registry para la SA…"
gcloud artifacts repositories add-iam-policy-binding "$AR_REPO" \
  --location="$REGION" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/artifactregistry.reader" \
  --project="$PROJECT_ID" >/dev/null
echo "   ok"

echo
echo "✅ Infra de seguridad lista."
echo "   Runtime SA: $RUNTIME_SA"
echo "   La SA NO tiene claves descargables: Cloud Run la usa vía Workload Identity."
echo
echo "Siguiente paso: re-desplegar con  bash product/backend/deploy.sh"
echo
echo "──────────────────────────────────────────────────────────────────────────"
echo "EXPORTAR A UN PROYECTO DE CLIENTE (su BigQuery / sus buckets)."
echo "El export acepta destinos totalmente cualificados, así que pueden vivir en"
echo "el proyecto del cliente. En ese caso es EL CLIENTE quien concede acceso a"
echo "nuestra SA en su lado:"
echo
echo "  # BigQuery (sobre su dataset)"
echo "  bq add-iam-policy-binding --member='serviceAccount:$RUNTIME_SA' \\"
echo "    --role='roles/bigquery.dataEditor' <PROYECTO_CLIENTE>:<DATASET>"
echo "  gcloud projects add-iam-policy-binding <PROYECTO_CLIENTE> \\"
echo "    --member='serviceAccount:$RUNTIME_SA' --role='roles/bigquery.jobUser'"
echo
echo "  # Cloud Storage (sobre su bucket)"
echo "  gcloud storage buckets add-iam-policy-binding gs://<BUCKET_CLIENTE> \\"
echo "    --member='serviceAccount:$RUNTIME_SA' --role='roles/storage.objectAdmin'"
echo "──────────────────────────────────────────────────────────────────────────"
echo
echo "──────────────────────────────────────────────────────────────────────────"
echo "OPCIONAL — limpieza de claves antiguas de la SA expuesta 'segmenteacion@'."
echo "La clave filtrada (22f600ce747c) ya fue DESHABILITADA automáticamente por"
echo "Google. Las otras claves no estaban en el repo. Si quieres eliminarlas por"
echo "higiene, revisa primero que nada dependa de ellas y ejecuta a mano:"
echo
echo "  gcloud iam service-accounts keys list \\"
echo "    --iam-account=segmenteacion@$PROJECT_ID.iam.gserviceaccount.com \\"
echo "    --project=$PROJECT_ID"
echo
echo "  gcloud iam service-accounts keys delete <KEY_ID> \\"
echo "    --iam-account=segmenteacion@$PROJECT_ID.iam.gserviceaccount.com \\"
echo "    --project=$PROJECT_ID"
echo "──────────────────────────────────────────────────────────────────────────"
