import asyncio
import logging
import os
import numpy as np
import httpx
from fastapi import HTTPException
from typing import List, Optional, Protocol
from apps.api.schemas import SearchQuery, SearchResponse, SearchResult
from apps.api.services.embedder_client import EmbedderClient
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.services.image_storage import ImageStorage

logger = logging.getLogger(__name__)

class SearchBackend(Protocol):
    async def search(self, query: SearchQuery) -> SearchResponse:
        ...

class PythonSearchBackend:
    def __init__(self, embedder: EmbedderClient, store: PgVectorStore, image_storage: ImageStorage):
        self.embedder = embedder
        self.store = store
        self.image_storage = image_storage

    async def search(self, query: SearchQuery) -> SearchResponse:
        # 1. Embed the query text
        q_vec = await self.embedder.embed_text(query.q)
        
        # 2. Search in vector store (hybrid)
        results = await self.store.search(
            query_vec=q_vec,
            k=query.k,
            text_query=query.q,
            user_id=query.user_id,
            scope=query.scope
        )
        
        # 3. Add image URLs
        for result in results:
            image_id = result.get("id")
            if image_id:
                result["download_url"] = self.image_storage.get_image_url(image_id)
                result["thumbnail_url"] = self.image_storage.get_thumbnail_url(image_id)
                
        # 4. Format response
        return SearchResponse(
            query=query.q,
            results=results
        )

class GoSearchBackend(SearchBackend):
    def __init__(self, go_url: str, embedder: EmbedderClient, image_storage: ImageStorage):
        self.go_url = go_url
        self.embedder = embedder
        self.image_storage = image_storage
        self.client = httpx.AsyncClient(timeout=5.0)  # 5s timeout

    async def search(self, query: SearchQuery) -> SearchResponse:
        # 1. Embed query
        vector = await self.embedder.embed_text(query.q)
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        
        # 2. Call Go Service
        payload = {
            "vector": vector,
            "k": query.k,
            "user_id": str(query.user_id) if query.user_id else "",
            "scope": query.scope,
            "text_query": query.q,
            "hybrid_boost": 0.3 # TODO: Configurable
        }
        
        try:
            resp = await self.client.post(f"{self.go_url}/search", json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results_data = data.get("results") or []
            results: List[SearchResult] = []
            # 4. Add image URLs and convert to SearchResult
            for result_item in results_data:
                image_id = result_item.get("id")
                if image_id:
                    result_item["download_url"] = self.image_storage.get_image_url(image_id)
                    result_item["thumbnail_url"] = self.image_storage.get_thumbnail_url(image_id)
                results.append(SearchResult(**result_item))
            
            return SearchResponse(
                query=query.q,
                results=results
            )
        except httpx.RequestError as e:
            logger.error(f"Go Service Request Error: {e}")
            raise HTTPException(status_code=503, detail=f"Search service unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Go Service HTTP Error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Search service error: {e.response.text}")

class ShadowSearchBackend(SearchBackend):
    def __init__(self, primary: SearchBackend, shadow: SearchBackend):
        self.primary = primary
        self.shadow = shadow

    async def search(self, query: SearchQuery) -> SearchResponse:
        # Start shadow request in background
        # Note: In a real production app, we might want to use a proper background task
        # or fire-and-forget mechanism to avoid any impact on the main request.
        # For now, we'll await both but suppress shadow errors, or just run shadow in background task.
        # Let's run shadow in background using asyncio.create_task to not block primary.
        
        async def run_shadow():
            try:
                start = asyncio.get_event_loop().time()
                shadow_results = await self.shadow.search(query)
                duration = asyncio.get_event_loop().time() - start
                logger.info(f"[Shadow] Search completed in {duration:.3f}s. Found {len(shadow_results.results)} results.")
            except Exception as e:
                logger.error(f"[Shadow] Search failed: {e}")

        # Run shadow query in background
        asyncio.create_task(run_shadow())
        
        # Return primary results immediately
        return await self.primary.search(query)
