"""Mock embedder for testing without PyTorch - generates deterministic fake embeddings"""
import numpy as np
import hashlib

class EmbedderClient:
    """Mock implementation that doesn't require PyTorch"""
    
    def _hash_to_vector(self, data: bytes, dim: int = 512) -> np.ndarray:
        """Generate deterministic vector from hash"""
        # Use hash to seed random generator for reproducibility
        hash_int = int(hashlib.md5(data).hexdigest(), 16)
        rng = np.random.RandomState(hash_int % (2**32))
        
        # Generate random vector
        vec = rng.randn(dim).astype(np.float32)
        
        # Normalize to unit length (like real CLIP embeddings)
        vec = vec / np.linalg.norm(vec)
        
        return vec
    
    async def embed_image(self, img_bytes: bytes) -> np.ndarray:
        """Generate mock image embedding"""
        return self._hash_to_vector(img_bytes, 512)
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate mock text embedding"""
        # Add prefix to differentiate text from images
        text_bytes = f"text:{text}".encode('utf-8')
        return self._hash_to_vector(text_bytes, 512)
