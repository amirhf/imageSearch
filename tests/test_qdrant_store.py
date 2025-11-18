"""
Tests for QdrantStore multi-tenant functionality (Phase 4).
"""
import pytest
import numpy as np
import uuid
from apps.api.storage.qdrant_store import QdrantStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
import os
from datetime import datetime

# Test collection name
TEST_COLLECTION = "test_images"


def generate_uuid():
    """Generate a UUID string for test image IDs"""
    return str(uuid.uuid4())


@pytest.fixture
def qdrant_store():
    """Create a test Qdrant store with a test collection"""
    # Override collection name for testing
    original_coll = os.environ.get("QDRANT_COLLECTION")
    
    # Create store
    store = QdrantStore()
    
    # Recreate collection for clean tests
    try:
        store.client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    
    store.client.recreate_collection(
        collection_name=TEST_COLLECTION,
        vectors_config=qm.VectorParams(size=512, distance=qm.Distance.COSINE)
    )
    
    # Override collection name in store
    import apps.api.storage.qdrant_store as qs
    original_coll_name = qs.COLL
    qs.COLL = TEST_COLLECTION
    
    yield store
    
    # Cleanup
    try:
        store.client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    
    # Restore original collection name
    qs.COLL = original_coll_name
    if original_coll:
        os.environ["QDRANT_COLLECTION"] = original_coll


def create_test_vector():
    """Create a random test vector"""
    return np.random.rand(512).tolist()


