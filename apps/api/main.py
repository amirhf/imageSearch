from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request, Header, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import io
import hashlib
import os
import time
import logging
from prometheus_client import (
    Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST,
    REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR
)

from apps.api.schemas import SearchQuery
from apps.api.deps import get_embedder, get_vector_store, get_image_storage, get_captioner
from apps.api.services.embedder_client import EmbedderClient
from apps.api.services.captioner_client import CaptionerClient
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.services.image_storage import ImageStorage
from apps.api.auth.dependencies import get_current_user, require_auth, require_admin
from apps.api.auth.models import CurrentUser
from apps.api.auth.models import CurrentUser
from apps.api.routing_policy import should_use_cloud
from apps.api.services.routing.router import AIFeatureRouter, RoutingContext, RoutingTier

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

# Configure basic logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("imagesearch")


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

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3100",  # Next.js dev server
        "http://localhost:3000",  # Alternative port
        os.getenv("FRONTEND_URL", "http://localhost:3100")
    ],
    allow_origin_regex=r"https://image-search-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-client-caption", "x-client-confidence"],
    expose_headers=["*"]
)

from apps.api.routes import async_jobs
app.include_router(async_jobs.router)

class ImageIn(BaseModel):
    url: Optional[str] = None

@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok"}

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

@app.get("/_ah/health", include_in_schema=False)
def gcp_health():
    # Common GCP health endpoint
    return {"status": "ok"}


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.get("/auth/me")
async def get_me(current_user: Optional[CurrentUser] = Depends(get_current_user)):
    """
    Get current user info from JWT.
    Useful for debugging and client-side auth state management.
    Returns authenticated=false if no valid token provided.
    """
    if not current_user:
        return {
            "authenticated": False,
            "user": None
        }
    
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    }


@app.get("/auth/check")
async def check_auth(current_user: CurrentUser = Depends(require_auth)):
    """
    Protected endpoint to verify authentication.
    Returns 401 if not authenticated.
    Useful for testing auth flow.
    """
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    }


@app.get("/admin/health")
async def admin_health(admin: CurrentUser = Depends(require_admin)):
    """
    Admin-only endpoint for testing role-based access.
    Returns 403 if user is not an admin.
    """
    return {
        "status": "ok",
        "admin": {
            "id": admin.id,
            "email": admin.email
        }
    }


# ============================================================================
# Metrics Endpoint
# ============================================================================

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
    file: UploadFile = File(...),
    visibility: str = Form("private"),
    current_user: CurrentUser = Depends(require_auth),
    captioner: CaptionerClient = Depends(get_captioner),
    embedder: EmbedderClient = Depends(get_embedder),
    storage: ImageStorage = Depends(get_image_storage),
    x_client_caption: Optional[str] = Header(None),
    x_client_confidence: Optional[float] = Header(None)
):
    import traceback
    try:
        t0 = time.time()
        # Load bytes
        print(f"DEBUG: ingest_image headers: x_client_caption={x_client_caption}, x_client_confidence={x_client_confidence}")
        img_bytes = await file.read()
        src = {"source": "upload", "filename": file.filename}

        image_id = hashlib.sha256(img_bytes).hexdigest()[:16]

        # 1. Local Caption (always run for fallback/metrics)
        local_caption, local_conf, local_ms = await captioner.caption(img_bytes)

        # 2. Route Request (Tier 1/2/3/4)
        # We pass the client caption as a hint to the router
        router = AIFeatureRouter()
        try:
            budget_ms = int(os.getenv("CAPTION_LATENCY_BUDGET_MS", 600))
        except Exception:
            budget_ms = 600
            
        routing_decision = await router.route_caption_request(
            image_bytes=img_bytes,
            context=RoutingContext(latency_budget_ms=budget_ms),
            text_hint=x_client_caption,
            client_confidence=x_client_confidence
        )
        
        tier = routing_decision.tier
        caption = local_caption # Default to local caption
        origin = "local"
        conf = local_conf
        
        use_cloud = routing_decision.tier == RoutingTier.CLOUD
        use_cache = routing_decision.tier == RoutingTier.CACHE
        use_edge = routing_decision.tier == RoutingTier.EDGE
        
        logger.info(
            f"routing_decision: tier={routing_decision.tier} reason={routing_decision.reason}",
            extra={"tier": routing_decision.tier, "reason": routing_decision.reason}
        )
        
        if use_cache:
            # Cache hit!
            logger.info("routing: cache hit", extra={"tier": "cache"})
            cached = routing_decision.metadata.get("cached_result", {})
            caption = cached.get("caption", local_caption)
            origin = cached.get("origin", "cache")
            conf = cached.get("confidence", 1.0)
            
        elif use_edge:
            # Edge accepted!
            logger.info("routing: edge accepted", extra={"tier": "edge"})
            caption = x_client_caption
            origin = "edge"
            conf = x_client_confidence or 1.0
            
        elif use_cloud:
            logger.info("routing: attempting cloud caption", extra={"use_cloud": True})
            cloud_caption, cloud_ms, cost_usd = await captioner.caption_cloud(img_bytes)
            if cloud_caption:
                caption = cloud_caption
                origin = "cloud"
                ROUTED_CLOUD.inc()
                logger.info(
                    f"routing: cloud_success latency_ms={cloud_ms} cost_usd={cost_usd}",
                    extra={"cloud_latency_ms": cloud_ms, "cost_usd": cost_usd}
                )
                # Store in cache
                await router.cache.store(img_bytes, {
                    "caption": caption,
                    "confidence": 1.0, # Cloud is high conf
                    "origin": "cloud"
                })
            else:
                ROUTED_LOCAL.inc()  # fallback failed → keep local
                logger.warning("routing: cloud_fallback_failed; using local caption", extra={"use_cloud": True})
        else:
            ROUTED_LOCAL.inc()

        # Embeddings (image + caption text)
        embedder = get_embedder()
        img_vec = await embedder.embed_image(img_bytes)

        # Persist image and thumbnail to configured storage
        img_metadata = await storage.save_image(image_id=image_id, image_bytes=img_bytes, generate_thumbnail=True)

        # Validate visibility
        if visibility not in ("private", "public", "public_admin"):
            raise HTTPException(400, "visibility must be 'private', 'public', or 'public_admin'")
        
        # Only admins can create public_admin images
        if visibility == "public_admin" and not current_user.is_admin():
            raise HTTPException(403, "Only admins can create public_admin images")
        
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
            thumbnail_path=img_metadata.thumbnail_path,
            owner_user_id=current_user.id,
            visibility=visibility
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
        raise HTTPException(500, f"Internal error: {str(e)}")
    except Exception as e:
        import traceback
        with open("/tmp/api_error.log", "w") as f:
            f.write(f"Error: {str(e)}\n")
            traceback.print_exc(file=f)
        print(f"ERROR in ingest_image: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Internal error: {str(e)}")
    finally:
        try:
            LATENCY.observe(max(1.0, (time.time() - t0) * 1000.0))
        except Exception:
            pass

