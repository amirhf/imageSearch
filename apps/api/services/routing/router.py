from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import time
import logging

logger = logging.getLogger("imagesearch.router")

class RoutingTier(str, Enum):
    EDGE = "edge"
    CACHE = "cache"
    LOCAL = "local"
    CLOUD = "cloud"

@dataclass
class RoutingDecision:
    tier: RoutingTier
    reason: str
    confidence: float
    latency_budget_ms: int
    fallback_chain: List[RoutingTier]
    metadata: Dict[str, Any] = None

@dataclass
class RoutingContext:
    latency_budget_ms: int = 600
    user_tier: str = "free"
    request_id: Optional[str] = None

class AIFeatureRouter:
    """
    Implements the Cascade of Intelligence pattern.
    Routes requests to the cheapest tier capable of handling them.
    """
    
    def __init__(self):
        from apps.api.services.routing.classifiers.complexity import ComplexityClassifier
        from apps.api.services.routing.tiers.cache_tier import SemanticCache
        import os
        
        self.classifier = ComplexityClassifier()
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache = SemanticCache(redis_url=redis_url)
    
    async def route_caption_request(
        self, 
        image_bytes: bytes,
        context: RoutingContext,
        text_hint: Optional[str] = None,
        client_confidence: Optional[float] = None
    ) -> RoutingDecision:
        """
        Decide which tier should handle the caption request.
        text_hint: Now represents the Client/Edge caption if available.
        """
        from apps.api.services.routing.metrics.routing_metrics import ROUTING_DECISIONS, ROUTING_LATENCY
        
        start_time = time.time()
        
        try:
            # 0. Check Cache (Tier 2)
            cached_result = await self.cache.lookup(image_bytes)
            if cached_result:
                ROUTING_DECISIONS.labels(tier="cache", reason="hit").inc()
                return RoutingDecision(
                    tier=RoutingTier.CACHE,
                    reason="cache_hit",
                    confidence=1.0,
                    latency_budget_ms=context.latency_budget_ms,
                    fallback_chain=[],
                    metadata={"cached_result": cached_result}
                )

            # 1. Analyze Edge Input (Tier 1)
            complexity_score = 1.0 # Default to complex (needs processing)
            
            if text_hint:
                # text_hint is now the client caption
                complexity = self.classifier.classify(text_hint)
                complexity_score = complexity.score
                
                # If Edge caption is high confidence AND simple enough -> Accept it
                # We trust Edge for simple things ("red shoes"), but not for complex ("cyberpunk...")
                # Actually, if it's simple, Edge is likely correct.
                # If it's complex, Edge might be hallucinating or missing detail -> Verify with Cloud/Local?
                # For now: If High Conf + Simple -> EDGE.
                
                edge_conf = client_confidence or 0.0
                print(f"DEBUG: text_hint='{text_hint}', conf={edge_conf}, complexity={complexity.level}")
                if edge_conf > 0.8 and complexity.level == "simple":
                    ROUTING_DECISIONS.labels(tier="edge", reason="accepted").inc()
                    return RoutingDecision(
                        tier=RoutingTier.EDGE,
                        reason="edge_accepted",
                        confidence=edge_conf,
                        latency_budget_ms=context.latency_budget_ms,
                        fallback_chain=[RoutingTier.LOCAL],
                        metadata={"complexity": complexity_score}
                    )

            # 2. Route based on complexity + SLO
            # Simple queries -> Local
            # Complex queries -> Cloud (if budget allows)
            
            tier = RoutingTier.LOCAL
            reason = "default_local"
            fallback = [RoutingTier.CLOUD]
            
            if complexity_score > 0.7:
                tier = RoutingTier.CLOUD
                reason = "high_complexity"
                fallback = [RoutingTier.LOCAL]
            elif context.latency_budget_ms < 200:
                tier = RoutingTier.LOCAL
                reason = "low_latency_budget"
                fallback = [RoutingTier.CLOUD]
                
            ROUTING_DECISIONS.labels(tier=tier.value, reason=reason).inc()
            
            return RoutingDecision(
                tier=tier,
                reason=reason,
                confidence=1.0,
                latency_budget_ms=context.latency_budget_ms,
                fallback_chain=fallback,
                metadata={"complexity": complexity_score}
            )
        finally:
            ROUTING_LATENCY.observe(time.time() - start_time)
