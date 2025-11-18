# AI Feature Router for Image Metadata

Local‑first image captioning + semantic image/text search with a **cost/latency‑aware** cloud fallback. Built to demonstrate **AI integration, retrieval, and production‑grade engineering** with **multi-tenant authentication**.

## Why this project
- Show local vs cloud **policy routing** (confidence & SLO‑based)
- Demonstrate **vector search** (pgvector or Qdrant)
- Ship **observability** (Prometheus, Grafana, Jaeger) and **ADR**s
- **Multi-tenant architecture** with Supabase authentication
- **Privacy controls** - users can upload private or public images

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
- **Authentication**: **Supabase** JWT-based auth with user profiles
- **Multi-tenant**: User-owned images with privacy controls (private/public)
- **Captioner**: local **BLIP** first; **cloud** fallback (OpenAI/Gemini/Anthropic) via adapter
- **Embedder**: **OpenCLIP** (or SigLIP) image+text encoders → vectors
- **Vector store**: **pgvector** (HNSW) or **Qdrant**, selectable via env

```
[Client/UI] → Next.js (Supabase Auth) → FastAPI (JWT validation)
                                      → (caption: BLIP → cloud?)
                                      → (embed: OpenCLIP)
                                      → Vector Store (pgvector/Qdrant)
                                      → Prometheus/Jaeger → Grafana
```

## Endpoints

### Public Endpoints
- `GET /search?q=...` – semantic text→image search; query params: `k`, `scope` (all/mine/public)
- `GET /images` – list images with filtering; query params: `limit`, `offset`, `visibility`
- `GET /images/{id}` – metadata including download URLs (respects privacy)
- `GET /images/{id}/download` – download original image (respects privacy)
- `GET /images/{id}/thumbnail` – download 256x256 thumbnail (respects privacy)
- `GET /metrics` – Prometheus exposition
- `GET /health` – health check

### Authenticated Endpoints (requires Bearer token)
- `POST /images` – upload image (URL or file); returns `{id, caption, download_url, thumbnail_url, ...}`
- `PATCH /images/{id}` – update image metadata (caption, visibility)
- `DELETE /images/{id}` – soft delete image (owner only)

## Config
Environment (.env):
```
# Vector Store
VECTOR_BACKEND=pgvector   # or qdrant
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router
QDRANT_URL=http://localhost:6333

# Supabase Authentication (Multi-tenant)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
ADMIN_USER_ID=your-admin-user-uuid

# Cloud providers
CLOUD_PROVIDER=openrouter  # openrouter, openai, gemini, or anthropic
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Routing policy
CAPTION_CONFIDENCE_THRESHOLD=0.55
CAPTION_LATENCY_BUDGET_MS=600

# Model Configuration
USE_MOCK_MODELS=false  # Set to true to disable ML models (cloud-only)
USE_REAL_EMBEDDER=true
USE_REAL_CAPTIONER=false

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
S3_REGION=us-east-1  # or 'auto' for Cloudflare R2
S3_USE_PRESIGNED_URLS=true
```

## Multi-Tenant Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Get your credentials from Settings → API:
   - Project URL
   - Anon/Public key
   - Service role key (keep secret!)
   - JWT Secret (Settings → API → JWT Settings)

### 2. Run Database Migrations
```bash
# Connect to your database and run migrations
psql $DATABASE_URL -f apps/api/storage/migrations/001_add_profiles.sql
psql $DATABASE_URL -f apps/api/storage/migrations/002_add_multi_tenant_fields.sql
```

### 3. Migrate Existing Data (Optional)
If you have existing images, migrate them to the admin user:
```bash
# Set environment variables
export DATABASE_URL="your-database-url"
export ADMIN_USER_ID="your-admin-uuid"

# Run migration
python scripts/migrate_to_multitenant.py --yes
```

### 4. Configure Environment
Update your `.env` file with Supabase credentials (see Config section above).

### 5. Configure Supabase
In your Supabase dashboard:
- **Authentication → URL Configuration**: Add your frontend URL to redirect URLs
- **Authentication → Providers**: Enable Email provider
- **Authentication → Email Templates**: Customize if needed

See `docs/multi_tenant/DEPLOYMENT_CHECKLIST.md` for complete deployment guide.

