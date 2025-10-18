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
    import traceback
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in ingest_image: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Internal error: {str(e)}")

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
