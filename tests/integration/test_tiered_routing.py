import pytest
import asyncio
import os
from httpx import AsyncClient
import hashlib
from apps.api.main import app
from apps.api.services.routing.tiers.cache_tier import SemanticCache

@pytest.mark.asyncio
async def test_tiered_routing_e2e():
    """
    Test the full routing flow with Redis.
    Requires Redis to be running (or mocked).
    For this test, we'll assume Redis is available or we mock it if needed.
    But ideally integration tests run against real infra.
    """
    # Skip if no Redis available (check env or try connect)
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        cache = SemanticCache(redis_url)
        await cache.connect()
        await cache.redis.ping()
    except Exception:
        pytest.skip("Redis not available")

    # Force mock models by patching deps
    import apps.api.deps
    apps.api.deps.USE_MOCK = "true"
    apps.api.deps._captioner = None # Reset singleton to force re-init
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Upload image (first time) -> Local/Cloud
        # We need to mock auth or use a test user.
        # For simplicity, we'll assume auth is disabled or mocked in test env,
        # OR we simulate auth headers.
        
        # Mocking auth dependency override
        from apps.api.auth.dependencies import require_auth
        from apps.api.auth.models import CurrentUser
        import uuid
        
        test_user_id = "00000000-0000-0000-0000-000000000001"
        app.dependency_overrides[require_auth] = lambda: CurrentUser(id=test_user_id, role="user", email="test@example.com")
        
        # Create a valid 1x1 JPEG image
        import io
        from PIL import Image
        img_byte_arr = io.BytesIO()
        Image.new('RGB', (1, 1), color='red').save(img_byte_arr, format='JPEG')
        valid_image_bytes = img_byte_arr.getvalue()
        
        files = {"file": ("atmosphere mood.jpg", valid_image_bytes, "image/jpeg")}
        
        response = await ac.post("/images", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # 2. Upload same image again -> Should be Cache Hit
        # We can't easily verify "Cache Hit" from API response unless we expose it in headers or metadata.
        # But we can verify latency is lower or check side effects.
        # Or we can check if the cache key exists in Redis.
        
        import hashlib
        img_hash = hashlib.sha256(valid_image_bytes).hexdigest()
        cache_key = f"caption:hash:{img_hash}"
        
        cached_val = await cache.redis.get(cache_key)
        assert cached_val is not None

@pytest.mark.asyncio
async def test_edge_routing_e2e():
    # Force mock models by patching deps
    import apps.api.deps
    apps.api.deps.USE_MOCK = "true"
    apps.api.deps._captioner = None 
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Mock auth
        from apps.api.auth.dependencies import require_auth
        from apps.api.auth.models import CurrentUser
        
        test_user_id = "00000000-0000-0000-0000-000000000001"
        app.dependency_overrides[require_auth] = lambda: CurrentUser(id=test_user_id, role="user", email="test@example.com")
        
        # Create valid image
        import io
        from PIL import Image
        img_byte_arr = io.BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(img_byte_arr, format='JPEG')
        valid_image_bytes = img_byte_arr.getvalue()
        
        # Ensure cache is clean
        from apps.api.services.routing.tiers.cache_tier import SemanticCache
        cache = SemanticCache()
        await cache.connect()
        img_hash = hashlib.sha256(valid_image_bytes).hexdigest()
        cache_key = f"caption:hash:{img_hash}"
        await cache.redis.delete(cache_key)
        
        files = {"file": ("edge_test.jpg", valid_image_bytes, "image/jpeg")}
        headers = {
            "x-client-caption": "a blue square",
            "x-client-confidence": "0.99"
        }
        
        # Send request with Edge headers
        response = await ac.post("/images", files=files, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify Edge was accepted
        # The response should contain the image metadata
        # We expect origin to be 'edge'
        assert data["caption"] == "a blue square"
        assert data["origin"] == "edge"
        
        # 3. Upload again
        response2 = await ac.post("/images", files=files)
        # Should still be edge (or cache if we implemented edge caching, but currently edge result is not cached in Redis, only Cloud result is)
        # Actually, Edge result is NOT cached in Redis in current implementation.
        # So it should be processed again as Edge.
        
        # Cleanup
        from apps.api.services.routing.tiers.cache_tier import SemanticCache
        cache = SemanticCache()
        await cache.connect()
        cache_key = hashlib.sha256(valid_image_bytes).hexdigest()
        await cache.redis.delete(cache_key)
        assert response2.status_code == 200
        
        # Clean up
        await cache.redis.delete(cache_key)
        app.dependency_overrides = {}
