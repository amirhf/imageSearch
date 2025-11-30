import time
from typing import Tuple, Optional
from PIL import Image
import io
import sys

# Monkeypatch lzma if missing (common on some python builds)
try:
    import lzma
except ImportError:
    try:
        from backports import lzma
        sys.modules['lzma'] = lzma
    except ImportError:
        pass

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
    _BLIP_OK = True
except Exception as e:
    print(f"DEBUG: Failed to import transformers/torch: {e}")
    import traceback
    traceback.print_exc()
    _BLIP_OK = False

from apps.api.services.cloud_providers.factory import CloudProviderFactory
from apps.api.services.cloud_providers.circuit_breaker import get_circuit_breaker

_processor = None
_model = None

def _load_blip():
    global _processor, _model
    if _processor is None or _model is None:
        if not _BLIP_OK:
            raise RuntimeError("transformers/torch not available")
        _processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        _model.eval()

class CaptionerClient:
    def __init__(self):
        """Initialize captioner with lazy-loaded cloud provider"""
        self._cloud_provider = None
        self._circuit_breaker = get_circuit_breaker()
    
    def _get_cloud_provider(self):
        """Lazy load cloud provider"""
        if self._cloud_provider is None:
            try:
                self._cloud_provider = CloudProviderFactory.create()
                print(f"[CaptionerClient] Cloud provider initialized: {self._cloud_provider.get_provider_name()}")
            except Exception as e:
                print(f"[WARN] Could not initialize cloud provider: {e}")
                self._cloud_provider = None
        return self._cloud_provider
    
    async def caption(self, img_bytes: bytes) -> Tuple[str, float, int]:
        start = time.time()
        try:
            _load_blip()
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            inputs = _processor(images=image, return_tensors="pt")
            with torch.no_grad():
                out = _model.generate(**inputs, max_new_tokens=30)
            text = _processor.decode(out[0], skip_special_tokens=True)
            # naive confidence proxy: inverse length penalty + basic heuristic
            conf = max(0.0, min(1.0, 0.9 - 0.005 * max(0, len(text) - 15)))
        except Exception as e:
            print(f"[WARN] Local captioner failed/disabled: {e}")
            # Fallback to cloud
            cloud_caption, _, _ = await self.caption_cloud(img_bytes)
            if cloud_caption:
                return cloud_caption, 1.0, int((time.time() - start) * 1000)
            
            print(f"[WARN] Cloud captioner also failed (fallback to mock)")
            text = "a mock caption for the image"
            conf = 0.5
            
        ms = int((time.time() - start) * 1000)
        return text, conf, ms

    async def caption_cloud(self, img_bytes: bytes) -> Tuple[Optional[str], int, float]:
        """
        Generate caption using cloud provider (OpenRouter).
        
        Returns:
            Tuple of (caption, latency_ms, cost_usd)
            Returns (None, 0, 0.0) if cloud provider unavailable or circuit breaker open
        """
        # Check circuit breaker
        can_proceed, reason = self._circuit_breaker.can_proceed()
        if not can_proceed:
            print(f"[CaptionerClient] {reason}")
            return None, 0, 0.0
        
        try:
            provider = self._get_cloud_provider()
            if provider is None:
                return None, 0, 0.0
            
            # Make cloud API call
            response = await provider.caption(img_bytes)
            
            # Record success
            self._circuit_breaker.record_success()
            
            return (response.caption, response.latency_ms, response.cost_usd)
        
        except Exception as e:
            # Record failure
            self._circuit_breaker.record_failure()
            print(f"[ERROR] Cloud caption failed: {e}")
            return None, 0, 0.0
