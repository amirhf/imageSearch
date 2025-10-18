import numpy as np
from PIL import Image
import io

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
        _model, _, _preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        _tokenizer = open_clip.get_tokenizer("ViT-B-32")
        _model.eval()

class EmbedderClient:
    async def embed_image(self, img_bytes: bytes):
        _load_openclip()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        im = _preprocess(image).unsqueeze(0)
        with torch.no_grad():
            vec = _model.encode_image(im)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)

    async def embed_text(self, text: str):
        _load_openclip()
        toks = _tokenizer([text])
        with torch.no_grad():
            vec = _model.encode_text(toks)
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec.squeeze(0).cpu().numpy().astype(np.float32)
