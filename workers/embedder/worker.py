import asyncio
import json
import os
import base64
import time
from workers.base import BaseWorker, logger
from apps.api.services.embedder_client import EmbedderClient

class EmbeddingWorker(BaseWorker):
    QUEUE_NAME = "embedding:jobs"
    RESULT_PREFIX = "embedding:result:"

    def __init__(self, concurrency: int = 1):
        super().__init__(self.QUEUE_NAME, concurrency)
        self.embedder = EmbedderClient()

    async def process_job(self, job: dict):
        job_id = job["job_id"]
        try:
            image_bytes = base64.b64decode(job["image_b64"])
            
            # Generate embedding
            # embed_image returns a numpy array or list
            embedding = await self.embedder.embed_image(image_bytes)
            
            # Convert to list if numpy
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            # Store result
            result = {
                "status": "completed",
                "embedding": embedding,
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
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "2"))
    worker = EmbeddingWorker(concurrency=concurrency)
    asyncio.run(worker.start())
