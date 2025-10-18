# ai-feature-router

> **Local‑first image captioning + vector search with cloud fallback.** This starter repo scaffolds the core pieces you’ll demo to hiring managers: a FastAPI backend (Python) with BLIP captioning and OpenCLIP/SigLIP embeddings, a pluggable vector store (pgvector or Qdrant), a routing policy hook for cost/latency, seed + benchmark stubs, and an ADR template.

---

## Quickstart (dev)

```bash
# 0) prerequisites: Docker + docker compose v2, Python 3.11+

# 1) clone & enter
# git clone https://github.com/<you>/ai-feature-router && cd ai-feature-router

# 2) bring up infra (Postgres+pgvector, Qdrant, Grafana, Prometheus, Jaeger)
docker compose -f infra/docker-compose.yml up -d --build

# 3) create & activate venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4) install backend deps
pip install -r apps/api/requirements.txt

# 5) run FastAPI (auto-reload)
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# 6) open Swagger
# http://localhost:8000/docs
```

**Notes**
- BLIP/OpenCLIP models are lazily loaded on first use. The first request may be slower while weights are cached locally (`~/.cache`).
- You can toggle vector store (pgvector vs Qdrant) via env: `VECTOR_BACKEND=pgvector|qdrant`.
- Cloud VLM is optional; the project runs fully offline. Fallback adapters are no-ops until you add provider keys.

---

## Repo structure

```
ai-feature-router/
  apps/
    api/
      main.py
      deps.py
      routing_policy.py
      storage/
        __init__.py
        models.py           # SQLAlchemy models for Postgres + pgvector
        pgvector_store.py   # ANN search via pgvector
        qdrant_store.py     # ANN search via qdrant-client
      services/
        captioner_client.py # fast local BLIP + optional cloud fallback adapter
        embedder_client.py  # local OpenCLIP/SigLIP encoders
      requirements.txt
  workers/
    captioner/captioner.py
    embedder/embedder.py
    requirements.txt
  scripts/
    seed.py                # seed demo images & ingest metadata
    loadtest.js            # k6 (stub)
  costs/
    providers.yaml         # pricing table for ADR & metrics
  docs/
    adr/0001-routing-policy.md
  infra/
    docker-compose.yml
    grafana/dashboards.json
    prometheus/prometheus.yml
    jaeger/README.md
  notebooks/
    benchmark.ipynb        # (placeholder)
  .env.example
  README.md
```

---

## README.md (project skeleton)

```markdown
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
- `POST /images` – body: `{ url | file }` → returns `{id, caption, tags, vector_info}`
- `GET /images/{id}` – metadata
- `GET /search?q=...` – semantic text→image search; query params: `k`, `backend`
- `GET /metrics` – Prometheus exposition
- `GET /healthz` – liveness

## Config
Environment (.env):
```
VECTOR_BACKEND=pgvector   # or qdrant
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
CAPTION_CONFIDENCE_THRESHOLD=0.55
CAPTION_LATENCY_BUDGET_MS=600
```

## Run tests (placeholder)
```bash
pytest -q
```

## Observability
- Prometheus at http://localhost:9090
- Grafana at http://localhost:3000 (import `infra/grafana/dashboards.json`)
- Jaeger at http://localhost:16686

## ADRs
See `docs/adr/0001-routing-policy.md` for “Local‑first with Confidence & SLO Overrides”.

## License
MIT (sample) – replace or update as you prefer.
```
```

---

## docs/adr/0001-routing-policy.md (template)

```markdown
# ADR 0001 – Routing Policy: Local‑First with Confidence & SLO Overrides

- **Status**: Proposed
- **Date**: 2025‑10‑18

## Context
Local captioning/embeddings are fast and free but can be weaker on edge cases; cloud VLMs provide higher quality at monetary cost. We need predictable costs and low latency while preserving search quality.

## Decision
Use local models by default. Promote to a cloud provider **only when**:
1. Local caption **confidence** < `τ = 0.55`, or
2. Local p95 **latency** exceeds `600 ms` under load and **queue depth** is high, or
3. The request explicitly sets `quality=high`.

Cloud provider is selected by **cost × latency** table (see `costs/providers.yaml`). Per‑minute and daily budget caps prevent cost runaways. Results are cached by `(image_hash, model_version)`.

## Consequences
- Expect 75–90% local hit‑rate; predictable monthly cost
- Slight quality variance on rare/hard images handled by fallback
- Adds minimal policy complexity but strong product value

