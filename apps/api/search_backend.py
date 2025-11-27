from typing import Protocol, List, Optional, Dict, Any
from apps.api.schemas import SearchQuery, SearchResponse
from apps.api.deps import get_vector_store, get_embedder, get_image_storage

class SearchBackend(Protocol):
    async def search(self, query: SearchQuery) -> SearchResponse:
        ...

class PythonSearchBackend:
    async def search(self, query: SearchQuery) -> SearchResponse:
        embedder = get_embedder()
        q_vec = await embedder.embed_text(query.q)
        store = get_vector_store()
        
        results = await store.search(
            query_vec=q_vec,
            k=query.k,
            text_query=query.q,
            user_id=query.user_id,
            scope=query.scope
        )
        
        storage = get_image_storage()
        for result in results:
            image_id = result.get("id")
            if image_id:
                result["download_url"] = storage.get_image_url(image_id)
                result["thumbnail_url"] = storage.get_thumbnail_url(image_id)
                
        return SearchResponse(query=query.q, results=results)
