import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.services.routing.router import AIFeatureRouter, RoutingContext, RoutingTier

@pytest.mark.asyncio
async def test_router_default_local():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value=None)
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=600)
        
        # Simple image/hint -> Local
        decision = await router.route_caption_request(b"fake_image", context, text_hint="simple shoes")
        
        assert decision.tier == RoutingTier.LOCAL
        assert decision.reason == "default_local"

@pytest.mark.asyncio
async def test_router_complex_cloud():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value=None)
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=2000)
        
        # Complex hint -> Cloud
        decision = await router.route_caption_request(
            b"fake_image", 
            context, 
            text_hint="melancholic cyberpunk atmosphere"
        )
        
        assert decision.tier == RoutingTier.CLOUD
        assert decision.reason == "high_complexity"

@pytest.mark.asyncio
async def test_router_cache_hit():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value={"caption": "cached caption"})
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=600)
        
        decision = await router.route_caption_request(b"fake_image", context)
        
        assert decision.tier == RoutingTier.CACHE
        assert decision.reason == "cache_hit"
        assert decision.metadata["cached_result"]["caption"] == "cached caption"

@pytest.mark.asyncio
async def test_router_edge_accepted():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value=None)
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=600)
        
        # Edge caption provided, simple, high confidence -> Accept
        decision = await router.route_caption_request(
            b"fake_image", 
            context, 
            text_hint="a red shoe",
            client_confidence=0.95
        )
        
        assert decision.tier == RoutingTier.EDGE
        assert decision.reason == "edge_accepted"
        assert decision.confidence == 0.95

@pytest.mark.asyncio
async def test_router_edge_rejected_complex():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value=None)
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=600)
        
        # Edge caption provided, but complex -> Reject Edge, go to Cloud (or Local)
        decision = await router.route_caption_request(
            b"fake_image", 
            context, 
            text_hint="a melancholic atmosphere with cyberpunk vibes",
            client_confidence=0.95
        )
        
        # Should NOT be EDGE. Should be CLOUD due to complexity.
        assert decision.tier == RoutingTier.CLOUD
        assert decision.reason == "high_complexity"

@pytest.mark.asyncio
async def test_router_edge_rejected_low_conf():
    with patch("apps.api.services.routing.tiers.cache_tier.SemanticCache") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.lookup = AsyncMock(return_value=None)
        
        router = AIFeatureRouter()
        context = RoutingContext(latency_budget_ms=600)
        
        # Edge caption provided, simple, but LOW confidence -> Reject Edge
        decision = await router.route_caption_request(
            b"fake_image", 
            context, 
            text_hint="a red shoe",
            client_confidence=0.5
        )
        
        # Should fall back to LOCAL (default)
        assert decision.tier == RoutingTier.LOCAL
