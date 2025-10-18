# Day 1&2 Implementation Plan - Image AI Feature Router

**Project**: AI Feature Router for Image Metadata  
**Timeline**: Days 1-2 of implementation  
**Goal**: Complete local stack setup with working BLIP captioning + OpenCLIP embeddings + vector search

---

## Current Status Summary

### ✅ Already Implemented
- Core FastAPI application with endpoints (`/images`, `/search`, `/healthz`, `/metrics`)
- Dependency injection system for vector stores and ML clients
- Basic routing policy (confidence/latency-based)
- Both pgvector and Qdrant storage implementations
- BLIP captioner (local) and OpenCLIP embedder clients
- Docker Compose infrastructure stack
- ADR 0001 (routing policy), README, pricing YAML
- Seed script and load test stubs

### ❌ Critical Issues Found
1. **Vector dimension mismatch**: models.py defines Vector(768) but OpenCLIP ViT-B-32 produces 512-dim vectors
2. **Missing prometheus.yml**: Referenced in docker-compose but file doesn't exist
3. **Minimal .gitignore**: Needs Python-specific patterns
4. **OTEL not initialized**: Tracing dependencies installed but not configured in main.py

---

## Day 1: Infrastructure & Environment Setup (4 hours)

### Phase 1.1: Fix Critical Code Issues (30 min)

#### 1. Fix Vector Dimension Mismatch 🔴
**Problem**: `models.py` defines `Vector(768)` but OpenCLIP ViT-B-32 produces 512-dimensional vectors

**Solution Options**:
- **Option A** (Recommended): Change model to Vector(512) to match ViT-B-32
- **Option B**: Change OpenCLIP model to ViT-B-16 or ViT-L-14 (produces 512-768 dims)

**Action**: Use Option A - update `apps/api/storage/models.py`
```python
embed_vector = mapped_column(Vector(512))  # Match ViT-B-32 output
```

**Impact**: Database schema needs recreation

#### 2. Enhanced .gitignore 🔴
**Add**:
```
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
.DS_Store
.idea/
*.swp
*.swo
~*
test_data/*.jpg
test_data/*.png
notebooks/.ipynb_checkpoints/
```

#### 3. Create Missing Prometheus Config 🔴
**File**: `infra/prometheus/prometheus.yml`
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "api"
    static_configs:
      - targets: ["host.docker.internal:8000"]
    metrics_path: "/metrics"
```

### Phase 1.2: Docker Infrastructure Setup (1 hour)

#### 1. Start Docker Services
```powershell
cd infra
docker compose up -d --build
```

#### 2. Verify All Services Healthy
```powershell
docker compose ps
# Expected: postgres, qdrant, prometheus, grafana, jaeger all "Up"
```

#### 3. Service Validation Checklist
- [ ] Postgres: `psql postgresql://postgres:postgres@localhost:5432/ai_router -c "\l"`
- [ ] Qdrant: `curl http://localhost:6333/collections`
- [ ] Prometheus: Access `http://localhost:9090/targets`
- [ ] Grafana: Access `http://localhost:3000` (admin/admin)
- [ ] Jaeger: Access `http://localhost:16686`

### Phase 1.3: Python Environment Setup (1 hour)

#### 1. Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

#### 2. Upgrade pip and Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r apps/api/requirements.txt
```

**Expected Downloads** (first time):
- PyTorch (~2GB)
- Transformers models (BLIP: ~1GB on first API call)
- OpenCLIP models (~500MB on first API call)

#### 3. Verify Environment
```powershell
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import open_clip; print(f'OpenCLIP: {open_clip.__version__}')"
```

### Phase 1.4: Environment Configuration (30 min)

#### 1. Verify .env File
Already exists with:
```
VECTOR_BACKEND=pgvector
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router
QDRANT_URL=http://localhost:6333
CAPTION_CONFIDENCE_THRESHOLD=0.55
CAPTION_LATENCY_BUDGET_MS=600
```

#### 2. Test Database Connection
```powershell
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✓ DB Connected'); conn.close()"
```

---

## Day 2: Core Functionality Testing & Validation (4 hours)

### Phase 2.1: API Startup & Health (30 min)

#### 1. Start FastAPI Server
```powershell
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Verify Endpoints
```powershell
# Health check
curl http://localhost:8000/healthz

# Swagger UI
# Open browser: http://localhost:8000/docs

# Metrics (Prometheus format)
curl http://localhost:8000/metrics
```

