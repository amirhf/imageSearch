FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY apps/api/requirements.base.txt .
COPY apps/api/requirements.models.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.base.txt
RUN pip install --no-cache-dir -r requirements.models.txt

# Copy application code
COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "-m", "workers.captioner.worker"]