## Pricing Inputs (example; keep up‑to‑date)
```yaml
openai_gpt4o_mini:
  input_per_million: 0.15
  output_per_million: 0.60
gemini_flash_lite:
  input_per_million: 0.10
  output_per_million: 0.40
anthropic_claude_3_5_sonnet:
  input_per_million: 3.00
  output_per_million: 15.00
```

## Alternatives Considered
- Cloud‑first with local fallback (too costly)
- Manual operator override only (not adaptive)

## Links
- `/docs` (Swagger)
- Grafana dashboard screenshot
- Benchmark notebook results
```

---

## apps/api/requirements.txt

```
fastapi==0.115.5
uvicorn[standard]==0.32.0
pydantic==2.9.2
python-multipart==0.0.9
httpx==0.27.2
Pillow==11.0.0
numpy==2.1.3
# models
transformers==4.45.2
torch>=2.3.0
open-clip-torch==2.26.1
# storage
SQLAlchemy==2.0.36
psycopg[binary,pool]==3.2.3
qdrant-client==1.11.3
pgvector==0.3.3
# metrics & tracing
prometheus-client==0.21.0
opentelemetry-sdk==1.27.0
opentelemetry-instrumentation-fastapi==0.48b0
opentelemetry-exporter-otlp==1.27.0
python-dotenv==1.0.1
```

---

## apps/api/main.py (minimal FastAPI + Swagger + endpoints)

```python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import io
import hashlib
import os
from dotenv import load_dotenv
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from apps.api.deps import get_vector_store, get_captioner, get_embedder
from apps.api.routing_policy import should_use_cloud

load_dotenv()

app = FastAPI(title="AI Feature Router", version="0.1.0")

# Prometheus metrics
REGISTRY = CollectorRegistry()
ROUTED_LOCAL = Counter("router_local_total", "Local caption route count", registry=REGISTRY)
ROUTED_CLOUD = Counter("router_cloud_total", "Cloud caption route count", registry=REGISTRY)
LATENCY = Histogram("request_latency_ms", "Request latency (ms)", registry=REGISTRY, buckets=(50,100,200,400,800,1600,3200))

class ImageIn(BaseModel):
    url: Optional[str] = None

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return JSONResponse(content=generate_latest(REGISTRY).decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@app.post("/images")
async def ingest_image(payload: Optional[ImageIn] = None, file: Optional[UploadFile] = File(None)):
    if not payload and not file:
        raise HTTPException(400, "Provide either url or file")

    # Load bytes
    if file:
        img_bytes = await file.read()
        src = {"source": "upload", "filename": file.filename}
    else:
        import httpx
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(payload.url)
            r.raise_for_status()
            img_bytes = r.content
        src = {"source": "url", "url": payload.url}

    image_id = hashlib.sha256(img_bytes).hexdigest()[:16]

    # Caption (local first, maybe fallback)
    captioner = get_captioner()
    local_caption, conf, local_ms = await captioner.caption(img_bytes)

    use_cloud = should_use_cloud(confidence=conf, local_latency_ms=local_ms)
    caption = local_caption
    origin = "local"

    if use_cloud:
        cloud_caption, cloud_ms, cost_usd = await captioner.caption_cloud(img_bytes)
        if cloud_caption:
            caption = cloud_caption
            origin = "cloud"
            ROUTED_CLOUD.inc()
        else:
            ROUTED_LOCAL.inc()  # fallback failed → keep local
    else:
        ROUTED_LOCAL.inc()

    # Embeddings (image + caption text)
    embedder = get_embedder()
    img_vec = await embedder.embed_image(img_bytes)

    store = get_vector_store()
    await store.upsert_image(
        image_id=image_id,
        caption=caption,
        caption_confidence=conf,
        caption_origin=origin,
        img_vec=img_vec,
        payload={"src": src}
    )

    return {"id": image_id, "caption": caption, "origin": origin, "confidence": conf}

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    if not doc:
        raise HTTPException(404, "Not found")
    return doc

@app.get("/search")
async def search(q: str, k: int = 10):
    embedder = get_embedder()
    q_vec = await embedder.embed_text(q)
    store = get_vector_store()
    results = await store.search(query_vec=q_vec, k=k)
    return {"query": q, "results": results}
```

---

## apps/api/deps.py (providers & stores)

```python
import os
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.storage.qdrant_store import QdrantStore
from apps.api.services.captioner_client import CaptionerClient
from apps.api.services.embedder_client import EmbedderClient

_vector_store = None
_captioner = None
_embedder = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        backend = os.getenv("VECTOR_BACKEND", "pgvector").lower()
        if backend == "qdrant":
            _vector_store = QdrantStore()
        else:
            _vector_store = PgVectorStore()
    return _vector_store

def get_captioner():
    global _captioner
    if _captioner is None:
        _captioner = CaptionerClient()
    return _captioner

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = EmbedderClient()
    return _embedder
```

---

## apps/api/routing_policy.py (simple SLO + confidence rule)

```python
import os

CONF_T = float(os.getenv("CAPTION_CONFIDENCE_THRESHOLD", 0.55))
BUDGET_MS = int(os.getenv("CAPTION_LATENCY_BUDGET_MS", 600))

# TODO: include queue depth + moving p95 latency from metrics

def should_use_cloud(confidence: float, local_latency_ms: int) -> bool:
    return (confidence < CONF_T) or (local_latency_ms > BUDGET_MS)
```

---

## apps/api/storage/models.py (SQLAlchemy + pgvector DDL)

```python
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, Float, JSON, Text
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class ImageDoc(Base):
    __tablename__ = "images"
    id = mapped_column(String(64), primary_key=True)
    caption = mapped_column(Text)
    caption_confidence = mapped_column(Float)
    caption_origin = mapped_column(String(16))
    embed_vector = mapped_column(Vector(768))  # adjust to match encoder
    payload = mapped_column(JSON)
```

---

## apps/api/storage/pgvector_store.py (minimal async-ish interface)

```python
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from apps.api.storage.models import Base, ImageDoc

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
_engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=_engine)

