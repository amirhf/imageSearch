import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from apps.api.storage.models import Base, ImageDoc
import numpy as np

# Lazily initialized globals to avoid failing at import time if DB is unreachable
_engine = None
Session = None
_initialized = False


def _init_db():
    """Initialize engine, session, and schema on first use."""
    global _engine, Session, _initialized
    if _initialized:
        return

    # Read DATABASE_URL at runtime (Cloud Run env)
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router",
    )

    # Create engine with pre_ping for resilient connections
    _engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=_engine)

    # Initialize schema and index; tolerate extension/index creation errors gracefully
    try:
        with _engine.begin() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as e:
                print(f"[WARN] Could not create pgvector extension: {e}")

            Base.metadata.create_all(bind=conn)

            try:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS images_vec_hnsw ON images USING hnsw (embed_vector vector_cosine_ops)"
                    )
                )
            except Exception as e:
                print(f"[WARN] Could not create HNSW index: {e}")
    except Exception as e:
        # Defer hard failure to actual DB operations so the app can start and expose /healthz
        print(f"[ERROR] Database initialization failed: {e}")

    _initialized = True

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
        _init_db()
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
        _init_db()
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

    async def search(self, query_vec, k: int = 10, text_query: str = None):
        # Convert numpy array to list if needed
        if hasattr(query_vec, 'tolist'):
            query_vec = query_vec.tolist()
        elif isinstance(query_vec, np.ndarray):
            query_vec = query_vec.tolist()
        
        # Simple approach: use ORM with SQLAlchemy
        _init_db()
        with Session() as s:
            # Build vector string for pgvector
            vec_str = str(query_vec)

            # Optional hybrid boosting using caption substring match
            hybrid = os.getenv("HYBRID_TEXT_BOOST", "true").lower() == "true" and bool(text_query)
            try:
                boost_w = float(os.getenv("HYBRID_TEXT_WEIGHT", "0.2"))
            except Exception:
                boost_w = 0.2

            if hybrid:
                q = text("""
                    SELECT id, caption, caption_confidence, caption_origin,
                           (1 - (embed_vector <=> CAST(:qvec AS vector))) AS vec_score,
                           CASE WHEN lower(caption) LIKE '%' || :qterm || '%' THEN :boost ELSE 0 END AS text_boost,
                           ((1 - (embed_vector <=> CAST(:qvec AS vector))) +
                            CASE WHEN lower(caption) LIKE '%' || :qterm || '%' THEN :boost ELSE 0 END) AS score
                    FROM images
                    ORDER BY score DESC
                    LIMIT :k
                """)
                params = {"qvec": vec_str, "qterm": str(text_query).strip().lower(), "boost": boost_w, "k": k}
                rows = s.execute(q, params).fetchall()
                return [
                    {"id": r.id, "caption": r.caption, "score": float(r.score)}
                    for r in rows
                ]
            else:
                # Pure vector search (cosine similarity)
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
