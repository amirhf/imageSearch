from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, Header
from apps.api.auth.dependencies import require_auth
from apps.api.auth.models import CurrentUser
from redis import asyncio as aioredis
import os
import json
import uuid
import base64
import time

router = APIRouter()

# Redis connection (lazy)
_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis

@router.post("/images/async")
async def ingest_image_async(
    file: UploadFile = File(...),
    visibility: str = Form("private"),
    priority: str = Query("normal", enum=["low", "normal", "high"]),
    user: CurrentUser = Depends(require_auth),
    redis = Depends(get_redis),
    x_client_caption: str = Header(None),
    x_client_confidence: float = Header(None)
):
    """
    Submit image for async processing.
    Returns job_id for polling.
    """
    try:
        if visibility not in ("private", "public", "public_admin"):
            raise HTTPException(400, "visibility must be 'private', 'public', or 'public_admin'")

        if visibility == "public_admin" and not user.is_admin():
            raise HTTPException(403, "Only admins can create public_admin images")

        img_bytes = await file.read()
        job_id = str(uuid.uuid4())
        submitted_at = time.time()
        job_meta = {
            "job_id": job_id,
            "user_id": user.id,
            "visibility": visibility,
            "filename": file.filename,
            "content_type": file.content_type,
            "priority": priority,
            "submitted_at": submitted_at,
        }

        await redis.setex(
            f"ingestion:job:{job_id}",
            3600,
            json.dumps(job_meta)
        )
        
        # Submit to ingestion queue
        await redis.lpush(
            "ingestion:jobs",
            json.dumps({
                "job_id": job_id,
                "image_b64": base64.b64encode(img_bytes).decode(),
                "user_id": user.id,
                "priority": priority,
                "filename": file.filename,
                "content_type": file.content_type,
                "visibility": visibility,
                "text_hint": x_client_caption,
                "client_confidence": x_client_confidence,
                "submitted_at": submitted_at
            })
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/jobs/{job_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to queue job: {str(e)}")

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    user: CurrentUser = Depends(require_auth),
    redis = Depends(get_redis)
):
    """Poll for job completion"""
    meta_res = await redis.get(f"ingestion:job:{job_id}")
    meta = json.loads(meta_res) if meta_res else {}

    if meta and meta.get("user_id") != user.id and not user.is_admin():
        raise HTTPException(404, "Job not found")

    # Check ingestion result
    res = await redis.get(f"ingestion:result:{job_id}")
    
    status = "processing"
    result = {}
    
    if res:
        data = json.loads(res)
        if data.get("user_id") and data.get("user_id") != user.id and not user.is_admin():
            raise HTTPException(404, "Job not found")

        if data.get("status") == "failed":
            status = "failed"
            result["error"] = data.get("error")
        else:
            status = "completed"
            base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
            image_id = data.get("image_id")
            result = {
                "image_id": image_id,
                "caption": data.get("caption"),
                "visibility": data.get("visibility") or meta.get("visibility"),
            }
            if image_id:
                result["download_url"] = f"{base_url}/images/{image_id}/download"
                result["thumbnail_url"] = f"{base_url}/images/{image_id}/thumbnail"
            
    return {
        "job_id": job_id,
        "status": status,
        "result": result,
        "submitted_at": meta.get("submitted_at"),
        "visibility": meta.get("visibility"),
    }