# Initialize schema
with _engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=conn)
    conn.execute(text("CREATE INDEX IF NOT EXISTS images_vec_hnsw ON images USING hnsw (embed_vector vector_cosine_ops)"))

class PgVectorStore:
    async def upsert_image(self, image_id: str, caption: str, caption_confidence: float, caption_origin: str, img_vec, payload: dict):
        with Session() as s:
            doc = s.get(ImageDoc, image_id) or ImageDoc(id=image_id)
            doc.caption = caption
            doc.caption_confidence = caption_confidence
            doc.caption_origin = caption_origin
            doc.embed_vector = img_vec
            doc.payload = payload
            s.add(doc)
            s.commit()

    async def fetch_image(self, image_id: str):
        with Session() as s:
            doc = s.get(ImageDoc, image_id)
            return None if not doc else {
                "id": doc.id,
                "caption": doc.caption,
                "confidence": doc.caption_confidence,
                "origin": doc.caption_origin,
                "payload": doc.payload,
            }

    async def search(self, query_vec, k: int = 10):
        q = text("""
            SELECT id, caption, caption_confidence, caption_origin,
                   1 - (embed_vector <=> :qvec) AS score
            FROM images
            ORDER BY embed_vector <=> :qvec
            LIMIT :k
        """)
        with Session() as s:
            rows = s.execute(q, {"qvec": query_vec, "k": k}).fetchall()
            return [
                {"id": r.id, "caption": r.caption, "score": float(r.score)}
                for r in rows
            ]
```

---

## apps/api/storage/qdrant_store.py (stub)

```python
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

COLL = "images"

class QdrantStore:
    def __init__(self):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=url)
        try:
            self.client.get_collection(COLL)
        except Exception:
            self.client.recreate_collection(
                collection_name=COLL,
                vectors_config=qm.VectorParams(size=768, distance=qm.Distance.COSINE),
            )

    async def upsert_image(self, image_id: str, caption: str, caption_confidence: float, caption_origin: str, img_vec, payload: dict):
        self.client.upsert(COLL, points=[qm.PointStruct(id=image_id, vector=img_vec, payload={
            "caption": caption,
            "confidence": caption_confidence,
            "origin": caption_origin,
            **payload,
        })])

    async def fetch_image(self, image_id: str):
        r = self.client.retrieve(COLL, ids=[image_id])
        return None if not r else {"id": image_id, **(r[0].payload or {})}

    async def search(self, query_vec, k: int = 10):
        res = self.client.search(COLL, query_vector=query_vec, limit=k)
        return [{"id": p.id, "score": float(p.score), **(p.payload or {})} for p in res]
```

---

## apps/api/services/captioner_client.py (BLIP local + cloud stub)

```python
import time
from typing import Tuple, Optional
from PIL import Image
import io

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
    _BLIP_OK = True
except Exception:
    _BLIP_OK = False

_processor = None
_model = None

def _load_blip():
    global _processor, _model
    if _processor is None or _model is None:
        if not _BLIP_OK:
            raise RuntimeError("transformers/torch not available")
        _processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        _model.eval()

