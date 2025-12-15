"""Search routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import os
import time

from apps.api.schemas import SearchQuery
from apps.api.deps import get_embedder, get_vector_store, get_image_storage
from apps.api.services.embedder_client import EmbedderClient
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.services.image_storage import ImageStorage
from apps.api.auth.dependencies import get_current_user
from apps.api.auth.models import CurrentUser
from apps.api.search_backend import PythonSearchBackend, GoSearchBackend, ShadowSearchBackend, SearchBackend

from prometheus_client import Histogram

LATENCY = Histogram("search_latency_ms", "Search latency (ms)", buckets=(50,100,200,400,800,1600,3200))

router = APIRouter(tags=["search"])


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


@router.get("/search")
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
