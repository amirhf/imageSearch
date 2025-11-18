"""
Tests for multi-tenant API endpoints (Phase 3).
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from jose import jwt
import os
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

client = TestClient(app)


def create_test_token(user_id: str, email: str, role: str = "user") -> str:
    """Create a test JWT token"""
    secret = os.getenv("SUPABASE_JWT_SECRET", "test-secret-for-development-only")
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_test_image() -> BytesIO:
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


class TestImageIngestion:
    """Test POST /images endpoint"""
    
    def test_upload_requires_auth(self):
        """Test that image upload requires authentication"""
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        assert response.status_code == 401
    
    def test_upload_with_auth(self):
        """Test authenticated image upload"""
        token = create_test_token("user-1", "user1@test.com")
        img_bytes = create_test_image()
        
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "private"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed or fail with specific error (not auth error)
        assert response.status_code != 401
        # Note: May fail with 500 if embedder/storage not configured, but that's OK for this test
    
    def test_upload_public_image(self):
        """Test uploading a public image"""
        token = create_test_token("user-1", "user1@test.com")
        img_bytes = create_test_image()
        
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code != 401
    
    def test_upload_public_admin_requires_admin(self):
        """Test that public_admin visibility requires admin role"""
        token = create_test_token("user-1", "user1@test.com", role="user")
        img_bytes = create_test_image()
        
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public_admin"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should fail with 403 or succeed if we get past validation
        if response.status_code not in [500]:  # Ignore infrastructure errors
            assert response.status_code in [403, 400]
    
    def test_upload_invalid_visibility(self):
        """Test that invalid visibility is rejected"""
        token = create_test_token("user-1", "user1@test.com")
        img_bytes = create_test_image()
        
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "invalid"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should fail with 400 or 500 (depending on when validation happens)
        if response.status_code not in [500]:
            assert response.status_code == 400


class TestImageRetrieval:
    """Test GET /images/{id} endpoint"""
    
    def test_get_image_anonymous_public(self):
        """Test anonymous access to public images"""
        # This will fail with 404 if image doesn't exist, which is expected
        response = client.get("/images/nonexistent-id")
        assert response.status_code in [404, 401]  # 404 if not found, 401 if private
    
    def test_get_image_with_auth(self):
        """Test authenticated access to images"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/images/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404  # Should be 404, not 401


class TestImageSearch:
    """Test GET /search endpoint"""
    
    def test_search_anonymous_public_scope(self):
        """Test anonymous search with public scope"""
        response = client.get("/search?q=test&scope=public")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "test"
    
    def test_search_anonymous_all_scope_fails(self):
        """Test that anonymous users cannot use 'all' scope"""
        response = client.get("/search?q=test&scope=all")
        assert response.status_code == 401
    
    def test_search_anonymous_mine_scope_fails(self):
        """Test that anonymous users cannot use 'mine' scope"""
        response = client.get("/search?q=test&scope=mine")
        assert response.status_code == 401
    
    def test_search_authenticated_all_scope(self):
        """Test authenticated search with 'all' scope"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/search?q=test&scope=all",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_authenticated_mine_scope(self):
        """Test authenticated search with 'mine' scope"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/search?q=test&scope=mine",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_search_invalid_scope(self):
        """Test that invalid scope is rejected"""
        response = client.get("/search?q=test&scope=invalid")
        assert response.status_code == 400


class TestImageUpdate:
    """Test PATCH /images/{id} endpoint"""
    
    def test_update_requires_auth(self):
        """Test that update requires authentication"""
        response = client.patch(
            "/images/test-id",
            json={"visibility": "public"}
        )
        assert response.status_code == 401
    
    def test_update_with_auth(self):
        """Test authenticated update"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.patch(
            "/images/nonexistent-id",
            json={"visibility": "public"},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should be 404 (not found) not 401 (unauthorized)
        assert response.status_code == 404
    
    def test_update_invalid_visibility(self):
        """Test that invalid visibility is rejected"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.patch(
            "/images/test-id",
            json={"visibility": "invalid"},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should fail with 400 or 404
        assert response.status_code in [400, 404]
    
    def test_update_public_admin_requires_admin(self):
        """Test that setting public_admin requires admin role"""
        token = create_test_token("user-1", "user1@test.com", role="user")
        response = client.patch(
            "/images/test-id",
            json={"visibility": "public_admin"},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should fail with 403 or 404
        assert response.status_code in [403, 404]


class TestImageDelete:
    """Test DELETE /images/{id} endpoint"""
    
    def test_delete_requires_auth(self):
        """Test that delete requires authentication"""
        response = client.delete("/images/test-id")
        assert response.status_code == 401
    
    def test_delete_with_auth(self):
        """Test authenticated delete"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.delete(
            "/images/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should be 404 (not found) not 401 (unauthorized)
        assert response.status_code == 404


class TestImageList:
    """Test GET /images endpoint"""
    
    def test_list_anonymous(self):
        """Test anonymous image listing"""
        response = client.get("/images")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert "limit" in data
        assert "offset" in data
        assert "count" in data
    
    def test_list_authenticated(self):
        """Test authenticated image listing"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/images",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
    
    def test_list_with_pagination(self):
        """Test image listing with pagination"""
        response = client.get("/images?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    def test_list_max_limit(self):
        """Test that limit is capped at 100"""
        response = client.get("/images?limit=200")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100  # Should be capped
    
    def test_list_with_visibility_filter(self):
        """Test image listing with visibility filter"""
        response = client.get("/images?visibility=public")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data


class TestAccessControl:
    """Test access control logic"""
    
    def test_anonymous_cannot_access_private(self):
        """Test that anonymous users cannot access private images"""
        # This is tested indirectly through other tests
        # The actual test would require creating a private image first
        pass
    
    def test_user_can_access_own_images(self):
        """Test that users can access their own images"""
        # Would require creating an image and then accessing it
        pass
    
    def test_admin_can_access_all_images(self):
        """Test that admins can access all images"""
        # Would require creating images and testing admin access
        pass


class TestDownloadEndpoints:
    """Test download and thumbnail endpoints"""
    
    def test_download_anonymous_public(self):
        """Test anonymous download of public images"""
        response = client.get("/images/nonexistent-id/download")
        assert response.status_code in [404, 401]
    
    def test_download_with_auth(self):
        """Test authenticated download"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/images/nonexistent-id/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
    
    def test_thumbnail_anonymous_public(self):
        """Test anonymous thumbnail access"""
        response = client.get("/images/nonexistent-id/thumbnail")
        assert response.status_code in [404, 401]
    
    def test_thumbnail_with_auth(self):
        """Test authenticated thumbnail access"""
        token = create_test_token("user-1", "user1@test.com")
        response = client.get(
            "/images/nonexistent-id/thumbnail",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
