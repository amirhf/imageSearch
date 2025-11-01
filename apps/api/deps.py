import os
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.storage.qdrant_store import QdrantStore
from apps.api.services.image_storage import ImageStorage
from apps.api.services.local_file_storage import LocalFileStorage

# Global defaults
USE_MOCK = os.getenv("USE_MOCK_MODELS", "auto").lower()

# Component overrides (hybrid support)
USE_REAL_EMBEDDER = os.getenv("USE_REAL_EMBEDDER", "auto").lower()
USE_REAL_CAPTIONER = os.getenv("USE_REAL_CAPTIONER", "auto").lower()

CaptionerClient = None
EmbedderClient = None

def _select_captioner_class():
    # Explicit overrides first
    if USE_REAL_CAPTIONER == "true":
        try:
            from apps.api.services.captioner_client import CaptionerClient as RealCaptioner
            print("[INFO] Captioner: using REAL")
            return RealCaptioner
        except Exception as e:
            print(f"[WARN] Captioner REAL requested but unavailable: {e}. Falling back to MOCK")
            from apps.api.services.captioner_client_mock import CaptionerClient as MockCaptioner
            return MockCaptioner
    if USE_REAL_CAPTIONER == "false":
        from apps.api.services.captioner_client_mock import CaptionerClient as MockCaptioner
        print("[INFO] Captioner: forced MOCK")
        return MockCaptioner

    # Otherwise, use global USE_MOCK strategy
    if USE_MOCK == "true":
        from apps.api.services.captioner_client_mock import CaptionerClient as MockCaptioner
        print("[INFO] Captioner: MOCK (USE_MOCK_MODELS=true)")
        return MockCaptioner
    if USE_MOCK == "false":
        try:
            from apps.api.services.captioner_client import CaptionerClient as RealCaptioner
            print("[INFO] Captioner: REAL (USE_MOCK_MODELS=false)")
            return RealCaptioner
        except Exception as e:
            print(f"[WARN] Captioner REAL requested but unavailable: {e}. Falling back to MOCK")
            from apps.api.services.captioner_client_mock import CaptionerClient as MockCaptioner
            return MockCaptioner

    # Auto-detect
    try:
        import torch
        torch.tensor([1.0])
        from apps.api.services.captioner_client import CaptionerClient as RealCaptioner
        print("[INFO] Captioner: REAL (auto)")
        return RealCaptioner
    except Exception as e:
        print(f"[INFO] Captioner: MOCK (auto, {e})")
        from apps.api.services.captioner_client_mock import CaptionerClient as MockCaptioner
        return MockCaptioner


def _select_embedder_class():
    # Explicit overrides first
    if USE_REAL_EMBEDDER == "true":
        try:
            from apps.api.services.embedder_client import EmbedderClient as RealEmbedder
            print("[INFO] Embedder: using REAL")
            return RealEmbedder
        except Exception as e:
            print(f"[WARN] Embedder REAL requested but unavailable: {e}. Falling back to MOCK")
            from apps.api.services.embedder_client_mock import EmbedderClient as MockEmbedder
            return MockEmbedder
    if USE_REAL_EMBEDDER == "false":
        from apps.api.services.embedder_client_mock import EmbedderClient as MockEmbedder
        print("[INFO] Embedder: forced MOCK")
        return MockEmbedder

    # Otherwise, use global USE_MOCK strategy
    if USE_MOCK == "true":
        from apps.api.services.embedder_client_mock import EmbedderClient as MockEmbedder
        print("[INFO] Embedder: MOCK (USE_MOCK_MODELS=true)")
        return MockEmbedder
    if USE_MOCK == "false":
        try:
            from apps.api.services.embedder_client import EmbedderClient as RealEmbedder
            print("[INFO] Embedder: REAL (USE_MOCK_MODELS=false)")
            return RealEmbedder
        except Exception as e:
            print(f"[WARN] Embedder REAL requested but unavailable: {e}. Falling back to MOCK")
            from apps.api.services.embedder_client_mock import EmbedderClient as MockEmbedder
            return MockEmbedder

    # Auto-detect
    try:
        import torch
        torch.tensor([1.0])
        from apps.api.services.embedder_client import EmbedderClient as RealEmbedder
        print("[INFO] Embedder: REAL (auto)")
        return RealEmbedder
    except Exception as e:
        print(f"[INFO] Embedder: MOCK (auto, {e})")
        from apps.api.services.embedder_client_mock import EmbedderClient as MockEmbedder
        return MockEmbedder

_vector_store = None
_captioner = None
_embedder = None
_image_storage = None

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
        cls = _select_captioner_class()
        _captioner = cls()
    return _captioner

def get_embedder():
    global _embedder
    if _embedder is None:
        cls = _select_embedder_class()
        _embedder = cls()
    return _embedder

def get_image_storage() -> ImageStorage:
    global _image_storage
    if _image_storage is None:
        backend = os.getenv("IMAGE_STORAGE_BACKEND", "local").lower()
        
        if backend == "local":
            storage_path = os.getenv("IMAGE_STORAGE_PATH", "./storage/images")
            thumbnail_size = int(os.getenv("THUMBNAIL_SIZE", "256"))
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            _image_storage = LocalFileStorage(
                base_path=storage_path,
                thumbnail_size=thumbnail_size,
                base_url=base_url
            )
            print(f"[INFO] Using local file storage: {storage_path}")
            
        elif backend in ["s3", "minio"]:
            from apps.api.services.s3_storage import S3Storage
            
            bucket_name = os.getenv("S3_BUCKET_NAME", "imagesearch")
            endpoint_url = os.getenv("S3_ENDPOINT_URL")
            access_key = os.getenv("S3_ACCESS_KEY_ID")
            secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
            region = os.getenv("S3_REGION", "us-east-1")
            thumbnail_size = int(os.getenv("THUMBNAIL_SIZE", "256"))
            use_presigned = os.getenv("S3_USE_PRESIGNED_URLS", "true").lower() == "true"
            presigned_expiry = int(os.getenv("S3_PRESIGNED_URL_EXPIRY", "3600"))
            public_url_base = os.getenv("S3_PUBLIC_URL_BASE")
            
            # MinIO-specific defaults
            if backend == "minio":
                endpoint_url = endpoint_url or "http://localhost:9000"
                access_key = access_key or "minioadmin"
                secret_key = secret_key or "minioadmin"
                print(f"[INFO] Using MinIO storage: {endpoint_url}/{bucket_name}")
            else:
                print(f"[INFO] Using S3 storage: {bucket_name} (region: {region})")
            
            _image_storage = S3Storage(
                bucket_name=bucket_name,
                endpoint_url=endpoint_url,
                access_key_id=access_key,
                secret_access_key=secret_key,
                region_name=region,
                thumbnail_size=thumbnail_size,
                public_url_base=public_url_base,
                use_presigned_urls=use_presigned,
                presigned_url_expiry=presigned_expiry
            )
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")
    
    return _image_storage
