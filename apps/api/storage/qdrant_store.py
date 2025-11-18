import os
from typing import Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

COLL = "images"

class QdrantStore:
    def __init__(self):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=url)
        try:
            self.client.get_collection(COLL)
        except Exception:
            self.client.recreate_collection(
                collection_name=COLL,
                vectors_config=qm.VectorParams(size=512, distance=qm.Distance.COSINE),  # Match OpenCLIP ViT-B-32
            )

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
        """Upsert image with multi-tenant metadata"""
        # Build complete payload with multi-tenant fields
        full_payload = {
            "caption": caption,
            "confidence": caption_confidence,
            "origin": caption_origin,
            **payload,
        }
        
        # Add storage fields if provided
        if file_path is not None:
            full_payload["file_path"] = file_path
        if format is not None:
            full_payload["format"] = format
        if size_bytes is not None:
            full_payload["size_bytes"] = size_bytes
        if width is not None:
            full_payload["width"] = width
        if height is not None:
            full_payload["height"] = height
        if thumbnail_path is not None:
            full_payload["thumbnail_path"] = thumbnail_path
        
        # Add multi-tenant fields
        if owner_user_id is not None:
            full_payload["owner_user_id"] = owner_user_id
        full_payload["visibility"] = visibility
        full_payload["deleted_at"] = None
        full_payload["created_at"] = datetime.utcnow().isoformat()
        full_payload["updated_at"] = datetime.utcnow().isoformat()
        
        self.client.upsert(
            COLL,
            points=[qm.PointStruct(id=image_id, vector=img_vec, payload=full_payload)]
        )

    async def fetch_image(self, image_id: str):
        """Fetch image by ID"""
        r = self.client.retrieve(COLL, ids=[image_id])
        return None if not r else {"id": image_id, **(r[0].payload or {})}

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
            text_query: Optional text query (not used in Qdrant, kept for API compatibility)
            user_id: Current user ID (None for anonymous)
            scope: 'all', 'mine', or 'public'
        """
        # Build filter for multi-tenant access control
        must_conditions = [
            # Exclude deleted images (deleted_at must be null)
            qm.IsNullCondition(is_null=qm.PayloadField(key="deleted_at"))
        ]
        
        # Apply scope-based filtering
        if user_id is None:
            # Anonymous: only public images
            must_conditions.append(
                qm.FieldCondition(
                    key="visibility",
                    match=qm.MatchAny(any=["public", "public_admin"])
                )
            )
        elif scope == "mine":
            # Only user's own images
            must_conditions.append(
                qm.FieldCondition(
                    key="owner_user_id",
                    match=qm.MatchValue(value=user_id)
                )
            )
        elif scope == "public":
            # Only public images
            must_conditions.append(
                qm.FieldCondition(
                    key="visibility",
                    match=qm.MatchAny(any=["public", "public_admin"])
                )
            )
        else:  # scope == "all"
            # User's images OR public images
            # Use should clause for OR logic
            filter_obj = qm.Filter(
                must=must_conditions,
                should=[
                    qm.FieldCondition(
                        key="owner_user_id",
                        match=qm.MatchValue(value=user_id)
                    ),
                    qm.FieldCondition(
                        key="visibility",
                        match=qm.MatchAny(any=["public", "public_admin"])
                    )
                ]
            )
            
            res = self.client.search(
                COLL,
                query_vector=query_vec,
                limit=k,
                query_filter=filter_obj
            )
            return [{"id": p.id, "score": float(p.score), **(p.payload or {})} for p in res]
        
        # For other scopes, use simple must conditions
        filter_obj = qm.Filter(must=must_conditions)
        
        res = self.client.search(
            COLL,
            query_vector=query_vec,
            limit=k,
            query_filter=filter_obj
        )
        return [{"id": p.id, "score": float(p.score), **(p.payload or {})} for p in res]
    
    async def update_visibility(self, image_id: str, visibility: str):
        """Update image visibility"""
        # Fetch current point
        points = self.client.retrieve(COLL, ids=[image_id])
        if not points:
            return
        
        # Update payload
        payload = points[0].payload or {}
        payload["visibility"] = visibility
        payload["updated_at"] = datetime.utcnow().isoformat()
        
        # Upsert with updated payload (keep same vector)
        self.client.set_payload(
            collection_name=COLL,
            payload=payload,
            points=[image_id]
        )
    
    async def soft_delete_image(self, image_id: str):
        """Soft delete an image by setting deleted_at timestamp"""
        # Fetch current point
        points = self.client.retrieve(COLL, ids=[image_id])
        if not points:
            return
        
        # Update payload with deleted_at
        payload = points[0].payload or {}
        payload["deleted_at"] = datetime.utcnow().isoformat()
        
        # Update payload
        self.client.set_payload(
            collection_name=COLL,
            payload=payload,
            points=[image_id]
        )
    
    async def list_images(
        self,
        user_id: Optional[str] = None,
        is_admin: bool = False,
        limit: int = 20,
        offset: int = 0,
        visibility_filter: Optional[str] = None
    ):
        """List images with multi-tenant filtering.
        
        Note: Qdrant doesn't have native pagination like SQL OFFSET.
        This implementation uses scroll with limit.
        """
        # Build filter conditions
        must_conditions = [
            # Exclude deleted images
            qm.IsNullCondition(is_null=qm.PayloadField(key="deleted_at"))
        ]
        
        # Apply visibility filtering based on user role
        if is_admin:
            # Admins see everything (no additional filter)
            pass
        elif user_id:
            # Authenticated users see their own + public
            # This requires a should clause (OR logic)
            filter_obj = qm.Filter(
                must=must_conditions,
                should=[
                    qm.FieldCondition(
                        key="owner_user_id",
                        match=qm.MatchValue(value=user_id)
                    ),
                    qm.FieldCondition(
                        key="visibility",
                        match=qm.MatchAny(any=["public", "public_admin"])
                    )
                ]
            )
        else:
            # Anonymous users see only public
            must_conditions.append(
                qm.FieldCondition(
                    key="visibility",
                    match=qm.MatchAny(any=["public", "public_admin"])
                )
            )
            filter_obj = qm.Filter(must=must_conditions)
        
        # Add optional visibility filter
        if visibility_filter:
            if 'filter_obj' not in locals():
                filter_obj = qm.Filter(must=must_conditions)
            filter_obj.must.append(
                qm.FieldCondition(
                    key="visibility",
                    match=qm.MatchValue(value=visibility_filter)
                )
            )
        
        # Use scroll to get points
        # Note: Qdrant scroll doesn't support offset directly
        # We fetch limit + offset and slice in memory (not ideal for large offsets)
        scroll_limit = limit + offset if offset > 0 else limit
        
        if 'filter_obj' not in locals():
            filter_obj = qm.Filter(must=must_conditions)
        
        points, _ = self.client.scroll(
            collection_name=COLL,
            scroll_filter=filter_obj,
            limit=scroll_limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Apply offset by slicing
        points = points[offset:offset + limit]
        
        # Convert to dict format
        return [
            {
                "id": p.id,
                **(p.payload or {})
            }
            for p in points
        ]
