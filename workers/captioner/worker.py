import asyncio
import json
import os
import base64
import time
from workers.base import BaseWorker, logger
from apps.api.services.captioner_client import CaptionerClient
from apps.api.services.routing.router import AIFeatureRouter, RoutingContext
from apps.api.schemas import CaptionRequest

class CaptionWorker(BaseWorker):
    QUEUE_NAME = "caption:jobs"
    RESULT_PREFIX = "caption:result:"

    def __init__(self, concurrency: int = 1):
        super().__init__(self.QUEUE_NAME, concurrency)
        self.captioner = CaptionerClient()
        self.router = AIFeatureRouter()

    async def process_job(self, job: dict):
        job_id = job["job_id"]
        try:
            image_bytes = base64.b64decode(job["image_b64"])
            
            # Use router to decide tier
            # Note: We create a dummy request object if needed, or update router to accept bytes
            # The router.route_caption_request expects image_bytes directly in current impl
            
            decision = await self.router.route_caption_request(
                image_bytes=image_bytes,
                context=RoutingContext(latency_budget_ms=job.get("latency_budget_ms", 2000)),
                text_hint=job.get("text_hint"),
                client_confidence=job.get("client_confidence")
            )
            
            caption = ""
            conf = 0.0
            origin = "local"
            latency = 0
            
            # Execute based on routing decision
            # (Logic copied/adapted from main.py ingest_image)
            
            if decision.tier == "local":
                caption, conf, latency = await self.captioner.caption(image_bytes)
                origin = "local"
            elif decision.tier == "cloud":
                caption, latency, cost = await self.captioner.caption_cloud(image_bytes)
                conf = 0.95
                origin = "cloud"
            elif decision.tier == "edge":
                caption = job.get("text_hint", "")
                conf = job.get("client_confidence", 1.0)
                origin = "edge"
            elif decision.tier == "cache":
                cached = decision.metadata.get("cached_result", {})
                caption = cached.get("caption", "")
                conf = cached.get("confidence", 1.0)
                origin = cached.get("origin", "cache")
            
            # Store result
            result = {
                "status": "completed",
                "caption": caption,
                "confidence": conf,
                "origin": origin,
                "tier": str(decision.tier),
                "latency_ms": latency,
                "completed_at": time.time()
            }
            
            await self.redis.setex(
                f"{self.RESULT_PREFIX}{job_id}",
                3600,
                json.dumps(result)
            )
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self.redis.setex(
                f"{self.RESULT_PREFIX}{job_id}",
                3600,
                json.dumps({"status": "failed", "error": str(e)})
            )

if __name__ == "__main__":
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "4"))
    worker = CaptionWorker(concurrency=concurrency)
    asyncio.run(worker.start())
