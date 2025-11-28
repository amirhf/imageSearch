import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from apps.api.services.routing.tiers.cache_tier import SemanticCache

@pytest.mark.asyncio
async def test_semantic_cache_lookup_miss():
    cache = SemanticCache()
    cache.redis = AsyncMock()
    cache.redis.get = AsyncMock(return_value=None)
    
    result = await cache.lookup(b"fake_image")
    assert result is None
    cache.redis.get.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_cache_lookup_hit():
    cache = SemanticCache()
    cache.redis = AsyncMock()
    stored_data = {"caption": "test", "confidence": 0.9}
    cache.redis.get = AsyncMock(return_value=json.dumps(stored_data))
    
    result = await cache.lookup(b"fake_image")
    assert result == stored_data
    cache.redis.get.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_cache_store():
    cache = SemanticCache()
    cache.redis = AsyncMock()
    cache.redis.setex = AsyncMock()
    
    data = {"caption": "test"}
    await cache.store(b"fake_image", data)
    
    cache.redis.setex.assert_called_once()
