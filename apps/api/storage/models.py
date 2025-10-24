from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, Float, JSON, Text
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class ImageDoc(Base):
    __tablename__ = "images"
    id = mapped_column(String(64), primary_key=True)
    caption = mapped_column(Text)
    caption_confidence = mapped_column(Float)
    caption_origin = mapped_column(String(16))
    embed_vector = mapped_column(Vector(512))  # OpenCLIP ViT-B-32 produces 512-dim vectors
    payload = mapped_column(JSON)
    
    # Image storage fields
    file_path = mapped_column(String(512), nullable=True)  # Path to stored image file
    format = mapped_column(String(16), nullable=True)  # jpeg, png, webp
    size_bytes = mapped_column(Integer, nullable=True)  # File size in bytes
    width = mapped_column(Integer, nullable=True)  # Image width in pixels
    height = mapped_column(Integer, nullable=True)  # Image height in pixels
    thumbnail_path = mapped_column(String(512), nullable=True)  # Path to thumbnail
