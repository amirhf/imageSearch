import os
from sqlalchemy import create_engine, text, or_, and_
from sqlalchemy.orm import sessionmaker
from apps.api.storage.models import Base, ImageDoc
from datetime import datetime
from typing import Optional
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
        thumbnail_path: str = None,
        owner_user_id: str = None,
        visibility: str = "private"
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
            
            # Multi-tenant fields
            if owner_user_id is not None:
                doc.owner_user_id = owner_user_id
            if visibility is not None:
                doc.visibility = visibility
            
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
                "owner_user_id": str(doc.owner_user_id) if doc.owner_user_id else None,
                "visibility": doc.visibility,
                "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            }

    async def search(
        self,
        query_vec,
        k: int = 10,
        text_query: str = None,
        user_id: Optional[str] = None,
        scope: str = "all"
    ):
        """Search with multi-tenant filtering.
        
        Args:
            query_vec: Query embedding vector
            k: Number of results
            text_query: Optional text for hybrid search
            user_id: Current user ID (None for anonymous)
            scope: 'all', 'mine', or 'public'
        """
        # Convert numpy array to list if needed
        if hasattr(query_vec, 'tolist'):
            query_vec = query_vec.tolist()
        elif isinstance(query_vec, np.ndarray):
            query_vec = query_vec.tolist()
        
        _init_db()
        with Session() as s:
            vec_str = str(query_vec)
            
            # Build WHERE clause for multi-tenant filtering
            where_clauses = ["deleted_at IS NULL"]
            params = {"qvec": vec_str, "k": k}
            
            if user_id is None:
                # Anonymous: only public images
                where_clauses.append("visibility IN ('public', 'public_admin')")
            elif scope == "mine":
                # Only user's own images
                where_clauses.append("CAST(owner_user_id AS TEXT) = :user_id")
                params["user_id"] = str(user_id)
            elif scope == "public":
                # Only public images
                where_clauses.append("visibility IN ('public', 'public_admin')")
            else:  # scope == "all"
                # User's images + public images
                where_clauses.append("(CAST(owner_user_id AS TEXT) = :user_id OR visibility IN ('public', 'public_admin'))")
                params["user_id"] = str(user_id)
            
            where_clause = " AND ".join(where_clauses)
            
            # Optional hybrid boosting
            hybrid = os.getenv("HYBRID_TEXT_BOOST", "true").lower() == "true" and bool(text_query)
            try:
                boost_w = float(os.getenv("HYBRID_TEXT_WEIGHT", "0.2"))
            except Exception:
                boost_w = 0.2

            if hybrid:
                q = text(f"""
                    SELECT id, caption, caption_confidence, caption_origin,
                           (1 - (embed_vector <=> CAST(:qvec AS vector))) AS vec_score,
                           CASE WHEN lower(caption) LIKE '%' || :qterm || '%' THEN :boost ELSE 0 END AS text_boost,
                           ((1 - (embed_vector <=> CAST(:qvec AS vector))) +
                            CASE WHEN lower(caption) LIKE '%' || :qterm || '%' THEN :boost ELSE 0 END) AS score
                    FROM images
                    WHERE {where_clause}
                    ORDER BY score DESC
                    LIMIT :k
                """)
                params.update({"qterm": str(text_query).strip().lower(), "boost": boost_w})
                rows = s.execute(q, params).fetchall()
                return [
                    {"id": r.id, "caption": r.caption, "score": float(r.score)}
                    for r in rows
                ]
            else:
                # Pure vector search
                q = text(f"""
                    SELECT id, caption, caption_confidence, caption_origin,
                           1 - (embed_vector <=> CAST(:qvec AS vector)) AS score
                    FROM images
                    WHERE {where_clause}
                    ORDER BY embed_vector <=> CAST(:qvec AS vector)
                    LIMIT :k
                """)
                rows = s.execute(q, params).fetchall()
                return [
                    {"id": r.id, "caption": r.caption, "score": float(r.score)}
                    for r in rows
                ]
    
    async def update_visibility(self, image_id: str, visibility: str):
        """Update image visibility"""
        _init_db()
        with Session() as s:
            doc = s.get(ImageDoc, image_id)
            if doc:
                doc.visibility = visibility
                doc.updated_at = datetime.utcnow()
                s.commit()
    
    async def soft_delete_image(self, image_id: str):
        """Soft delete an image"""
        _init_db()
        with Session() as s:
            doc = s.get(ImageDoc, image_id)
            if doc:
                doc.deleted_at = datetime.utcnow()
                s.commit()
    
    async def list_images(
        self,
        user_id: Optional[str] = None,
        is_admin: bool = False,
        limit: int = 20,
        offset: int = 0,
        visibility_filter: Optional[str] = None
    ):
        """List images with multi-tenant filtering"""
        _init_db()
        with Session() as s:
            query = s.query(ImageDoc).filter(ImageDoc.deleted_at == None)
            
            # Apply visibility filtering
            if is_admin:
                # Admins see everything
                pass
            elif user_id:
                # Authenticated users see their own + public
                # Cast UUID to string for comparison
                from sqlalchemy import cast, String
                query = query.filter(
                    or_(
                        cast(ImageDoc.owner_user_id, String) == str(user_id),
                        ImageDoc.visibility.in_(["public", "public_admin"])
                    )
                )
            else:
                # Anonymous users see only public
                query = query.filter(ImageDoc.visibility.in_(["public", "public_admin"]))
            
            # Optional visibility filter
            if visibility_filter:
                query = query.filter(ImageDoc.visibility == visibility_filter)
            
            # Order by most recent first
            query = query.order_by(ImageDoc.created_at.desc())
            
            # Pagination
            query = query.limit(limit).offset(offset)
            
            docs = query.all()
            return [
                {
                    "id": doc.id,
                    "caption": doc.caption,
                    "confidence": doc.caption_confidence,
                    "origin": doc.caption_origin,
                    "format": doc.format,
                    "size_bytes": doc.size_bytes,
                    "width": doc.width,
                    "height": doc.height,
                    "owner_user_id": str(doc.owner_user_id) if doc.owner_user_id else None,
                    "visibility": doc.visibility,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                }
                for doc in docs
            ]
