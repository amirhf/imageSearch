from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SearchQuery(BaseModel):
    q: str
    k: int = 10
    scope: str = "all"
    user_id: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    score: float
    caption: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    # Allow other fields
    model_config = {"extra": "allow"}

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