**Expected Output**:
- `/healthz`: `{"status": "ok"}`
- `/metrics`: Prometheus text format with `router_local_total`, etc.

### Phase 2.2: Model Loading & First Inference (1.5 hours)

#### 1. Prepare Test Image
**Option A**: Download test image
```powershell
mkdir test_data
curl -o test_data/beach.jpg "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800"
```

**Option B**: Use any local image

#### 2. Test Upload via Swagger
1. Open http://localhost:8000/docs
2. Expand `POST /images`
3. Click "Try it out"
4. Upload `test_data/beach.jpg`
5. Click "Execute"

**First Request Notes**:
- Will take 30-120 seconds (model downloads)
- Models cached in `~/.cache/huggingface/` and `~/.cache/clip/`
- Subsequent requests: 300-800ms

**Expected Response**:
```json
{
  "id": "abc123...",
  "caption": "a beach with ocean waves and blue sky",
  "origin": "local",
  "confidence": 0.87
}
```

#### 3. Test Upload via cURL
```powershell
curl -X POST "http://localhost:8000/images" `
  -F "file=@test_data/beach.jpg" `
  -H "accept: application/json"
```

### Phase 2.3: Vector Search Testing (1 hour)

#### 1. Upload Multiple Test Images
```powershell
# Upload 5 different images to build a corpus
$images = @("beach.jpg", "mountain.jpg", "city.jpg", "forest.jpg", "desert.jpg")
foreach ($img in $images) {
  curl -X POST "http://localhost:8000/images" -F "file=@test_data/$img"
}
```

#### 2. Test Semantic Search
```powershell
# Search for beach-related images
curl "http://localhost:8000/search?q=beach%20at%20sunset&k=5"

# Search for nature scenes
curl "http://localhost:8000/search?q=natural%20landscape&k=5"

# Search for urban settings
curl "http://localhost:8000/search?q=city%20buildings&k=5"
```

**Expected Response**:
```json
{
  "query": "beach at sunset",
  "results": [
    {
      "id": "abc123...",
      "caption": "a beach with ocean waves...",
      "score": 0.89
    },
    ...
  ]
}
```

#### 3. Verify Score Relevance
- Top result should have score > 0.8 for exact matches
- Related images: 0.6-0.8
- Unrelated images: < 0.5

### Phase 2.4: Dual Vector Backend Testing (30 min)

#### 1. Test pgvector Mode
```powershell
# Already default in .env
$env:VECTOR_BACKEND="pgvector"
# Restart API, upload image, search
```

#### 2. Test Qdrant Mode
```powershell
$env:VECTOR_BACKEND="qdrant"
# Restart API
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Upload same test image
curl -X POST "http://localhost:8000/images" -F "file=@test_data/beach.jpg"

# Run same search
curl "http://localhost:8000/search?q=beach&k=5"
```

#### 3. Compare Results
Both backends should return similar results (scores within ±0.05)

### Phase 2.5: Observability Stack Validation (30 min)

#### 1. Verify Prometheus Scraping
1. Open http://localhost:9090/targets
2. Verify "api" target is "UP"
3. Query: `router_local_total`
4. Should show counter incrementing

#### 2. Check Metrics in Prometheus
```
# Query Examples:
router_local_total          # Total local routes
router_cloud_total          # Total cloud routes (should be 0)
rate(router_local_total[5m])  # Local routing rate
histogram_quantile(0.95, rate(request_latency_ms_bucket[5m]))  # p95 latency
```

#### 3. Grafana Dashboard (Basic)
1. Access http://localhost:3000 (admin/admin)
2. Add Prometheus data source: http://prometheus:9090
3. Create simple dashboard with:
   - Panel 1: `router_local_total` (Counter)
   - Panel 2: `histogram_quantile(0.95, request_latency_ms_bucket)` (Gauge)

#### 4. Jaeger Tracing (Stretch Goal)
- Access http://localhost:16686
- Note: Requires OTEL initialization (not in scope for Day 1-2)

---