class TestQdrantUpsert:
    """Test upsert_image with multi-tenant fields"""
    
    @pytest.mark.asyncio
    async def test_upsert_with_owner_and_visibility(self, qdrant_store):
        """Test upserting image with owner and visibility"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Test image",
            caption_confidence=0.95,
            caption_origin="local",
            img_vec=vector,
            payload={},
            owner_user_id="user-123",
            visibility="private"
        )
        
        # Fetch and verify
        result = await qdrant_store.fetch_image(image_id)
        assert result is not None
        assert result["caption"] == "Test image"
        assert result["owner_user_id"] == "user-123"
        assert result["visibility"] == "private"
        assert result["deleted_at"] is None
        assert "created_at" in result
        assert "updated_at" in result
    
    @pytest.mark.asyncio
    async def test_upsert_public_image(self, qdrant_store):
        """Test upserting public image"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Public image",
            caption_confidence=0.90,
            caption_origin="cloud",
            img_vec=vector,
            payload={},
            owner_user_id="user-456",
            visibility="public"
        )
        
        result = await qdrant_store.fetch_image(image_id)
        assert result["visibility"] == "public"
        assert result["owner_user_id"] == "user-456"
    
    @pytest.mark.asyncio
    async def test_upsert_with_storage_fields(self, qdrant_store):
        """Test upserting with storage metadata"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Image with metadata",
            caption_confidence=0.88,
            caption_origin="local",
            img_vec=vector,
            payload={},
            file_path="/path/to/image.jpg",
            format="jpeg",
            size_bytes=123456,
            width=1920,
            height=1080,
            thumbnail_path="/path/to/thumb.jpg",
            owner_user_id="user-789",
            visibility="private"
        )
        
        result = await qdrant_store.fetch_image(image_id)
        assert result["file_path"] == "/path/to/image.jpg"
        assert result["format"] == "jpeg"
        assert result["size_bytes"] == 123456
        assert result["width"] == 1920
        assert result["height"] == 1080


class TestQdrantSearch:
    """Test search with multi-tenant filtering"""
    
    @pytest.fixture
    async def populated_store(self, qdrant_store):
        """Create a store with test data"""
        # User 1's private images
        for i in range(3):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"User 1 private image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="user-1",
                visibility="private"
            )
        
        # User 1's public images
        for i in range(2):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"User 1 public image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="user-1",
                visibility="public"
            )
        
        # User 2's private images
        for i in range(2):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"User 2 private image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="user-2",
                visibility="private"
            )
        
        # Public admin images
        for i in range(2):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"Admin public image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="admin-user",
                visibility="public_admin"
            )
        
        # Deleted image
        deleted_id = generate_uuid()
        await qdrant_store.upsert_image(
            image_id=deleted_id,
            caption="Deleted image",
            caption_confidence=0.9,
            caption_origin="local",
            img_vec=create_test_vector(),
            payload={},
            owner_user_id="user-1",
            visibility="public"
        )
        await qdrant_store.soft_delete_image(deleted_id)
        
        # Store deleted_id for later verification
        qdrant_store._test_deleted_id = deleted_id
        return qdrant_store
    
    @pytest.mark.asyncio
    async def test_anonymous_search_public_only(self, populated_store):
        """Test anonymous users only see public images"""
        query_vec = create_test_vector()
        results = await populated_store.search(
            query_vec=query_vec,
            k=20,
            user_id=None,
            scope="public"
        )
        
        # Should get 2 user1-public + 2 admin-public = 4 images
        # (deleted image should be excluded)
        assert len(results) == 4
        
        # Verify no private images
        for result in results:
            assert result["visibility"] in ["public", "public_admin"]
    
    @pytest.mark.asyncio
    async def test_user_search_mine_scope(self, populated_store):
        """Test user searching only their images"""
        query_vec = create_test_vector()
        results = await populated_store.search(
            query_vec=query_vec,
            k=20,
            user_id="user-1",
            scope="mine"
        )
        
        # Should get 3 private + 2 public = 5 images from user-1
        # (deleted image should be excluded)
        assert len(results) == 5
        
        # Verify all belong to user-1
        for result in results:
            assert result["owner_user_id"] == "user-1"
    
    @pytest.mark.asyncio
    async def test_user_search_all_scope(self, populated_store):
        """Test user searching all accessible images"""
        query_vec = create_test_vector()
        results = await populated_store.search(
            query_vec=query_vec,
            k=20,
            user_id="user-1",
            scope="all"
        )
        
        # Should get:
        # - User 1's images: 3 private + 2 public = 5
        # - Other public: 2 admin-public = 2
        # Total: 7 images (deleted excluded)
        assert len(results) == 7
        
        # Verify access rules
        for result in results:
            is_own = result["owner_user_id"] == "user-1"
            is_public = result["visibility"] in ["public", "public_admin"]
            assert is_own or is_public
    
    @pytest.mark.asyncio
    async def test_search_excludes_deleted(self, populated_store):
        """Test that deleted images are excluded from search"""
        query_vec = create_test_vector()
        
        # Search as owner
        results = await populated_store.search(
            query_vec=query_vec,
            k=20,
            user_id="user-1",
            scope="mine"
        )
        
        # Verify deleted image not in results
        image_ids = [r["id"] for r in results]
        assert populated_store._test_deleted_id not in image_ids


class TestQdrantUpdate:
    """Test update operations"""
    
    @pytest.mark.asyncio
    async def test_update_visibility(self, qdrant_store):
        """Test updating image visibility"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        # Create private image
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Test image",
            caption_confidence=0.9,
            caption_origin="local",
            img_vec=vector,
            payload={},
            owner_user_id="user-123",
            visibility="private"
        )
        
        # Update to public
        await qdrant_store.update_visibility(image_id, "public")
        
        # Verify
        result = await qdrant_store.fetch_image(image_id)
        assert result["visibility"] == "public"
        assert "updated_at" in result
    
    @pytest.mark.asyncio
    async def test_soft_delete(self, qdrant_store):
        """Test soft deleting an image"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        # Create image
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Test image",
            caption_confidence=0.9,
            caption_origin="local",
            img_vec=vector,
            payload={},
            owner_user_id="user-123",
            visibility="public"
        )
        
        # Soft delete
        await qdrant_store.soft_delete_image(image_id)
        
        # Verify deleted_at is set
        result = await qdrant_store.fetch_image(image_id)
        assert result["deleted_at"] is not None
        
        # Verify excluded from search
        query_vec = create_test_vector()
        results = await qdrant_store.search(
            query_vec=query_vec,
            k=10,
            user_id=None,
            scope="public"
        )
        image_ids = [r["id"] for r in results]
        assert image_id not in image_ids


class TestQdrantList:
    """Test list_images functionality"""
    
    @pytest.fixture
    async def list_test_store(self, qdrant_store):
        """Create store with test data for listing"""
        # Create 5 public images
        for i in range(5):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"Public image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="user-1",
                visibility="public"
            )
        
        # Create 3 private images
        for i in range(3):
            await qdrant_store.upsert_image(
                image_id=generate_uuid(),
                caption=f"Private image {i}",
                caption_confidence=0.9,
                caption_origin="local",
                img_vec=create_test_vector(),
                payload={},
                owner_user_id="user-1",
                visibility="private"
            )
        
        return qdrant_store
    
    @pytest.mark.asyncio
    async def test_list_anonymous(self, list_test_store):
        """Test anonymous listing shows only public"""
        images = await list_test_store.list_images(
            user_id=None,
            is_admin=False,
            limit=20
        )
        
        # Should only see 5 public images
        assert len(images) == 5
        for img in images:
            assert img["visibility"] in ["public", "public_admin"]
    
    @pytest.mark.asyncio
    async def test_list_authenticated(self, list_test_store):
        """Test authenticated user sees own + public"""
        images = await list_test_store.list_images(
            user_id="user-1",
            is_admin=False,
            limit=20
        )
        
        # Should see 5 public + 3 private = 8 images
        assert len(images) == 8
    
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, list_test_store):
        """Test pagination in list"""
        # Get first 3
        images_page1 = await list_test_store.list_images(
            user_id="user-1",
            is_admin=False,
            limit=3,
            offset=0
        )
        assert len(images_page1) == 3
        
        # Get next 3
        images_page2 = await list_test_store.list_images(
            user_id="user-1",
            is_admin=False,
            limit=3,
            offset=3
        )
        assert len(images_page2) == 3
        
        # Verify different images
        ids_page1 = {img["id"] for img in images_page1}
        ids_page2 = {img["id"] for img in images_page2}
        assert len(ids_page1.intersection(ids_page2)) == 0
    
    @pytest.mark.asyncio
    async def test_list_with_visibility_filter(self, list_test_store):
        """Test filtering by visibility"""
        images = await list_test_store.list_images(
            user_id="user-1",
            is_admin=False,
            limit=20,
            visibility_filter="public"
        )
        
        # Should only see public images
        assert len(images) == 5
        for img in images:
            assert img["visibility"] == "public"


class TestQdrantFilters:
    """Test Qdrant filter construction"""
    
    @pytest.mark.asyncio
    async def test_filter_excludes_deleted(self, qdrant_store):
        """Verify deleted_at filter is always applied"""
        image_id = generate_uuid()
        vector = create_test_vector()
        
        # Create and delete image
        await qdrant_store.upsert_image(
            image_id=image_id,
            caption="Test",
            caption_confidence=0.9,
            caption_origin="local",
            img_vec=vector,
            payload={},
            owner_user_id="user-1",
            visibility="public"
        )
        await qdrant_store.soft_delete_image(image_id)
        
        # Search should not find it
        results = await qdrant_store.search(
            query_vec=vector,
            k=10,
            user_id=None,
            scope="public"
        )
        
        ids = [r["id"] for r in results]
        assert image_id not in ids


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
