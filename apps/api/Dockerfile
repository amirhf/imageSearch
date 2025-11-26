# FastAPI for Cloud Run (mock-mode by default)
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

# Use repository root as workdir so imports like `apps.api.main` resolve
WORKDIR /app

# System deps (build-essential sometimes needed for psycopg extras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install base requirements
COPY apps/api/requirements.base.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install ML model dependencies (Torch + transformers + open-clip)
# These are needed for real captioning/embedding (USE_MOCK_MODELS=false)
# Set USE_MOCK_MODELS=true in .env to skip using these at runtime
COPY apps/api/requirements.models.txt /app/requirements.models.txt
RUN pip install --no-cache-dir -r /app/requirements.models.txt

# Copy full repository (needed for package path `apps.api.*`)
COPY . /app

# Ensure Python can resolve `apps.api.*`
ENV PYTHONPATH=/app

EXPOSE 8000

# Cloud Run provides $PORT. Default to 8000 locally.
# Use python -m and --app-dir to ensure import path resolution.
CMD ["sh", "-c", "python -m uvicorn apps.api.main:app --app-dir /app --host 0.0.0.0 --port ${PORT:-8000}"]
