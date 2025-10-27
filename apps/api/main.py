from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import io
import hashlib
import os
from dotenv import load_dotenv
from prometheus_client import (
    Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST,
    REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR
)

from apps.api.deps import get_vector_store, get_captioner, get_embedder, get_image_storage
from apps.api.routing_policy import should_use_cloud

load_dotenv()

# Disable automatic _created metrics to reduce noise in Grafana
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = 'True'

# Disable default Python collectors (GC, platform, process) to reduce noise
try:
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(GC_COLLECTOR)
except Exception:
    pass  # Already unregistered or not present

# Prometheus metrics for router - defined at module level
ROUTED_LOCAL = Counter("router_local_total", "Local caption route count")
ROUTED_CLOUD = Counter("router_cloud_total", "Cloud caption route count")
LATENCY = Histogram("request_latency_ms", "Request latency (ms)", buckets=(50,100,200,400,800,1600,3200))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize metrics on startup.
    This ensures all metrics are registered in the same REGISTRY instance.
    """
    # Initialize cloud provider metrics after app is created
    from apps.api.services.cloud_providers.metrics import get_metrics
    from apps.api.services.cloud_providers.rate_limiter import get_rate_limiter
    from apps.api.services.cloud_providers.circuit_breaker import get_circuit_breaker
    from apps.api.services.cloud_providers.factory import CloudProviderFactory
    
    _ = get_metrics()
    _ = get_rate_limiter()
    _ = get_circuit_breaker()
    
    try:
        _ = CloudProviderFactory.create()
    except Exception as e:
        print(f"[WARNING] Could not initialize cloud provider: {e}")
    
    yield


app = FastAPI(title="AI Feature Router", version="0.1.0", lifespan=lifespan)

class ImageIn(BaseModel):
    url: Optional[str] = None

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

async def _generate_metrics_async():
    """Helper to generate metrics in thread pool to avoid blocking"""
    import asyncio
    from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST
    
    # Run in thread pool to prevent blocking event loop
    loop = asyncio.get_event_loop()
    metrics_output = await loop.run_in_executor(None, generate_latest, REGISTRY)
    return metrics_output, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    import asyncio
    
    try:
        # Use timeout to prevent hanging
        metrics_output, content_type = await asyncio.wait_for(
            _generate_metrics_async(), 
            timeout=5.0
        )
        return Response(content=metrics_output, media_type=content_type)
    except asyncio.TimeoutError:
        return Response(content="Metrics generation timed out", status_code=504)
    except Exception as e:
        return Response(content=f"Error generating metrics: {str(e)}", status_code=500)

@app.post("/images")
async def ingest_image(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    import traceback
    try:
        if not file and not url:
            raise HTTPException(400, "Provide either url or file")

        # Load bytes
        if file:
            img_bytes = await file.read()
            src = {"source": "upload", "filename": file.filename}
        else:
            import httpx
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                img_bytes = r.content
            src = {"source": "url", "url": url}

        image_id = hashlib.sha256(img_bytes).hexdigest()[:16]

        # Save image to storage
        storage = get_image_storage()
        img_metadata = await storage.save_image(image_id, img_bytes, generate_thumbnail=True)

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
            payload={"src": src},
            file_path=img_metadata.file_path,
            format=img_metadata.format,
            size_bytes=img_metadata.size_bytes,
            width=img_metadata.width,
            height=img_metadata.height,
            thumbnail_path=img_metadata.thumbnail_path
        )

        base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
        return {
            "id": image_id, 
            "caption": caption, 
            "origin": origin, 
            "confidence": conf,
            "download_url": f"{base_url}/images/{image_id}/download",
            "thumbnail_url": f"{base_url}/images/{image_id}/thumbnail",
            "width": img_metadata.width,
            "height": img_metadata.height,
            "size_bytes": img_metadata.size_bytes,
            "format": img_metadata.format
        }
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
    
    # Add API download URLs
    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    doc["download_url"] = f"{base_url}/images/{image_id}/download"
    doc["thumbnail_url"] = f"{base_url}/images/{image_id}/thumbnail"
    
    return doc

@app.get("/images/{image_id}/download")
async def download_image(image_id: str):
    """Download the original image file"""
    storage = get_image_storage()
    img_bytes = await storage.get_image(image_id)
    
    if not img_bytes:
        raise HTTPException(404, "Image not found")
    
    # Get format from database for correct content-type
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    img_format = doc.get("format", "jpeg") if doc else "jpeg"
    
    # Map format to MIME type
    mime_types = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }
    content_type = mime_types.get(img_format, "image/jpeg")
    
    return Response(content=img_bytes, media_type=content_type)

@app.get("/images/{image_id}/thumbnail")
async def download_thumbnail(image_id: str):
    """Download the thumbnail image"""
    storage = get_image_storage()
    thumb_bytes = await storage.get_thumbnail(image_id)
    
    if not thumb_bytes:
        raise HTTPException(404, "Thumbnail not found")
    
    # Get format from database
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    img_format = doc.get("format", "jpeg") if doc else "jpeg"
    
    # Map format to MIME type
    mime_types = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }
    content_type = mime_types.get(img_format, "image/jpeg")
    
    return Response(content=thumb_bytes, media_type=content_type)

@app.get("/search")
async def search(q: str, k: int = 10):
    embedder = get_embedder()
    q_vec = await embedder.embed_text(q)
    store = get_vector_store()
    results = await store.search(query_vec=q_vec, k=k)
    
    # Add API download URLs to each result (avoid direct storage URLs)
    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    for result in results:
        image_id = result.get("id")
        if image_id:
            result["download_url"] = f"{base_url}/images/{image_id}/download"
            result["thumbnail_url"] = f"{base_url}/images/{image_id}/thumbnail"
    
    return {"query": q, "results": results}
