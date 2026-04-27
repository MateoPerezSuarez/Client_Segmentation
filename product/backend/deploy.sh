#!/bin/bash
set -e

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="segmentacion-491208"
REGION="europe-west1"
SERVICE_NAME="client-segmentation-api"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "▶ Building image..."
docker build --platform linux/amd64 -t "$IMAGE" "$SCRIPT_DIR"

echo "▶ Pushing to Container Registry..."
docker push "$IMAGE"

echo "▶ Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --project "$PROJECT_ID"

echo "✅ Done. Service URL:"
gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format "value(status.url)"
