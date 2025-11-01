import numpy as np
from PIL import Image
import io
import os

try:
    import open_clip
    import torch
    _OK = True
except Exception:
    _OK = False

_model = None
_preprocess = None
_tokenizer = None


def _load_openclip():
    global _model, _preprocess, _tokenizer
    if _model is None:
        if not _OK:
            raise RuntimeError("open_clip/torch not available")
        # Choose model from env (defaults to small CPU-friendly ViT-B-32)
        model_name = os.getenv("OPENCLIP_MODEL", "ViT-B-32")
        pretrained = os.getenv("OPENCLIP_PRETRAINED", "laion2b_s34b_b79k")
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        _tokenizer = open_clip.get_tokenizer("ViT-B-32")
        # Limit Torch threading to reduce memory spikes
        try:
            import torch
            torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))
            torch.set_num_interop_threads(int(os.getenv("TORCH_NUM_INTEROP_THREADS", "1")))
        except Exception:
            pass
        _model.eval()

class EmbedderClient:
    async def embed_image(self, img_bytes: bytes):
        _load_openclip()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Pre-resize to cap memory before preprocess (configurable)
        try:
            max_side = int(os.getenv("EMBED_MAX_SIDE", "768"))
        except Exception:
            max_side = 768
        if max_side and max_side > 0:
            image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        im = _preprocess(image).unsqueeze(0)
        import torch
        with torch.inference_mode():
            vec = _model.encode_image(im)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)

    async def embed_text(self, text: str):
        _load_openclip()
        toks = _tokenizer([text])
        import torch
        with torch.inference_mode():
            vec = _model.encode_text(toks)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)
