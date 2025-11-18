from sqlalchemy.orm import declarative_base, mapped_column, relationship
from sqlalchemy import Integer, String, Float, JSON, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()


class Profile(Base):
    """User profile table (extends Supabase auth.users)"""
    __tablename__ = "profiles"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name = mapped_column(String(255), nullable=True)
    avatar_url = mapped_column(Text, nullable=True)
    role = mapped_column(String(16), default='user')  # 'user' or 'admin'
    created_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to images
    images = relationship("ImageDoc", back_populates="owner", foreign_keys="ImageDoc.owner_user_id")
    
    def __repr__(self):
        return f"<Profile(id={self.id}, email={self.email}, role={self.role})>"


class ImageDoc(Base):
    """Image document with embeddings and metadata"""
    __tablename__ = "images"
    
    # Primary fields
    id = mapped_column(String(64), primary_key=True)
    caption = mapped_column(Text, nullable=False)
    caption_confidence = mapped_column(Float, nullable=False)
    caption_origin = mapped_column(String(16), nullable=False)  # 'local' or 'cloud'
    embed_vector = mapped_column(Vector(512), nullable=False)  # OpenCLIP ViT-B-32 produces 512-dim vectors
    payload = mapped_column(JSON, nullable=True)
    
    # Image storage fields
    file_path = mapped_column(String(512), nullable=True)  # Path to stored image file
    format = mapped_column(String(16), nullable=True)  # jpeg, png, webp
    size_bytes = mapped_column(Integer, nullable=True)  # File size in bytes
    width = mapped_column(Integer, nullable=True)  # Image width in pixels
    height = mapped_column(Integer, nullable=True)  # Image height in pixels
    thumbnail_path = mapped_column(String(512), nullable=True)  # Path to thumbnail
    
    # Multi-tenant fields
    owner_user_id = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('profiles.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    visibility = mapped_column(
        String(16), 
        default='private', 
        nullable=False,
        index=True
    )  # 'private', 'public', 'public_admin'
    deleted_at = mapped_column(DateTime, nullable=True, index=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to owner
    owner = relationship("Profile", back_populates="images", foreign_keys=[owner_user_id])
    
    def __repr__(self):
        return f"<ImageDoc(id={self.id}, visibility={self.visibility}, owner={self.owner_user_id})>"
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    @property
    def is_public(self):
        return self.visibility in ('public', 'public_admin')
