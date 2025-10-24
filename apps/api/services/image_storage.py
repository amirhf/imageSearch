"""
Abstract interface for image storage backends.
Supports local filesystem, S3, or other storage providers.
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ImageMetadata:
    """Metadata about stored image"""
    image_id: str
    file_path: str
    format: str  # jpeg, png, webp
    size_bytes: int
    width: int
    height: int
    thumbnail_path: Optional[str] = None


class ImageStorage(ABC):
    """Abstract base class for image storage backends"""
    
    @abstractmethod
    async def save_image(
        self, 
        image_id: str, 
        image_bytes: bytes,
        generate_thumbnail: bool = True
    ) -> ImageMetadata:
        """
        Save image and optionally generate thumbnail.
        
        Args:
            image_id: Unique identifier for the image
            image_bytes: Raw image bytes
            generate_thumbnail: Whether to generate thumbnail
            
        Returns:
            ImageMetadata with file paths and dimensions
        """
        pass
    
    @abstractmethod
    async def get_image(self, image_id: str) -> Optional[bytes]:
        """
        Retrieve original image bytes.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            Image bytes or None if not found
        """
        pass
    
    @abstractmethod
    async def get_thumbnail(self, image_id: str) -> Optional[bytes]:
        """
        Retrieve thumbnail image bytes.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            Thumbnail bytes or None if not found
        """
        pass
    
    @abstractmethod
    async def delete_image(self, image_id: str) -> bool:
        """
        Delete image and its thumbnail.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def get_image_url(self, image_id: str) -> str:
        """
        Get public URL for image download.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            URL string
        """
        pass
    
    @abstractmethod
    def get_thumbnail_url(self, image_id: str) -> str:
        """
        Get public URL for thumbnail download.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            URL string
        """
        pass
