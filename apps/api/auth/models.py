"""
Authentication models for user representation and JWT payloads.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class CurrentUser(BaseModel):
    """Represents the currently authenticated user from JWT"""
    id: str  # UUID from Supabase
    email: EmailStr
    role: str = "user"  # 'user' or 'admin'
    
    class Config:
        frozen = True  # Immutable
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == "admin"
    
    def can_access_image(self, image_owner_id: Optional[str], image_visibility: str) -> bool:
        """
        Check if user can access an image based on ownership and visibility.
        
        Args:
            image_owner_id: UUID of image owner (None for system images)
            image_visibility: 'private', 'public', or 'public_admin'
        
        Returns:
            True if user can access the image
        """
        # Public images are accessible to all authenticated users
        if image_visibility in ('public', 'public_admin'):
            return True
        
        # Private images only accessible to owner or admin
        if image_visibility == 'private':
            return self.id == image_owner_id or self.is_admin()
        
        return False
    
    def can_modify_image(self, image_owner_id: Optional[str]) -> bool:
        """
        Check if user can modify an image (update visibility, delete, etc.)
        
        Args:
            image_owner_id: UUID of image owner
        
        Returns:
            True if user can modify the image
        """
        return self.id == image_owner_id or self.is_admin()


class TokenPayload(BaseModel):
    """JWT token payload structure from Supabase"""
    sub: str  # Subject (user ID)
    email: Optional[str] = None
    role: Optional[str] = "user"
    aud: str = "authenticated"
    exp: Optional[int] = None  # Expiration timestamp
    iat: Optional[int] = None  # Issued at timestamp