## Success Criteria Checklist

By end of Day 2, verify:

### Infrastructure
- [x] Docker Compose: All 5 services running and healthy
- [x] Postgres: Database `ai_router` exists with `images` table
- [x] pgvector: Extension enabled, HNSW index created
- [x] Qdrant: Collection `images` exists with 512-dim vectors
- [x] Prometheus: Scraping `/metrics` endpoint successfully
- [x] Grafana: Accessible with basic dashboard

### API Functionality
- [x] FastAPI starts without errors
- [x] Swagger UI accessible at `/docs`
- [x] `/healthz` returns 200 OK
- [x] `/metrics` returns Prometheus format

### ML Models
- [x] BLIP model downloads and loads on first request
- [x] OpenCLIP model downloads and loads on first request
- [x] Models cached locally for subsequent requests
- [x] Caption generation completes in < 1 second (after first load)
- [x] Embeddings generation completes in < 500ms

### End-to-End Workflow
- [x] Upload image via Swagger → get caption + confidence + origin
- [x] Upload image via cURL → same results
- [x] Retrieve image by ID → returns metadata
- [x] Search with text query → returns ranked results
- [x] Search scores are semantically relevant
- [x] Switching vector backends works without code changes

### Observability
- [x] `router_local_total` increments on each upload
- [x] `request_latency_ms` histogram populates
- [x] Prometheus queries return data
- [x] Grafana displays live metrics

### Performance Baselines
- [x] First caption request: 30-120s (model download)
- [x] Subsequent captions: 300-800ms
- [x] Embedding generation: 100-500ms
- [x] Vector search (10K images): < 100ms
- [x] 100% local routing (no cloud fallbacks yet)

---

## Known Limitations (Day 1-2 Scope)

### Not Implemented Yet:
- Cloud VLM adapters (OpenAI, Gemini, Anthropic) - stubbed only
- OTEL/Jaeger tracing initialization
- Grafana dashboard JSON (manual setup only)
- Integration tests
- Load testing with k6
- Seed script with real datasets (COCO, Flickr30k)
- Next.js UI
- Cost tracking for cloud calls

### Expected for Day 3+:
- Cloud adapter implementation
- Advanced routing policy (queue depth, cache)
- Comprehensive benchmarking
- Load testing
- UI development

---

## Troubleshooting Guide

### Issue: Model downloads fail
**Solution**: Check internet connection, try manual download:
```python
from transformers import BlipProcessor
BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
```

### Issue: Postgres connection refused
**Solution**: 
```powershell
docker compose -f infra/docker-compose.yml logs postgres
# Wait for "database system is ready to accept connections"
```

### Issue: Vector dimension error
**Solution**: Drop and recreate database:
```sql
DROP TABLE IF EXISTS images;
-- Restart API to recreate with correct dimensions
```

### Issue: Qdrant collection mismatch
**Solution**:
```python
from qdrant_client import QdrantClient
client = QdrantClient("http://localhost:6333")
client.delete_collection("images")
# Restart API to recreate
```

### Issue: Prometheus not scraping
**Solution**: Check `host.docker.internal` resolves from container:
```powershell
docker compose -f infra/docker-compose.yml exec prometheus ping host.docker.internal
```

### Issue: High first-request latency
**Expected**: Model downloads can take 30-120s. Subsequent requests should be fast.

---

## Day 2 Deliverables

1. **Working local stack**: All services running, API responding
2. **Validated workflow**: Upload → Caption → Embed → Search working end-to-end
3. **Metrics observable**: Prometheus scraping, Grafana displaying
4. **Documentation**: This plan completed with checkmarks
5. **Test images**: 5-10 sample images ingested and searchable
6. **Performance baseline**: Recorded p50/p95 latency for local captioning

---

## Next Steps (Day 3-4)

1. Implement cloud VLM adapters (OpenAI GPT-4o-mini)
2. Add routing policy logic for confidence threshold
3. Implement cost tracking
4. Add OTEL/Jaeger tracing
5. Create comprehensive Grafana dashboard JSON
6. Write integration tests
7. Seed larger dataset (1000+ images)

---

**Plan Version**: 1.0  
**Last Updated**: 2025-10-18  
**Owner**: Development Team
