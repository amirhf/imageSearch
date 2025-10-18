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
See `docs/adr/0001-routing-policy.md` for "Local‑first with Confidence & SLO Overrides".

## License
MIT (sample) – replace or update as you prefer.
