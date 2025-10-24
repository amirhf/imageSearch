import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from apps.api.storage.models import Base, ImageDoc
import numpy as np

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
_engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=_engine)

# Initialize schema
with _engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=conn)
    conn.execute(text("CREATE INDEX IF NOT EXISTS images_vec_hnsw ON images USING hnsw (embed_vector vector_cosine_ops)"))

class PgVectorStore:
    async def upsert_image(
        self, 
        image_id: str, 
        caption: str, 
        caption_confidence: float, 
        caption_origin: str, 
        img_vec, 
        payload: dict,
        file_path: str = None,
        format: str = None,
        size_bytes: int = None,
        width: int = None,
        height: int = None,
        thumbnail_path: str = None
    ):
        with Session() as s:
            doc = s.get(ImageDoc, image_id) or ImageDoc(id=image_id)
            doc.caption = caption
            doc.caption_confidence = caption_confidence
            doc.caption_origin = caption_origin
            doc.embed_vector = img_vec
            doc.payload = payload
            
            # Update storage fields if provided
            if file_path is not None:
                doc.file_path = file_path
            if format is not None:
                doc.format = format
            if size_bytes is not None:
                doc.size_bytes = size_bytes
            if width is not None:
                doc.width = width
            if height is not None:
                doc.height = height
            if thumbnail_path is not None:
                doc.thumbnail_path = thumbnail_path
            
            s.add(doc)
            s.commit()

    async def fetch_image(self, image_id: str):
        with Session() as s:
            doc = s.get(ImageDoc, image_id)
            return None if not doc else {
                "id": doc.id,
                "caption": doc.caption,
                "confidence": doc.caption_confidence,
                "origin": doc.caption_origin,
                "payload": doc.payload,
                "file_path": doc.file_path,
                "format": doc.format,
                "size_bytes": doc.size_bytes,
                "width": doc.width,
                "height": doc.height,
                "thumbnail_path": doc.thumbnail_path,
            }

    async def search(self, query_vec, k: int = 10):
        # Convert numpy array to list if needed
        if hasattr(query_vec, 'tolist'):
            query_vec = query_vec.tolist()
        elif isinstance(query_vec, np.ndarray):
            query_vec = query_vec.tolist()
        
        # Simple approach: use ORM with SQLAlchemy
        with Session() as s:
            # Build vector string for pgvector
            vec_str = str(query_vec)
            
            # Use text SQL with proper vector casting
            q = text("""
                SELECT id, caption, caption_confidence, caption_origin,
                       1 - (embed_vector <=> CAST(:qvec AS vector)) AS score
                FROM images
                ORDER BY embed_vector <=> CAST(:qvec AS vector)
                LIMIT :k
            """)
            rows = s.execute(q, {"qvec": vec_str, "k": k}).fetchall()
            return [
                {"id": r.id, "caption": r.caption, "score": float(r.score)}
                for r in rows
            ]
