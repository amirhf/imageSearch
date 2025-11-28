import json
import time
import hashlib
import logging
from typing import Optional, Dict, Any, List
import numpy as np
from redis import asyncio as aioredis
from apps.api.services.embedder_client import EmbedderClient
from apps.api.services.routing.metrics.routing_metrics import CACHE_HITS, CACHE_MISSES

logger = logging.getLogger("imagesearch.cache")

class SemanticCache:
    """
    Caches results by semantic similarity, not exact match.
    "happy dog" and "cheerful puppy" return the same cached result.
    """
    
    SIMILARITY_THRESHOLD = 0.95
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
        self.embedder = None
        
    async def connect(self):
        if not self.redis:
            self.redis = await aioredis.from_url(self.redis_url)
            
    async def _get_embedder(self):
        # Lazy load to avoid circular deps or early init issues
        if not self.embedder:
            from apps.api.deps import get_embedder
            self.embedder = get_embedder()
        return self.embedder

    async def lookup(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Check cache for semantically similar image.
        For images, we use exact hash for Tier 1 (Edge/Exact) 
        and could use embedding similarity for Tier 2.
        
        For this implementation, we'll start with exact hash caching 
        as a proxy for "semantic" cache of the *same* image content,
        since we don't have a text query here yet (it's image-to-caption).
        
        Future: Store image embedding and search vector space in Redis (RediSearch).
        """
        await self.connect()
        
        # 1. Exact match (Hash) - Tier 1 behavior
        img_hash = hashlib.sha256(image_bytes).hexdigest()
        cache_key = f"caption:hash:{img_hash}"
        
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            CACHE_HITS.labels(tier="exact").inc()
            return json.loads(cached_data)
            
        CACHE_MISSES.labels(tier="exact").inc()
        return None
    
    async def store(self, image_bytes: bytes, result: Dict[str, Any]):
        await self.connect()
        
        img_hash = hashlib.sha256(image_bytes).hexdigest()
        cache_key = f"caption:hash:{img_hash}"
        
        await self.redis.setex(
            cache_key,
            self.CACHE_TTL,
            json.dumps(result)
        )
