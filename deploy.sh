#!/bin/bash
set -e

# Load production environment variables
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
else
    echo "Error: .env.production file not found."
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
REGION="us-east1"
REPO="imagesearch"
PYTHON_SERVICE="imagesearch-api"
GO_SERVICE="imagesearch-go"

echo "Deploying to Project: $PROJECT_ID, Region: $REGION"

# Parse DB Config for Go Service from DATABASE_URL
# Expected format: postgresql+psycopg://user:pass@host/dbname?sslmode=require
# We need to extract these components for the Go service if it expects separate vars, 
# OR just pass DATABASE_URL if it supports it.
# The Go service code uses `pgxpool.ParseConfig(dbURL)`, so passing DATABASE_URL is sufficient.
# However, we need to ensure the scheme is correct (postgres:// instead of postgresql+psycopg://).

# Fix scheme for Go (pgx expects postgres://)
GO_DB_URL=$(echo $DATABASE_URL | sed 's/postgresql+psycopg/postgres/')

echo "Building Go Search Service..."
gcloud builds submit \
  --config cloudbuild-go-search.yaml \
  --substitutions=_IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$GO_SERVICE:latest \
  .

echo "Deploying Go Search Service to Cloud Run..."
gcloud run deploy $GO_SERVICE \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$GO_SERVICE:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="$GO_DB_URL"

# Get Go Service URL
GO_SERVICE_URL=$(gcloud run services describe $GO_SERVICE --region $REGION --format 'value(status.url)')
echo "Go Service deployed at: $GO_SERVICE_URL"

# 3. Build and Deploy Python API
echo "Building Python API..."
gcloud builds submit \
  --config cloudbuild-api-embedder.yaml \
  --substitutions=_IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$PYTHON_SERVICE:latest \
  .

echo "Deploying Python API to Cloud Run..."
# We update the env vars to point to the new Go service
# We also update all other env vars from .env.production to ensure consistency
gcloud run deploy $PYTHON_SERVICE \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$PYTHON_SERVICE:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --update-env-vars GO_SEARCH_URL=$GO_SERVICE_URL \
  --update-env-vars SEARCH_BACKEND=go \
  --update-env-vars SEARCH_SHADOW_MODE=false \
  --update-env-vars DATABASE_URL="$DATABASE_URL" \
  --update-env-vars VECTOR_BACKEND="$VECTOR_BACKEND" \
  --update-env-vars IMAGE_STORAGE_BACKEND="$IMAGE_STORAGE_BACKEND" \
  --update-env-vars S3_BUCKET_NAME="$S3_BUCKET_NAME" \
  --update-env-vars S3_ENDPOINT_URL="$S3_ENDPOINT_URL" \
  --update-env-vars S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
  --update-env-vars S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
  --update-env-vars S3_REGION="$S3_REGION" \
  --update-env-vars S3_USE_PRESIGNED_URLS="$S3_USE_PRESIGNED_URLS" \
  --update-env-vars CLOUD_PROVIDER="$CLOUD_PROVIDER" \
  --update-env-vars OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  --update-env-vars OPENROUTER_MODEL="$OPENROUTER_MODEL" \
  --update-env-vars USE_MOCK_MODELS="$USE_MOCK_MODELS" \
  --update-env-vars BASE_URL="$BASE_URL" \
  --update-env-vars CAPTION_CONFIDENCE_THRESHOLD="$CAPTION_CONFIDENCE_THRESHOLD" \
  --update-env-vars CAPTION_LATENCY_BUDGET_MS="$CAPTION_LATENCY_BUDGET_MS" \
  --update-env-vars HYBRID_TEXT_BOOST="$HYBRID_TEXT_BOOST" \
  --update-env-vars HYBRID_TEXT_WEIGHT="$HYBRID_TEXT_WEIGHT" \
  --update-env-vars USE_REAL_EMBEDDER="$USE_REAL_EMBEDDER" \
  --update-env-vars USE_REAL_CAPTIONER="$USE_REAL_CAPTIONER" \
  --update-env-vars EMBED_MAX_SIDE="$EMBED_MAX_SIDE" \
  --update-env-vars TORCH_NUM_THREADS="$TORCH_NUM_THREADS" \
  --update-env-vars TORCH_NUM_INTEROP_THREADS="$TORCH_NUM_INTEROP_THREADS" \
  --update-env-vars OPENCLIP_MODEL="$OPENCLIP_MODEL" \
  --update-env-vars OPENCLIP_PRETRAINED="$OPENCLIP_PRETRAINED" \
  --update-env-vars SUPABASE_URL="$SUPABASE_URL" \
  --update-env-vars SUPABASE_JWT_SECRET="$SUPABASE_JWT_SECRET" \
  --update-env-vars SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
  --update-env-vars SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --update-env-vars ADMIN_USER_ID="$ADMIN_USER_ID"

echo "Deployment Complete!"
echo "Python API: $(gcloud run services describe $PYTHON_SERVICE --region $REGION --format 'value(status.url)')"
echo "Go Service: $GO_SERVICE_URL"
