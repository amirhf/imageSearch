"""Image management routes - upload, get, update, delete, list"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header, Response
from pydantic import BaseModel
from typing import Optional
import hashlib
import os
import time
import logging

from apps.api.deps import get_embedder, get_vector_store, get_image_storage, get_captioner
from apps.api.services.embedder_client import EmbedderClient
from apps.api.services.captioner_client import CaptionerClient
from apps.api.services.image_storage import ImageStorage
from apps.api.auth.dependencies import get_current_user, require_auth
from apps.api.auth.models import CurrentUser
from apps.api.services.routing.router import AIFeatureRouter, RoutingContext, RoutingTier

logger = logging.getLogger("imagesearch")

router = APIRouter(prefix="/images", tags=["images"])

# Import metrics from main module to avoid circular imports
from prometheus_client import Counter, Histogram

# These will be initialized when the module is imported
ROUTED_LOCAL = Counter("router_local_total", "Local caption route count")
ROUTED_CLOUD = Counter("router_cloud_total", "Cloud caption route count")
LATENCY = Histogram("request_latency_ms", "Request latency (ms)", buckets=(50,100,200,400,800,1600,3200))


class ImageUpdate(BaseModel):
    """Schema for updating image metadata"""
    visibility: Optional[str] = None


@router.post("")
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
        ai_router = AIFeatureRouter()
        try:
            budget_ms = int(os.getenv("CAPTION_LATENCY_BUDGET_MS", 600))
        except Exception:
            budget_ms = 600
            
        routing_decision = await ai_router.route_caption_request(
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
                await ai_router.cache.store(img_bytes, {
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


@router.get("")
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


@router.get("/{image_id}")
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


@router.get("/{image_id}/download")
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


@router.get("/{image_id}/thumbnail")
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


@router.patch("/{image_id}")
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


@router.delete("/{image_id}")
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
