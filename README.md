# AI Feature Router for Image Metadata

Local‑first image captioning + semantic image/text search with a **cost/latency‑aware** cloud fallback. Built to demonstrate **AI integration, retrieval, and production‑grade engineering**.

## Why this project
- Show local vs cloud **policy routing** (confidence & SLO‑based)
- Demonstrate **vector search** (pgvector or Qdrant)
- Ship **observability** (Prometheus, Grafana, Jaeger) and **ADR**s

## One‑liner demo
```bash
docker compose -f infra/docker-compose.yml up -d --build
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000/docs to upload an image and run /search
```

## Storage Options
- **Local** - Files stored on disk (default, zero setup)
- **MinIO** - S3-compatible, runs in Docker (dev/self-hosted)
- **Cloudflare R2** - Zero egress fees, $1.50/month for 100GB (production)
- **AWS S3** - Industry standard with CloudFront CDN

See [S3_STORAGE_SETUP.md](S3_STORAGE_SETUP.md) for complete setup guide.

## Architecture
- **FastAPI** gateway exposes `/images`, `/search`, `/metrics`
- **Captioner**: local **BLIP** first; **cloud** fallback (OpenAI/Gemini/Anthropic) via adapter
- **Embedder**: **OpenCLIP** (or SigLIP) image+text encoders → vectors
- **Vector store**: **pgvector** (HNSW) or **Qdrant**, selectable via env

```
[Client/UI] → FastAPI → (caption: BLIP → cloud?)
                     → (embed: OpenCLIP)
                     → Vector Store (pgvector/Qdrant)
                     → Prometheus/Jaeger → Grafana
```

## Endpoints
- `POST /images` – body: `{ url | file }` → returns `{id, caption, download_url, thumbnail_url, ...}`
- `GET /images/{id}` – metadata including download URLs
- `GET /images/{id}/download` – download original image
- `GET /images/{id}/thumbnail` – download 256x256 thumbnail
- `GET /search?q=...` – semantic text→image search; query params: `k`, `backend`
- `GET /metrics` – Prometheus exposition
- `GET /healthz` – liveness

## Config
Environment (.env):
```
VECTOR_BACKEND=pgvector   # or qdrant
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router
QDRANT_URL=http://localhost:6333

# Cloud providers
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Routing policy
CAPTION_CONFIDENCE_THRESHOLD=0.55
CAPTION_LATENCY_BUDGET_MS=600

# Image storage
IMAGE_STORAGE_BACKEND=local   # local, minio, or s3
IMAGE_STORAGE_PATH=./storage/images  # For local backend
THUMBNAIL_SIZE=256
BASE_URL=http://localhost:8000

# S3-Compatible Storage (MinIO/Cloudflare R2/AWS S3)
S3_BUCKET_NAME=imagesearch
S3_ENDPOINT_URL=http://localhost:9000  # MinIO or R2/S3 endpoint
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
```

## Run tests
```bash
# Run all CI/CD safe tests
python tests/test_infrastructure.py
python tests/test_load.py
python tests/test_image_storage.py

# Or use pytest
pytest tests/ -v

# See tests/README.md for more options
```

## Dataset Seeding
Seed the database with real image datasets:

```bash
# COCO validation set (automatic download)
python scripts/seed_datasets.py --dataset coco --count 1000

# Unsplash (requires API key)
python scripts/seed_datasets.py --dataset unsplash --count 500 --api-key YOUR_KEY

# List available datasets
python scripts/seed_datasets.py --list
```

## Benchmarking
Run comprehensive performance benchmarks:

```bash
cd notebooks
python benchmark.py --test-image ../test_image.jpg --sample-size 100
```

Generates:
- Latency statistics (mean, P95, P99)
- Cost projections
- Quality metrics (BLEU, METEOR)
- Visualization plots

## Observability
- Prometheus at http://localhost:9090
- Grafana at http://localhost:3000 (import `infra/grafana/dashboards.json`)
- Jaeger at http://localhost:16686

## ADRs
See `docs/adr/0001-routing-policy.md` for "Local‑first with Confidence & SLO Overrides".

## License
MIT (sample) – replace or update as you prefer.
