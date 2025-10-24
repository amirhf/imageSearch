"""
Local filesystem implementation of ImageStorage.
Stores images in a sharded directory structure for better performance.
"""
import os
import io
from pathlib import Path
from typing import Optional
from PIL import Image
import asyncio

from apps.api.services.image_storage import ImageStorage, ImageMetadata


class LocalFileStorage(ImageStorage):
    """Local filesystem storage with 2-level sharding"""
    
    def __init__(
        self, 
        base_path: str = "./storage/images",
        thumbnail_size: int = 256,
        base_url: str = "http://localhost:8000"
    ):
        self.base_path = Path(base_path)
        self.thumbnail_size = thumbnail_size
        self.base_url = base_url.rstrip('/')
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.thumbnail_path = self.base_path / "thumbnails"
        self.thumbnail_path.mkdir(parents=True, exist_ok=True)
    
    def _get_shard_path(self, image_id: str, is_thumbnail: bool = False) -> Path:
        """Get sharded path for image (first 2 chars as directory)"""
        shard = image_id[:2]
        base = self.thumbnail_path if is_thumbnail else self.base_path
        shard_dir = base / shard
        shard_dir.mkdir(parents=True, exist_ok=True)
        return shard_dir
    
    async def save_image(
        self, 
        image_id: str, 
        image_bytes: bytes,
        generate_thumbnail: bool = True
    ) -> ImageMetadata:
        """Save image and generate thumbnail"""
        # Detect format and dimensions
        img = Image.open(io.BytesIO(image_bytes))
        format_str = img.format.lower() if img.format else 'jpeg'
        width, height = img.size
        size_bytes = len(image_bytes)
        
        # Save original image
        shard_dir = self._get_shard_path(image_id)
        file_name = f"{image_id}.{format_str}"
        file_path = shard_dir / file_name
        
        # Use executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_bytes, image_bytes)
        
        # Generate thumbnail
        thumbnail_path = None
        if generate_thumbnail:
            thumbnail_path = await self._generate_thumbnail(image_id, img, format_str)
        
        return ImageMetadata(
            image_id=image_id,
            file_path=str(file_path),
            format=format_str,
            size_bytes=size_bytes,
            width=width,
            height=height,
            thumbnail_path=thumbnail_path
        )
    
    async def _generate_thumbnail(
        self, 
        image_id: str, 
        img: Image.Image, 
        format_str: str
    ) -> str:
        """Generate and save thumbnail"""
        # Create thumbnail
        thumb = img.copy()
        thumb.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
        
        # Save thumbnail
        thumb_shard_dir = self._get_shard_path(image_id, is_thumbnail=True)
        thumb_name = f"{image_id}.{format_str}"
        thumb_path = thumb_shard_dir / thumb_name
        
        # Use executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def save_thumbnail():
            thumb_buffer = io.BytesIO()
            thumb.save(thumb_buffer, format=format_str.upper())
            thumb_path.write_bytes(thumb_buffer.getvalue())
        
        await loop.run_in_executor(None, save_thumbnail)
        
        return str(thumb_path)
    
    async def get_image(self, image_id: str) -> Optional[bytes]:
        """Retrieve original image bytes"""
        # Try common formats
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            shard_dir = self._get_shard_path(image_id)
            file_path = shard_dir / f"{image_id}.{fmt}"
            if file_path.exists():
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, file_path.read_bytes)
        return None
    
    async def get_thumbnail(self, image_id: str) -> Optional[bytes]:
        """Retrieve thumbnail bytes"""
        # Try common formats
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            shard_dir = self._get_shard_path(image_id, is_thumbnail=True)
            thumb_path = shard_dir / f"{image_id}.{fmt}"
            if thumb_path.exists():
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, thumb_path.read_bytes)
        return None
    
    async def delete_image(self, image_id: str) -> bool:
        """Delete image and thumbnail"""
        deleted = False
        
        # Delete original
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            shard_dir = self._get_shard_path(image_id)
            file_path = shard_dir / f"{image_id}.{fmt}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
        
        # Delete thumbnail
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            shard_dir = self._get_shard_path(image_id, is_thumbnail=True)
            thumb_path = shard_dir / f"{image_id}.{fmt}"
            if thumb_path.exists():
                thumb_path.unlink()
        
        return deleted
    
    def get_image_url(self, image_id: str) -> str:
        """Get public URL for image download"""
        return f"{self.base_url}/images/{image_id}/download"
    
    def get_thumbnail_url(self, image_id: str) -> str:
        """Get public URL for thumbnail download"""
        return f"{self.base_url}/images/{image_id}/thumbnail"
