"""
Tests for authentication and authorization.
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from jose import jwt
import os
import base64
import time
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000123"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000999"


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


def _base64url_uint(value: int) -> str:
    return base64.urlsafe_b64encode(value.to_bytes(32, "big")).rstrip(b"=").decode()


def create_es256_test_token(user_id: str, email: str, role: str = "user") -> tuple[str, dict]:
    """Create an ES256 token and public JWK for Supabase signing-key tests."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": _base64url_uint(public_numbers.x),
        "y": _base64url_uint(public_numbers.y),
        "alg": "ES256",
        "kid": "test-es256-key",
    }
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(
        payload,
        private_pem,
        algorithm="ES256",
        headers={"kid": jwk["kid"]},
    )
    return token, jwk


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
        token = create_test_token(TEST_USER_ID, "test@example.com")
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["id"] == TEST_USER_ID
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"

    def test_auth_me_authenticated_es256_jwks(self, monkeypatch):
        """Test /auth/me with a Supabase asymmetric signing-key token."""
        from apps.api.auth import dependencies as auth_deps

        token, jwk = create_es256_test_token(TEST_USER_ID, "test@example.com")
        monkeypatch.setattr(auth_deps, "_jwks_cache", {"keys": [jwk]})
        monkeypatch.setattr(auth_deps, "_jwks_cache_expires_at", time.time() + 60)

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["id"] == TEST_USER_ID
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"
    
    def test_auth_check_requires_auth(self):
        """Test /auth/check requires authentication"""
        response = client.get("/auth/check")
        assert response.status_code == 401  # No credentials provided
    
    def test_auth_check_with_token(self):
        """Test /auth/check with valid token"""
        token = create_test_token(TEST_USER_ID, "test@example.com")
        response = client.get(
            "/auth/check",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
    
    def test_admin_endpoint_requires_admin(self):
        """Test admin endpoint rejects non-admin users"""
        token = create_test_token(TEST_USER_ID, "test@example.com", role="user")
        response = client.get(
            "/admin/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    def test_admin_endpoint_allows_admin(self):
        """Test admin endpoint allows admin users"""
        token = create_test_token(TEST_ADMIN_ID, "admin@example.com", role="admin")
        response = client.get(
            "/admin/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["admin"]["id"] == TEST_ADMIN_ID
    
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
            "sub": TEST_USER_ID,
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
            "sub": TEST_USER_ID,
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
