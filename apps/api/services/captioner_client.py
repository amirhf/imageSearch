import time
from typing import Tuple, Optional
from PIL import Image
import io

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
    _BLIP_OK = True
except Exception:
    _BLIP_OK = False

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
    async def caption(self, img_bytes: bytes) -> Tuple[str, float, int]:
        start = time.time()
        _load_blip()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        inputs = _processor(images=image, return_tensors="pt")
        with torch.no_grad():
            out = _model.generate(**inputs, max_new_tokens=30)
        text = _processor.decode(out[0], skip_special_tokens=True)
        # naive confidence proxy: inverse length penalty + basic heuristic
        conf = max(0.0, min(1.0, 0.9 - 0.005 * max(0, len(text) - 15)))
        ms = int((time.time() - start) * 1000)
        return text, conf, ms

    async def caption_cloud(self, img_bytes: bytes) -> Tuple[Optional[str], int, float]:
        # TODO: implement OpenAI/Gemini/Anthropic adapters
        # Return (caption, latency_ms, cost_usd)
        return None, 0, 0.0
