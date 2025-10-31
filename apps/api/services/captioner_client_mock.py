"""Mock captioner for testing without PyTorch - generates fake captions"""
import time
import hashlib
from typing import Tuple, Optional
from apps.api.services.cloud_providers.factory import CloudProviderFactory
from apps.api.services.cloud_providers.circuit_breaker import get_circuit_breaker

class CaptionerClient:
    """Mock implementation that doesn't require PyTorch.

    Also supports cloud fallback via CloudProviderFactory so that
    USE_MOCK_MODELS=true can still route to cloud providers.
    """

    def __init__(self):
        self._cloud_provider = None
        self._circuit_breaker = get_circuit_breaker()

    def _get_cloud_provider(self):
        if self._cloud_provider is None:
            try:
                self._cloud_provider = CloudProviderFactory.create()
                print(f"[MockCaptioner] Cloud provider initialized: {self._cloud_provider.get_provider_name()}")
            except Exception as e:
                print(f"[WARN] MockCaptioner: could not initialize cloud provider: {e}")
                self._cloud_provider = None
        return self._cloud_provider

    async def caption(self, img_bytes: bytes) -> Tuple[str, float, int]:
        """Generate a mock caption based on image hash"""
        start = time.time()
        
        # Generate deterministic caption from image hash
        img_hash = hashlib.md5(img_bytes).hexdigest()[:8]
        
        # Simple caption variations
        captions = [
            "a photo of an outdoor scene with natural lighting",
            "an image showing various objects in a room",
            "a picture of a landscape with interesting features",
            "a colorful scene with multiple elements",
            "a photograph captured in good lighting conditions"
        ]
        
        # Pick caption based on hash
        caption_idx = int(img_hash, 16) % len(captions)
        caption = captions[caption_idx]
        
        # Mock confidence (deterministic based on hash)
        confidence = 0.75 + (int(img_hash[:2], 16) / 255.0) * 0.2
        
        ms = int((time.time() - start) * 1000)
        
        return caption, confidence, ms
    
    async def caption_cloud(self, img_bytes: bytes) -> Tuple[Optional[str], int, float]:
        """Cloud caption via configured provider (OpenRouter, etc.)."""
        # Check circuit breaker
        can_proceed, reason = self._circuit_breaker.can_proceed()
        if not can_proceed:
            print(f"[MockCaptioner] Cloud caption blocked by circuit breaker: {reason}")
            return None, 0, 0.0

        try:
            provider = self._get_cloud_provider()
            if provider is None:
                print("[MockCaptioner] No cloud provider available")
                return None, 0, 0.0

            response = await provider.caption(img_bytes)
            self._circuit_breaker.record_success()
            return response.caption, response.latency_ms, response.cost_usd

        except Exception as e:
            self._circuit_breaker.record_failure()
            print(f"[ERROR] MockCaptioner cloud caption failed: {e}")
            return None, 0, 0.0
