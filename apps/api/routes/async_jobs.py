from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Header
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
        img_bytes = await file.read()
        job_id = str(uuid.uuid4())
        
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
                "text_hint": x_client_caption,
                "client_confidence": x_client_confidence,
                "submitted_at": time.time()
            })
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/jobs/{job_id}"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to queue job: {str(e)}")

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    redis = Depends(get_redis)
):
    """Poll for job completion"""
    # Check ingestion result
    res = await redis.get(f"ingestion:result:{job_id}")
    
    status = "processing"
    result = {}
    
    if res:
        data = json.loads(res)
        if data.get("status") == "failed":
            status = "failed"
            result["error"] = data.get("error")
        else:
            status = "completed"
            result = {
                "image_id": data.get("image_id"),
                "caption": data.get("caption")
            }
            
    return {
        "job_id": job_id,
        "status": status,
        "result": result
    }
