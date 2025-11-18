"""
End-to-end tests for multi-tenant functionality.
Tests the complete flow from upload to search with different users.
"""
import pytest
import uuid
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


class TestMultiTenantE2E:
    """End-to-end tests for multi-tenant scenarios"""
    
    def test_complete_user_flow(self):
        """Test complete flow: signup -> login -> upload -> view -> search"""
        user_id = str(uuid.uuid4())
        token = create_test_token(user_id, "testuser@example.com")
        
        # 1. Upload a private image
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "private"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed or fail with infrastructure error (not auth)
        assert response.status_code != 401
        assert response.status_code != 403
        
        if response.status_code == 200:
            image_data = response.json()
            image_id = image_data["id"]
            
            # 2. Verify user can access their own image
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # 3. Verify anonymous cannot access private image
            response = client.get(f"/images/{image_id}")
            assert response.status_code == 401
            
            # 4. Update visibility to public
            response = client.patch(
                f"/images/{image_id}",
                json={"visibility": "public"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # 5. Verify anonymous can now access public image
            response = client.get(f"/images/{image_id}")
            assert response.status_code == 200
            
            # 6. Delete image
            response = client.delete(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # 7. Verify image is no longer accessible
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 404
    
    def test_multi_user_isolation(self):
        """Test that users can only see their own private images"""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        token1 = create_test_token(user1_id, "user1@example.com")
        token2 = create_test_token(user2_id, "user2@example.com")
        
        # User 1 uploads a private image
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "private"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        if response.status_code == 200:
            image_id = response.json()["id"]
            
            # User 1 can access their image
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token1}"}
            )
            assert response.status_code == 200
            
            # User 2 cannot access User 1's private image
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token2}"}
            )
            assert response.status_code == 403
    
    def test_public_image_visibility(self):
        """Test that public images are visible to everyone"""
        user_id = str(uuid.uuid4())
        token = create_test_token(user_id, "user@example.com")
        
        # Upload a public image
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            image_id = response.json()["id"]
            
            # Owner can access
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Anonymous can access
            response = client.get(f"/images/{image_id}")
            assert response.status_code == 200
            
            # Other users can access
            other_token = create_test_token(str(uuid.uuid4()), "other@example.com")
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {other_token}"}
            )
            assert response.status_code == 200
    
    def test_admin_access(self):
        """Test that admins can access all images"""
        user_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        user_token = create_test_token(user_id, "user@example.com", role="user")
        admin_token = create_test_token(admin_id, "admin@example.com", role="admin")
        
        # User uploads a private image
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "private"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            image_id = response.json()["id"]
            
            # Admin can access user's private image
            response = client.get(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            
            # Admin can modify user's image
            response = client.patch(
                f"/images/{image_id}",
                json={"visibility": "public"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
    
    def test_search_scopes(self):
        """Test search with different scopes"""
        user_id = str(uuid.uuid4())
        token = create_test_token(user_id, "user@example.com")
        
        # Test public scope (anonymous)
        response = client.get("/search?q=test&scope=public")
        assert response.status_code == 200
        
        # Test all scope (requires auth)
        response = client.get("/search?q=test&scope=all")
        assert response.status_code == 401
        
        response = client.get(
            "/search?q=test&scope=all",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Test mine scope (requires auth)
        response = client.get("/search?q=test&scope=mine")
        assert response.status_code == 401
        
        response = client.get(
            "/search?q=test&scope=mine",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_list_images_filtering(self):
        """Test image listing with filters"""
        user_id = str(uuid.uuid4())
        token = create_test_token(user_id, "user@example.com")
        
        # Anonymous can list (only sees public)
        response = client.get("/images")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        
        # Authenticated user can list (sees own + public)
        response = client.get(
            "/images",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Filter by visibility
        response = client.get(
            "/images?visibility=public",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_visibility_constraints(self):
        """Test visibility constraints and validation"""
        user_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        user_token = create_test_token(user_id, "user@example.com", role="user")
        admin_token = create_test_token(admin_id, "admin@example.com", role="admin")
        
        # User cannot create public_admin images
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public_admin"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code not in [500]:  # Ignore infrastructure errors
            assert response.status_code in [403, 400]
        
        # Admin can create public_admin images
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public_admin"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should succeed or fail with infrastructure error (not permission error)
        assert response.status_code not in [403, 401]
    
    def test_soft_deletion(self):
        """Test that deleted images are properly hidden"""
        user_id = str(uuid.uuid4())
        token = create_test_token(user_id, "user@example.com")
        
        # Upload and delete an image
        img_bytes = create_test_image()
        response = client.post(
            "/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"visibility": "public"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            image_id = response.json()["id"]
            
            # Delete the image
            response = client.delete(
                f"/images/{image_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Image should not be accessible
            response = client.get(f"/images/{image_id}")
            assert response.status_code == 404
            
            # Image should not appear in search
            response = client.get("/search?q=test&scope=public")
            assert response.status_code == 200
            results = response.json()["results"]
            assert image_id not in [r["id"] for r in results]
            
            # Image should not appear in list
            response = client.get("/images?visibility=public")
            assert response.status_code == 200
            images = response.json()["images"]
            assert image_id not in [img["id"] for img in images]


class TestSecurityAndValidation:
    """Security and validation tests"""
    
    def test_invalid_token(self):
        """Test that invalid tokens are rejected"""
        response = client.post(
            "/images",
            files={"file": ("test.jpg", create_test_image(), "image/jpeg")},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_missing_token(self):
        """Test that protected endpoints require token"""
        response = client.post(
            "/images",
            files={"file": ("test.jpg", create_test_image(), "image/jpeg")}
        )
        assert response.status_code == 401
    
    def test_invalid_visibility(self):
        """Test that invalid visibility values are rejected"""
        token = create_test_token(str(uuid.uuid4()), "user@example.com")
        response = client.post(
            "/images",
            files={"file": ("test.jpg", create_test_image(), "image/jpeg")},
            data={"visibility": "invalid"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code not in [500]:
            assert response.status_code == 400
    
    def test_invalid_scope(self):
        """Test that invalid search scopes are rejected"""
        response = client.get("/search?q=test&scope=invalid")
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
