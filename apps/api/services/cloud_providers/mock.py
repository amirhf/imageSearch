"""Mock cloud provider for testing without API keys"""

import time
import hashlib
from .base import CloudCaptionProvider, CloudCaptionResponse


class MockCloudProvider(CloudCaptionProvider):
    """
    Mock cloud provider that generates deterministic captions.
    Useful for testing without API keys or offline development.
    """
    
    def __init__(self):
        self.model = "mock/test-model"
        self.input_cost = 0.0001  # Mock cost per 1M tokens
        self.output_cost = 0.0004
        print("[MockCloudProvider] Initialized (no API calls will be made)")
    
    async def caption(self, img_bytes: bytes) -> CloudCaptionResponse:
        """
        Generate mock caption based on image hash.
        Simulates cloud API latency.
        """
        start = time.time()
        
        # Simulate API latency (1-3 seconds)
        await self._simulate_latency()
        
        # Generate deterministic caption based on image hash
        img_hash = hashlib.sha256(img_bytes).hexdigest()[:8]
        captions = [
            "A beautiful landscape with mountains in the background",
            "A detailed close-up photograph showing intricate patterns",
            "An artistic composition with vibrant colors and textures",
            "A serene scene capturing natural lighting and shadows",
            "A modern abstract design with geometric elements",
        ]
        caption_idx = int(img_hash, 16) % len(captions)
        caption = captions[caption_idx]
        
        latency_ms = int((time.time() - start) * 1000)
        
        # Mock token usage
        input_tokens = 1000  # Typical image encoding
        output_tokens = len(caption.split())  # Rough token estimate
        
        cost_usd = self.calculate_cost(input_tokens, output_tokens)
        
        return CloudCaptionResponse(
            caption=caption,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    
    async def _simulate_latency(self):
        """Simulate API call latency"""
        import asyncio
        # Random latency between 1-3 seconds
        import random
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate mock cost"""
        input_cost = (input_tokens / 1_000_000) * self.input_cost
        output_cost = (output_tokens / 1_000_000) * self.output_cost
        total_cost = input_cost + output_cost
        # Ensure minimum cost to avoid rounding to 0
        return max(0.000001, round(total_cost, 6))
    
    def health_check(self) -> bool:
        """Mock provider is always available"""
        return True
    
    def get_provider_name(self) -> str:
        return "MockCloudProvider"
