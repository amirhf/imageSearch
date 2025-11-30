import asyncio
import json
import os
import base64
import time
import hashlib
import io
from PIL import Image
from workers.base import BaseWorker, logger
from apps.api.services.captioner_client import CaptionerClient
from apps.api.services.embedder_client import EmbedderClient
from apps.api.services.routing.router import AIFeatureRouter, RoutingContext
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.services.image_storage import ImageStorage
from apps.api.services.cloud_providers.factory import CloudProviderFactory

class IngestionWorker(BaseWorker):
    QUEUE_NAME = "ingestion:jobs"
    RESULT_PREFIX = "ingestion:result:"

    def __init__(self, concurrency: int = 1):
        super().__init__(self.QUEUE_NAME, concurrency)
        self.captioner = CaptionerClient()
        self.embedder = EmbedderClient()
        self.router = AIFeatureRouter()
        self.db = PgVectorStore()
        # Initialize storage (S3/Local)
        # We need a concrete implementation. For now, we'll assume Local or S3 based on env.
        # But wait, ImageStorage is an abstract class. We need the factory or concrete class.
        # Let's check how main.py does it. It uses CloudProviderFactory? No, that's for LLMs.
        # apps/api/deps.py uses get_image_storage which returns LocalImageStorage or S3ImageStorage.
        # I'll implement a simple factory here or import the dependency logic.
        self.storage = self._init_storage()

    def _init_storage(self) -> ImageStorage:
        # Simple factory based on env
        from apps.api.services.local_file_storage import LocalFileStorage
        from apps.api.services.s3_storage import S3Storage
        
        if os.getenv("IMAGE_STORAGE_BACKEND", "local") == "s3":
            return S3Storage(
                bucket_name=os.getenv("S3_BUCKET_NAME"),
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),
                access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
                region_name=os.getenv("S3_REGION", "auto"),
                public_url_base=os.getenv("S3_PUBLIC_URL_BASE"),
                use_presigned_urls=os.getenv("S3_USE_PRESIGNED_URLS", "true").lower() == "true",
                presigned_url_expiry=int(os.getenv("S3_PRESIGNED_URL_EXPIRY", "3600"))
            )
        return LocalFileStorage()

    async def process_job(self, job: dict):
        job_id = job["job_id"]
        logger.info(f"Starting ingestion for job {job_id}")
        
        try:
            # 1. Decode Image
            image_bytes = base64.b64decode(job["image_b64"])
            
            # 2. Generate ID (Hash)
            image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
            
            # 3. Save to Storage
            # Check if exists first? Ideally yes, but upsert handles it.
            # We save first to ensure we have the path.
            meta = await self.storage.save_image(image_hash, image_bytes)
            
            # 4. Captioning (Router)
            decision = await self.router.route_caption_request(
                image_bytes=image_bytes,
                context=RoutingContext(latency_budget_ms=job.get("latency_budget_ms", 2000)),
                text_hint=job.get("text_hint"),
                client_confidence=job.get("client_confidence")
            )
            
            caption = ""
            conf = 0.0
            origin = "local"
            
            if decision.tier == "local":
                caption, conf, _ = await self.captioner.caption(image_bytes)
                origin = "local"
            elif decision.tier == "cloud":
                caption, _, _ = await self.captioner.caption_cloud(image_bytes)
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
            
            # 5. Embedding
            embedding = await self.embedder.embed_image(image_bytes)
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
                
            # 6. Save to DB
            payload = {
                "original_filename": job.get("filename", "unknown"),
                "content_type": job.get("content_type", "image/jpeg"),
                "job_id": job_id
            }
            
            await self.db.upsert_image(
                image_id=image_hash,
                caption=caption,
                caption_confidence=conf,
                caption_origin=origin,
                img_vec=embedding,
                payload=payload,
                file_path=meta.file_path,
                format=meta.format,
                size_bytes=meta.size_bytes,
                width=meta.width,
                height=meta.height,
                thumbnail_path=meta.thumbnail_path,
                owner_user_id=job.get("user_id"),
                visibility=job.get("visibility", "private")
            )
            
            # 7. Store Result in Redis (for polling)
            result = {
                "status": "completed",
                "image_id": image_hash,
                "caption": caption,
                "completed_at": time.time()
            }
            
            await self.redis.setex(
                f"{self.RESULT_PREFIX}{job_id}",
                3600,
                json.dumps(result)
            )
            logger.info(f"Ingestion complete for job {job_id} -> image {image_hash}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            await self.redis.setex(
                f"{self.RESULT_PREFIX}{job_id}",
                3600,
                json.dumps({"status": "failed", "error": str(e)})
            )

if __name__ == "__main__":
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "4"))
    worker = IngestionWorker(concurrency=concurrency)
    asyncio.run(worker.start())
