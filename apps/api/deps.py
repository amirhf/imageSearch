import os
from apps.api.storage.pgvector_store import PgVectorStore
from apps.api.storage.qdrant_store import QdrantStore
from apps.api.services.image_storage import ImageStorage
from apps.api.services.local_file_storage import LocalFileStorage

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
        _captioner = CaptionerClient()
    return _captioner

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = EmbedderClient()
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