## Run tests
```bash
# Run all CI/CD safe tests
python tests/test_infrastructure.py
python tests/test_load.py
python tests/test_image_storage.py

# Multi-tenant E2E tests
pytest tests/test_e2e_multitenant.py -v

# Or use pytest for all tests
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

## Frontend (Next.js UI)
Path: `apps/ui/`

- **Stack**: Next.js 16 (App Router), React 18, TypeScript, Tailwind CSS, TanStack Query, Supabase Auth
- **Features**: User authentication, Search gallery, Upload (URL or file) with progress, Image library, Privacy controls, Explore public images
- **Default port**: `3100`

### Prerequisites
- Node.js 18+ (recommended 20+)
- Backend API running (default `http://localhost:8000`)
- Supabase project (for authentication)

### Setup & Run (Dev)
```bash
cd apps/ui
cp .env.local.example .env.local
# Edit .env.local with your values:
# NEXT_PUBLIC_API_BASE=http://localhost:8000
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
npm install
npm run dev   # http://localhost:3100
```
### Build & Start (Prod)
```bash
cd apps/ui
npm run build
npm run start   # http://localhost:3100
```
### Important environment
- `NEXT_PUBLIC_API_BASE` – Backend API URL (e.g., `http://localhost:8000`)
- `NEXT_PUBLIC_SUPABASE_URL` – Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` – Supabase anonymous/public key

### UI routes
- `/` – Search page (query by text, shows local/cloud origin badges)
- `/login` – User login with Supabase
- `/signup` – User registration
- `/upload` – Upload images (authenticated); set privacy (private/public)
- `/library` – User's uploaded images with privacy controls
- `/explore` – Browse public images from all users
- `/image/[id]` – Image detail (caption, origin, metadata, "Find similar")
- `/metrics` – Metrics dashboard (p50/p95, local vs cloud split, cost, cache hits)

### API proxy routes (UI → Backend)
All proxy routes automatically forward the `Authorization` header from Supabase:
- `GET /api/search` → `${NEXT_PUBLIC_API_BASE}/search` (with auth token)
- `GET /api/images` → `${NEXT_PUBLIC_API_BASE}/images` (with auth token)
- `GET /api/images/[id]` → `${NEXT_PUBLIC_API_BASE}/images/{id}` (with auth token)
- `POST /api/images` → `${NEXT_PUBLIC_API_BASE}/images` (authenticated, file or url)
- `PATCH /api/images/[id]` → `${NEXT_PUBLIC_API_BASE}/images/{id}` (authenticated)
- `DELETE /api/images/[id]` → `${NEXT_PUBLIC_API_BASE}/images/{id}` (authenticated)
- `GET /api/metrics/summary` → parses `${NEXT_PUBLIC_API_BASE}/metrics` into a compact JSON summary

### Troubleshooting
- Hydration warnings from extensions: we set `suppressHydrationWarning` on `<body>`.
- Dev over LAN (192.168.x.x) may show an "allowedDevOrigins" warning; add to `apps/ui/next.config.mjs` if needed:
  ```js
  const nextConfig = {
    images: { unoptimized: true },
    allowedDevOrigins: ['http://192.168.70.10:3100']
  }
  export default nextConfig
  ```
- Tailwind warning about `@tailwindcss/line-clamp`: remove the plugin from `tailwind.config.ts` (included by default in v3.3+).

## Production Deployment

### Backend (Google Cloud Run)
```bash
# Build with embedder support
gcloud builds submit --config cloudbuild-api-embedder.yaml \
  --substitutions=_IMAGE=us-east1-docker.pkg.dev/PROJECT_ID/REPO/imagesearch-api:latest

# Deploy with environment variables
gcloud run deploy imagesearch-api \
  --image us-east1-docker.pkg.dev/PROJECT_ID/REPO/imagesearch-api:latest \
  --region us-east1 \
  --update-env-vars="SUPABASE_URL=...,SUPABASE_JWT_SECRET=...,..."
```

### Frontend (Vercel)
```bash
cd apps/ui
vercel --prod

# Or configure via Vercel dashboard:
# - Link GitHub repository
# - Set environment variables (NEXT_PUBLIC_SUPABASE_URL, etc.)
# - Enable automatic deployments
```

### Database (Neon/Supabase/Cloud SQL)
- Run migrations on production database
- Configure connection pooling
- Enable SSL/TLS
- Set up backups

See `docs/multi_tenant/DEPLOYMENT_CHECKLIST.md` for complete production deployment guide.

## License
MIT (sample) – replace or update as you prefer.