class CaptionerClient:
    async def caption(self, img_bytes: bytes) -> Tuple[str, float, int]:
        start = time.time()
        _load_blip()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        inputs = _processor(images=image, return_tensors="pt")
        with torch.no_grad():
            out = _model.generate(**inputs, max_new_tokens=30)
        text = _processor.decode(out[0], skip_special_tokens=True)
        # naive confidence proxy: inverse length penalty + basic heuristic
        conf = max(0.0, min(1.0, 0.9 - 0.005 * max(0, len(text) - 15)))
        ms = int((time.time() - start) * 1000)
        return text, conf, ms

    async def caption_cloud(self, img_bytes: bytes) -> Tuple[Optional[str], int, float]:
        # TODO: implement OpenAI/Gemini/Anthropic adapters
        # Return (caption, latency_ms, cost_usd)
        return None, 0, 0.0
```

---

## apps/api/services/embedder_client.py (OpenCLIP for image & text)

```python
import numpy as np
from PIL import Image
import io

try:
    import open_clip
    import torch
    _OK = True
except Exception:
    _OK = False

_model = None
_preprocess = None
_tokenizer = None


def _load_openclip():
    global _model, _preprocess, _tokenizer
    if _model is None:
        if not _OK:
            raise RuntimeError("open_clip/torch not available")
        _model, _, _preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        _tokenizer = open_clip.get_tokenizer("ViT-B-32")
        _model.eval()

class EmbedderClient:
    async def embed_image(self, img_bytes: bytes):
        _load_openclip()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        im = _preprocess(image).unsqueeze(0)
        with torch.no_grad():
            vec = _model.encode_image(im)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)

    async def embed_text(self, text: str):
        _load_openclip()
        toks = _tokenizer([text])
        with torch.no_grad():
            vec = _model.encode_text(toks)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)
```

---

## workers/captioner/captioner.py (optional background worker stub)

```python
# Placeholder for a queue‑based caption worker (Redis/Kafka). For MVP we do inline captions in the API.
```

---

## workers/embedder/embedder.py (optional background worker stub)

```python
# Placeholder for a queue‑based embedding worker. For MVP we do inline embeddings in the API.
```

---

## scripts/seed.py (seed a few images; URLs file based)

```python
"""
Seed script to ingest images from a CSV/TSV list:
  url,tag
Use:  python scripts/seed.py data/seed_urls.csv
"""
import sys, csv, asyncio, httpx

async def ingest(url: str, tag: str|None=None):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get("http://localhost:8000/images", params={"url": url})
        r.raise_for_status()
        print(url, r.json().get("id"), tag)

async def main(p):
    tasks = []
    with open(p, newline="") as f:
        for row in csv.DictReader(f):
            tasks.append(ingest(row["url"], row.get("tag")))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed.py data/seed_urls.csv")
        raise SystemExit(2)
    asyncio.run(main(sys.argv[1]))
```

---

## scripts/loadtest.js (k6 stub)

```javascript
import http from 'k6/http';
import { sleep } from 'k6';

export const options = { stages: [ { duration: '30s', target: 20 }, { duration: '1m', target: 100 } ] };

export default function () {
  const res = http.get('http://localhost:8000/search?q=beach%20at%20sunset&k=10');
  sleep(1);
}
```

---

## costs/providers.yaml (template)

```yaml
openai_gpt4o_mini:
  input_per_million: 0.15
  output_per_million: 0.60
gemini_flash_lite:
  input_per_million: 0.10
  output_per_million: 0.40
anthropic_claude_3_5_sonnet:
  input_per_million: 3.00
  output_per_million: 15.00
```

---

## infra/docker-compose.yml (pgvector + qdrant + grafana stack)

```yaml
version: '3.9'
services:
  postgres:
    image: ankane/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_router
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 10

  qdrant:
    image: qdrant/qdrant:v1.11.3
    ports: ["6333:6333"]

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    depends_on: [prometheus]

  jaeger:
    image: jaegertracing/all-in-one:1.58
    ports: ["16686:16686", "6831:6831/udp"]
```

---

## infra/prometheus/prometheus.yml (scrape API)

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: "api"
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

---

## .env.example

```
VECTOR_BACKEND=pgvector
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
CAPTION_CONFIDENCE_THRESHOLD=0.55
CAPTION_LATENCY_BUDGET_MS=600
```

---

### Next steps
- Wire cloud adapters in `captioner_client.py` (OpenAI/Gemini/Anthropic)
- Add `/metrics` exporter hook to expose cost counters
- Publish Grafana dashboard JSON
- Add unit tests and a tiny Next.js demo UI

