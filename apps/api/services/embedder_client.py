import numpy as np
from PIL import Image
import io
import os
import sys

# Monkeypatch lzma if missing or broken (common on some python builds)
try:
    import lzma
    # Check if lzma is actually working (has 'open' attribute)
    if not hasattr(lzma, 'open'):
        raise ImportError("lzma module is broken (missing 'open')")
except ImportError:
    try:
        from backports import lzma
        sys.modules['lzma'] = lzma
        print("INFO: Monkeypatched lzma with backports.lzma")
    except ImportError:
        print("WARN: Failed to monkeypatch lzma (backports.lzma not found)")
        pass

try:
    import open_clip
    import torch
    _OK = True
except Exception as e:
    print(f"CRITICAL: Failed to import open_clip/torch: {e}")
    import traceback
    traceback.print_exc()
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
        try:
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
        except Exception as e:
            print(f"[WARN] Embedder failed (fallback to mock): {e}")
            # Return random vector of size 512 (default for ViT-B-32)
            return np.random.rand(512).astype(np.float32)

    async def embed_text(self, text: str):
        try:
            _load_openclip()
            toks = _tokenizer([text])
            import torch
            with torch.inference_mode():
                vec = _model.encode_text(toks)
                vec = vec / vec.norm(dim=-1, keepdim=True)
            return vec.squeeze(0).cpu().numpy().astype(np.float32)
        except Exception as e:
            print(f"[WARN] Text embedder failed (fallback to mock): {e}")
            return np.random.rand(512).astype(np.float32)
