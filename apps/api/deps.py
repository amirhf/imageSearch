import os
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.storage.qdrant_store import QdrantStore

# Try to import real implementations, fall back to mocks if PyTorch unavailable
USE_MOCK = os.getenv("USE_MOCK_MODELS", "auto").lower()

CaptionerClient = None
EmbedderClient = None

if USE_MOCK == "true":
    print("[INFO] USE_MOCK_MODELS=true, using mock implementations")
    from apps.api.services.captioner_client_mock import CaptionerClient
    from apps.api.services.embedder_client_mock import EmbedderClient
elif USE_MOCK == "false":
    print("[INFO] USE_MOCK_MODELS=false, using real PyTorch models")
    from apps.api.services.captioner_client import CaptionerClient
    from apps.api.services.embedder_client import EmbedderClient
else:
    # Auto-detect: try real, fall back to mock
    try:
        # Test if we can actually use torch
        import torch
        torch.tensor([1.0])  # Quick test
        from apps.api.services.captioner_client import CaptionerClient
        from apps.api.services.embedder_client import EmbedderClient
        print("[INFO] PyTorch available, using real models")
    except Exception as e:
        print(f"[WARN] PyTorch unavailable ({e}), using mock implementations")
        from apps.api.services.captioner_client_mock import CaptionerClient
        from apps.api.services.embedder_client_mock import EmbedderClient

_vector_store = None
_captioner = None
_embedder = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        backend = os.getenv("VECTOR_BACKEND", "pgvector").lower()
        if backend == "qdrant":
            _vector_store = QdrantStore()
        else:
            _vector_store = PgVectorStore()
    return _vector_store

def get_captioner():
    global _captioner
    if _captioner is None:
        _captioner = CaptionerClient()
    return _captioner

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = EmbedderClient()
    return _embedder
