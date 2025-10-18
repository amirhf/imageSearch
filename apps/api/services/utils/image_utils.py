"""Image utility functions"""

import base64
from typing import Optional
from PIL import Image
import io


def encode_image_base64(img_bytes: bytes, format: str = "JPEG") -> str:
    """
    Encode image bytes to base64 string.
    
    Args:
        img_bytes: Raw image bytes
        format: Image format (JPEG, PNG, etc.)
        
    Returns:
        Base64 encoded string
        
    Raises:
        ValueError: If image bytes are invalid
    """
    if not img_bytes:
        raise ValueError("Image bytes cannot be empty")
    
    try:
        # Validate the image can be loaded
        img = Image.open(io.BytesIO(img_bytes))
        img.verify()
        
        # Re-open for encoding (verify closes the file)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to RGB if needed (handles RGBA, L, etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Encode to base64
        b64_string = base64.b64encode(img_bytes).decode('utf-8')
        return b64_string
        
    except Exception as e:
        raise ValueError(f"Invalid image bytes: {e}")


def validate_image_bytes(img_bytes: bytes, max_size_mb: float = 10.0) -> tuple[bool, Optional[str]]:
    """
    Validate image bytes.
    
    Args:
        img_bytes: Raw image bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not img_bytes:
        return False, "Image bytes cannot be empty"
    
    # Check size
    size_mb = len(img_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"Image size {size_mb:.2f}MB exceeds maximum {max_size_mb}MB"
    
    # Try to load image
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.verify()
        return True, None
    except Exception as e:
        return False, f"Invalid image format: {e}"


def get_image_info(img_bytes: bytes) -> dict:
    """
    Get image metadata.
    
    Args:
        img_bytes: Raw image bytes
        
    Returns:
        Dictionary with width, height, format, mode
    """
    try:
        img = Image.open(io.BytesIO(img_bytes))
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(img_bytes),
            "size_mb": round(len(img_bytes) / (1024 * 1024), 2),
        }
    except Exception as e:
        return {"error": str(e)}
