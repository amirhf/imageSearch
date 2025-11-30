# Developer Guide & Troubleshooting

This guide summarizes how to run, test, and debug the AI Image Search project locally and in production. It includes non-obvious details about infrastructure and common pitfalls.

## 1. Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Go 1.23+
- Node.js 18+

### Infrastructure (The Foundation)
Before running any code, start the backing services.
```bash
# Starts Postgres (5432), Qdrant (6333), MinIO (9000), Prometheus (9090), Jaeger (16686)
docker compose -f infra/docker-compose.yml up -d
```
> **Tip**: If you see DB connection errors, ensure `postgres` is healthy: `docker compose -f infra/docker-compose.yml ps`

### Python API (The Gateway)
Runs on port **8000**. Handles auth, writes, and routing.
```bash
# Setup venv
python -m venv venv
source venv/bin/activate
pip install -r apps/api/requirements.txt

# Run with hot reload
# USE_MOCK_MODELS=true is faster for dev (no heavy ML models loaded)
export USE_MOCK_MODELS=true 
export PYTHONPATH=$PYTHONPATH:.
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Go Search Service (The Engine)
Runs on port **8080**. Handles high-performance read-only search.
```bash
cd services/search-go
# Ensure DB_URL uses 'postgres://' scheme (not 'postgresql+psycopg://')
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/ai_router"
go run main.go
```

### Frontend (The UI)
Runs on port **3100**.
```bash
cd apps/ui
# Ensure .env.local points to http://localhost:8000
npm run dev
```

---

## 2. Testing

### Unit & Integration Tests
```bash
# Run all tests (requires infrastructure up)
pytest tests/

# Test specific components
pytest tests/test_image_storage.py
pytest tests/test_search_consistency.py
```

### Load Testing (Locust)
To test performance under concurrency:
```bash
# Install locust
pip install locust

# Run headless load test (users=50, spawn_rate=5)
locust -f tests/load/locustfile.py --headless -u 50 -r 5 --host http://localhost:8000
```

### Manual Verification (Curl)
Quickly verify the search endpoint:
```bash
# Public search (no auth)
curl "http://localhost:8000/search?q=test&scope=public"

# Health check
curl "http://localhost:8000/health"
```

---

## 3. Cloud Deployment (Google Cloud Run)

### Deployment Script
Use `deploy.sh` to deploy both services. It handles:
1.  Building Docker images (Cloud Build).
2.  Deploying to Cloud Run.
3.  **Injecting Secrets**: It reads `.env.production` and passes all variables to the container.

> **Critical**: Always run `./deploy.sh` from the project root. Do not deploy services individually unless you manually pass all environment variables.

### Environment Variables
Production variables are in `.env.production`.
-   **Secrets**: `SUPABASE_JWT_SECRET`, `S3_SECRET_ACCESS_KEY`, `OPENROUTER_API_KEY`.
-   **Config**: `GO_SEARCH_URL` (must point to the deployed Go service URL).

---

## 4. Troubleshooting & Common Errors

### 🔴 Error: `RuntimeError: open_clip/torch not available`
-   **Context**: Production / Docker.
-   **Cause**:
    1.  **Shadowing**: A local file named `lzma.py` (or similar) in your project root is copied into the container, breaking Python's standard library.
    2.  **Missing Sys Deps**: Using `python:slim` image lacks `libgl1` (needed for OpenCV/Torch).
-   **Fix**:
    1.  Delete local `lzma.py` or add to `.dockerignore`.
    2.  Use non-slim base image (e.g., `python:3.11`) in Dockerfile.

### 🔴 Error: `NameError: name 'get_captioner' is not defined`
-   **Context**: Uploading images (`POST /images`).
-   **Cause**: Missing imports in `apps/api/main.py` after refactoring.
-   **Fix**: Ensure all dependencies (`get_captioner`, `should_use_cloud`) are imported from `apps.api.deps` or `apps.api.routing_policy`.

### 🔴 Error: Search returns only 1 result (or very few)
-   **Context**: "Explore" page or Public Search.
-   **Cause**: Visibility filtering bug. The Go service might be filtering for `visibility = 'public'` but ignoring `public_admin` (system-seeded images).
-   **Fix**: Ensure SQL query checks `visibility IN ('public', 'public_admin')`.

### 🔴 Error: `500 Internal Server Error` on Upload
-   **Context**: Uploading to S3/R2.
-   **Cause**: Missing or incorrect S3 credentials/region in environment variables.
-   **Fix**: Check `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` in `.env.production`. Ensure `deploy.sh` passes them.

### 🔴 Error: `connection refused` to Postgres/Qdrant
-   **Context**: Running locally or in Docker.
-   **Cause**:
    -   **Local**: Containers are not running (`docker compose up -d`).
    -   **Docker**: Incorrect hostnames. Use service names (`postgres`, `qdrant`) inside Docker, but `localhost` when running outside.

---

## 5. Database Schema & Migrations

### Schema Management
We use raw SQL migrations in `apps/api/storage/migrations/`.
-   `001_add_profiles.sql`: User profiles table.
-   `002_add_multi_tenant_fields.sql`: Ownership & visibility columns.
-   `004_add_hybrid_search.sql`: `tsvector` column and GIN index for hybrid search.

### Applying Migrations
```bash
# Local
psql $DATABASE_URL -f apps/api/storage/migrations/004_add_hybrid_search.sql

# Production (via script)
python apply_prod_migration.py
```
> **Note**: Always backup production DB before applying migrations.

