"""
Tests for authentication and authorization.
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from jose import jwt
import os
from datetime import datetime, timedelta

client = TestClient(app)


def create_test_token(user_id: str, email: str, role: str = "user") -> str:
    """
    Create a test JWT token for testing.
    Uses a test secret if SUPABASE_JWT_SECRET is not set.
    """
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


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_auth_me_anonymous(self):
        """Test /auth/me without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
    
    def test_auth_me_authenticated(self):
        """Test /auth/me with valid token"""
        token = create_test_token("user-123", "test@example.com")
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["id"] == "user-123"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"
    
    def test_auth_check_requires_auth(self):
        """Test /auth/check requires authentication"""
        response = client.get("/auth/check")
        assert response.status_code == 401  # No credentials provided
    
    def test_auth_check_with_token(self):
        """Test /auth/check with valid token"""
        token = create_test_token("user-123", "test@example.com")
        response = client.get(
            "/auth/check",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
    
    def test_admin_endpoint_requires_admin(self):
        """Test admin endpoint rejects non-admin users"""
        token = create_test_token("user-123", "test@example.com", role="user")
        response = client.get(
            "/admin/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    def test_admin_endpoint_allows_admin(self):
        """Test admin endpoint allows admin users"""
        token = create_test_token("admin-123", "admin@example.com", role="admin")
        response = client.get(
            "/admin/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["admin"]["id"] == "admin-123"
    
    def test_invalid_token(self):
        """Test invalid token is rejected"""
        response = client.get(
            "/auth/check",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_expired_token(self):
        """Test expired token is rejected"""
        secret = os.getenv("SUPABASE_JWT_SECRET", "test-secret-for-development-only")
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "user",
            "aud": "authenticated",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        response = client.get(
            "/auth/check",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
    
    def test_wrong_audience(self):
        """Test token with wrong audience is rejected"""
        secret = os.getenv("SUPABASE_JWT_SECRET", "test-secret-for-development-only")
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "user",
            "aud": "wrong-audience",  # Wrong audience
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        response = client.get(
            "/auth/check",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


class TestCurrentUserModel:
    """Test CurrentUser model methods"""
    
    def test_is_admin(self):
        """Test is_admin method"""
        from apps.api.auth.models import CurrentUser
        
        user = CurrentUser(id="1", email="user@test.com", role="user")
        assert user.is_admin() is False
        
        admin = CurrentUser(id="2", email="admin@test.com", role="admin")
        assert admin.is_admin() is True
    
    def test_can_access_image_public(self):
        """Test access to public images"""
        from apps.api.auth.models import CurrentUser
        
        user = CurrentUser(id="user-1", email="user@test.com", role="user")
        
        # Public images accessible to all
        assert user.can_access_image("other-user", "public") is True
        assert user.can_access_image("other-user", "public_admin") is True
    
    def test_can_access_image_private(self):
        """Test access to private images"""
        from apps.api.auth.models import CurrentUser
        
        user = CurrentUser(id="user-1", email="user@test.com", role="user")
        admin = CurrentUser(id="admin-1", email="admin@test.com", role="admin")
        
        # Own private images accessible
        assert user.can_access_image("user-1", "private") is True
        
        # Others' private images not accessible
        assert user.can_access_image("user-2", "private") is False
        
        # Admin can access all private images
        assert admin.can_access_image("user-1", "private") is True
    
    def test_can_modify_image(self):
        """Test image modification permissions"""
        from apps.api.auth.models import CurrentUser
        
        user = CurrentUser(id="user-1", email="user@test.com", role="user")
        admin = CurrentUser(id="admin-1", email="admin@test.com", role="admin")
        
        # Can modify own images
        assert user.can_modify_image("user-1") is True
        
        # Cannot modify others' images
        assert user.can_modify_image("user-2") is False
        
        # Admin can modify all images
        assert admin.can_modify_image("user-1") is True
        assert admin.can_modify_image("user-2") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