@app.get("/images/{image_id}")
async def get_image(
    image_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    if not doc:
        raise HTTPException(404, "Not found")
    
    # Check if image is deleted
    if doc.get("deleted_at"):
        raise HTTPException(404, "Image not found")
    
    # Access control
    owner_id = doc.get("owner_user_id")
    visibility = doc.get("visibility", "private")
    
    # Anonymous users can only see public images
    if not current_user:
        if visibility not in ("public", "public_admin"):
            raise HTTPException(401, "Authentication required")
    else:
        # Authenticated users: check access
        if not current_user.can_access_image(owner_id, visibility):
            raise HTTPException(403, "Access denied")
    
    # Prefer direct storage URLs (presigned/public) for performance
    storage = get_image_storage()
    doc["download_url"] = storage.get_image_url(image_id)
    doc["thumbnail_url"] = storage.get_thumbnail_url(image_id)
    
    return doc

@app.get("/images/{image_id}/download")
async def download_image(
    image_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """Download the original image file"""
    # Check access control first
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    if not doc or doc.get("deleted_at"):
        raise HTTPException(404, "Image not found")
    
    # Access control
    owner_id = doc.get("owner_user_id")
    visibility = doc.get("visibility", "private")
    
    if not current_user:
        if visibility not in ("public", "public_admin"):
            raise HTTPException(401, "Authentication required")
    else:
        if not current_user.can_access_image(owner_id, visibility):
            raise HTTPException(403, "Access denied")
    
    storage = get_image_storage()
    img_bytes = await storage.get_image(image_id)
    
    if not img_bytes:
        raise HTTPException(404, "Image not found")
    
    img_format = doc.get("format", "jpeg")
    
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
async def download_thumbnail(
    image_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """Download the thumbnail image"""
    # Check access control first
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    if not doc or doc.get("deleted_at"):
        raise HTTPException(404, "Thumbnail not found")
    
    # Access control
    owner_id = doc.get("owner_user_id")
    visibility = doc.get("visibility", "private")
    
    if not current_user:
        if visibility not in ("public", "public_admin"):
            raise HTTPException(401, "Authentication required")
    else:
        if not current_user.can_access_image(owner_id, visibility):
            raise HTTPException(403, "Access denied")
    
    storage = get_image_storage()
    thumb_bytes = await storage.get_thumbnail(image_id)
    
    if not thumb_bytes:
        raise HTTPException(404, "Thumbnail not found")
    
    img_format = doc.get("format", "jpeg")
    
    # Map format to MIME type
    mime_types = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }
    content_type = mime_types.get(img_format, "image/jpeg")
    
    return Response(content=thumb_bytes, media_type=content_type)

from apps.api.search_backend import PythonSearchBackend, GoSearchBackend, ShadowSearchBackend, SearchBackend

def get_search_backend(
    embedder: EmbedderClient = Depends(get_embedder),
    store: PgVectorStore = Depends(get_vector_store),
    image_storage: ImageStorage = Depends(get_image_storage),
) -> SearchBackend:
    backend_type = os.getenv("SEARCH_BACKEND", "python")
    go_url = os.getenv("GO_SEARCH_URL", "http://localhost:8080")
    shadow_mode = os.getenv("SEARCH_SHADOW_MODE", "false").lower() == "true"

    # Instantiate backends
    python_backend = PythonSearchBackend(embedder=embedder, store=store, image_storage=image_storage)
    # Only instantiate Go backend if needed (it's lightweight, so fine to do always)
    go_backend = GoSearchBackend(go_url=go_url, embedder=embedder, image_storage=image_storage)

    if shadow_mode:
        if backend_type == "go":
            return ShadowSearchBackend(primary=go_backend, shadow=python_backend)
        else:
            return ShadowSearchBackend(primary=python_backend, shadow=go_backend)

    if backend_type == "go":
        return go_backend
    return python_backend

@app.get("/search")
async def search(
    q: str,
    k: int = 10,
    scope: str = "all",
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    backend: SearchBackend = Depends(get_search_backend)
):
    """Search images with multi-tenant filtering.
    
    Args:
        q: Search query text
        k: Number of results to return
        scope: Search scope - 'all' (default), 'mine', or 'public'
            - 'all': My private images + all public images (requires auth)
            - 'mine': Only my images (requires auth)
            - 'public': Only public images (works for anonymous)
    """
    # Validate scope
    if scope not in ("all", "mine", "public"):
        raise HTTPException(400, "scope must be 'all', 'mine', or 'public'")
    
    # Scope validation
    if scope in ("all", "mine") and not current_user:
        raise HTTPException(401, "Authentication required for scope='" + scope + "'")
    
    t0 = time.time()
    
    try:
        user_id = current_user.id if current_user else None
        query = SearchQuery(q=q, k=k, scope=scope, user_id=user_id)
        return await backend.search(query)
    finally:
        try:
            LATENCY.observe(max(1.0, (time.time() - t0) * 1000.0))
        except Exception:
            pass


# ============================================================================
# Image Management Endpoints (Update/Delete)
# ============================================================================

class ImageUpdate(BaseModel):
    """Schema for updating image metadata"""
    visibility: Optional[str] = None


@app.patch("/images/{image_id}")
async def update_image(
    image_id: str,
    update: ImageUpdate,
    current_user: CurrentUser = Depends(require_auth)
):
    """Update image metadata (visibility, etc.)"""
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    
    if not doc or doc.get("deleted_at"):
        raise HTTPException(404, "Image not found")
    
    # Check modification permissions
    owner_id = doc.get("owner_user_id")
    if not current_user.can_modify_image(owner_id):
        raise HTTPException(403, "You don't have permission to modify this image")
    
    # Validate and update visibility
    if update.visibility is not None:
        if update.visibility not in ("private", "public", "public_admin"):
            raise HTTPException(400, "visibility must be 'private', 'public', or 'public_admin'")
        
        # Only admins can set public_admin
        if update.visibility == "public_admin" and not current_user.is_admin():
            raise HTTPException(403, "Only admins can set visibility to 'public_admin'")
        
        await store.update_visibility(image_id, update.visibility)
    
    # Fetch updated document
    updated_doc = await store.fetch_image(image_id)
    
    # Add storage URLs
    storage = get_image_storage()
    updated_doc["download_url"] = storage.get_image_url(image_id)
    updated_doc["thumbnail_url"] = storage.get_thumbnail_url(image_id)
    
    return updated_doc


@app.delete("/images/{image_id}")
async def delete_image(
    image_id: str,
    current_user: CurrentUser = Depends(require_auth)
):
    """Soft delete an image"""
    store = get_vector_store()
    doc = await store.fetch_image(image_id)
    
    if not doc:
        raise HTTPException(404, "Image not found")
    
    if doc.get("deleted_at"):
        raise HTTPException(404, "Image already deleted")
    
    # Check modification permissions
    owner_id = doc.get("owner_user_id")
    if not current_user.can_modify_image(owner_id):
        raise HTTPException(403, "You don't have permission to delete this image")
    
    # Soft delete
    await store.soft_delete_image(image_id)
    
    return {"message": "Image deleted successfully", "id": image_id}


@app.get("/images")
async def list_images(
    limit: int = 20,
    offset: int = 0,
    visibility: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """List images with filtering.
    
    Args:
        limit: Number of images to return (max 100)
        offset: Pagination offset
        visibility: Filter by visibility ('private', 'public', 'public_admin')
        
    Returns images based on user permissions:
    - Anonymous: Only public/public_admin images
    - Authenticated: Own images + public images
    - Admin: All images
    """
    if limit > 100:
        limit = 100
    
    store = get_vector_store()
    user_id = current_user.id if current_user else None
    is_admin = current_user.is_admin() if current_user else False
    
    images = await store.list_images(
        user_id=user_id,
        is_admin=is_admin,
        limit=limit,
        offset=offset,
        visibility_filter=visibility
    )
    
    # Add storage URLs
    storage = get_image_storage()
    for img in images:
        image_id = img.get("id")
        if image_id:
            img["download_url"] = storage.get_image_url(image_id)
            img["thumbnail_url"] = storage.get_thumbnail_url(image_id)
    
    return {
        "images": images,
        "limit": limit,
        "offset": offset,
        "count": len(images)
    }
