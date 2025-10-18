"""Mock captioner for testing without PyTorch - generates fake captions"""
import time
import hashlib
from typing import Tuple, Optional

class CaptionerClient:
    """Mock implementation that doesn't require PyTorch"""
    
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
        """Mock cloud caption - not implemented"""
        return None, 0, 0.0
