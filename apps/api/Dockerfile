# FastAPI for Cloud Run (mock-mode by default)
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Use repository root as workdir so imports like `apps.api.main` resolve
WORKDIR /app

# System deps (build-essential sometimes needed for psycopg extras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install light requirements (no Torch)
COPY apps/api/requirements.base.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy full repository (needed for package path `apps.api.*`)
COPY . /app

# Ensure Python can resolve `apps.api.*`
ENV PYTHONPATH=/app

EXPOSE 8000

# Cloud Run provides $PORT. Default to 8000 locally.
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
