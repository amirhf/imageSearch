# Phase 2: Authentication & Authorization

**Estimated Time:** 3-4 days

## Overview

Implement Supabase-based authentication with JWT validation and role-based access control.

## 2.1 Install Dependencies

Add required packages for JWT validation and Supabase integration.

**Update:** `apps/api/requirements.base.txt`

```txt
# Add these lines
supabase==2.3.0
python-jose[cryptography]==3.3.0
```

**Install:**
```bash
pip install supabase==2.3.0 python-jose[cryptography]==3.3.0
```

## 2.2 Environment Configuration

Add Supabase credentials to your environment files.

**Update:** `.env` and `.env.docker`

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-for-hs256-projects
SUPABASE_SECRET_KEY=sb_secret_your-secret-key

# Admin user (for migrations and seeding)
ADMIN_USER_ID=uuid-of-admin-user
```

**How to get these values:**
1. Go to Supabase Dashboard → Project Settings → API
2. Copy `Project URL` → `SUPABASE_URL`
3. Copy `JWT Secret` → `SUPABASE_JWT_SECRET` if your project still signs Auth JWTs with legacy/shared-secret `HS256`
4. Copy a secret API key (`sb_secret_...`) → `SUPABASE_SECRET_KEY`

Secret keys bypass Row Level Security and must only be used from backend components you control. Client applications should use a publishable key (`sb_publishable_...`) through `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
Projects using Supabase's asymmetric JWT signing keys (`ES256`/`RS256`) are verified through the JWKS endpoint derived from `SUPABASE_URL`.

## 2.3 Create Auth Module Structure

Create the authentication module:

```bash
mkdir -p apps/api/auth
touch apps/api/auth/__init__.py
touch apps/api/auth/dependencies.py
touch apps/api/auth/models.py
```

## 2.4 Auth Models

Define the user model for type safety.

**File:** `apps/api/auth/models.py`

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CurrentUser(BaseModel):
    """Represents the currently authenticated user from JWT"""
    id: str  # UUID from Supabase
    email: EmailStr
    role: str = "user"  # 'user' or 'admin'
    
    class Config:
        frozen = True  # Immutable
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == "admin"
    
    def can_access_image(self, image_owner_id: Optional[str], image_visibility: str) -> bool:
        """Check if user can access an image"""
        # Public images are accessible to all
        if image_visibility in ('public', 'public_admin'):
            return True
        
        # Private images only accessible to owner or admin
        if image_visibility == 'private':
            return self.id == image_owner_id or self.is_admin()
        
        return False
    
    def can_modify_image(self, image_owner_id: Optional[str]) -> bool:
        """Check if user can modify an image"""
        return self.id == image_owner_id or self.is_admin()


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str  # Subject (user ID)
    email: Optional[str] = None
    role: Optional[str] = "user"
    aud: str = "authenticated"
    exp: Optional[int] = None
    iat: Optional[int] = None
```

## 2.5 Auth Dependencies

Create FastAPI dependencies for authentication and authorization.

**File:** `apps/api/auth/dependencies.py`

The implementation should:
- Extract the `Authorization: Bearer <access_token>` header with `HTTPBearer`.
- Return `None` for anonymous routes when no token is present.
- Validate legacy/shared-secret `HS256` tokens with `SUPABASE_JWT_SECRET`.
- Validate asymmetric `ES256`/`RS256` Supabase Auth tokens through the project JWKS endpoint at `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`.
- Map the Supabase token subject (`sub`) to `CurrentUser.id`, then enforce `require_auth`, `require_admin`, and optional-user behavior in FastAPI dependencies.

Keep the source of truth in `apps/api/auth/dependencies.py` so JWT signing-key support stays in one place.

## 2.6 Add Auth Endpoints

Add authentication-related endpoints to the main API.

**Update:** `apps/api/main.py`

```python
from apps.api.auth.dependencies import get_current_user, require_auth, require_admin
from apps.api.auth.models import CurrentUser
from typing import Optional

# Add these endpoints

@app.get("/auth/me")
async def get_me(current_user: Optional[CurrentUser] = Depends(get_current_user)):
    """
    Get current user info from JWT.
    Useful for debugging and client-side auth state management.
    """
    if not current_user:
        return {
            "authenticated": False,
            "user": None
        }
    
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    }


@app.get("/auth/check")
async def check_auth(current_user: CurrentUser = Depends(require_auth)):
    """
    Protected endpoint to verify authentication.
    Returns 401 if not authenticated.
    """
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    }


@app.get("/admin/health")
async def admin_health(admin: CurrentUser = Depends(require_admin)):
    """
    Admin-only endpoint for testing role-based access.
    """
    return {
        "status": "ok",
        "admin": {
            "id": admin.id,
            "email": admin.email
        }
    }
```

## 2.7 Update CORS Settings

Allow authentication headers in CORS configuration.

**Update:** `apps/api/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware (if not already present)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3100",  # Next.js dev server
        "http://localhost:3000",  # Alternative port
        os.getenv("FRONTEND_URL", "http://localhost:3100")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

## 2.8 Testing Authentication

Create tests to verify authentication works correctly.

**File:** `tests/test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from jose import jwt
import os
from datetime import datetime, timedelta

client = TestClient(app)

def create_test_token(user_id: str, email: str, role: str = "user") -> str:
    """Create a test JWT token"""
    secret = os.getenv("SUPABASE_JWT_SECRET", "test-secret")
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_auth_me_anonymous():
    """Test /auth/me without authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["user"] is None


def test_auth_me_authenticated():
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


def test_auth_check_requires_auth():
    """Test /auth/check requires authentication"""
    response = client.get("/auth/check")
    assert response.status_code == 401


def test_auth_check_with_token():
    """Test /auth/check with valid token"""
    token = create_test_token("user-123", "test@example.com")
    response = client.get(
        "/auth/check",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True


def test_admin_endpoint_requires_admin():
    """Test admin endpoint rejects non-admin users"""
    token = create_test_token("user-123", "test@example.com", role="user")
    response = client.get(
        "/admin/health",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_admin_endpoint_allows_admin():
    """Test admin endpoint allows admin users"""
    token = create_test_token("admin-123", "admin@example.com", role="admin")
    response = client.get(
        "/admin/health",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_invalid_token():
    """Test invalid token is rejected"""
    response = client.get(
        "/auth/check",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_expired_token():
    """Test expired token is rejected"""
    secret = os.getenv("SUPABASE_JWT_SECRET", "test-secret")
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
```

**Run tests:**
```bash
pytest tests/test_auth.py -v
```

## 2.9 Manual Testing with cURL

Test authentication endpoints manually:

```bash
# Test anonymous access
curl http://localhost:8000/auth/me

# Test with Supabase token (get from Supabase Dashboard or login)
export TOKEN="your-supabase-jwt-token"

# Test authenticated access
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/me

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/check

# Test admin endpoint (should fail for non-admin)
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/admin/health
```

## 2.10 Verification Checklist

- [ ] Dependencies installed (`supabase`, `python-jose`)
- [ ] Environment variables configured
- [ ] Auth module created with models and dependencies
- [ ] Auth endpoints added to main.py
- [ ] CORS configured to allow auth headers
- [ ] Tests pass successfully
- [ ] Manual testing with real Supabase tokens works

## Next Steps

Once Phase 2 is complete:
1. Test authentication with real Supabase users
2. Verify JWT validation works correctly
3. Proceed to **Phase 3: API Endpoints** to add auth to existing endpoints

## Troubleshooting

### Issue: "Authentication not configured" error
**Solution:** Ensure `SUPABASE_URL` is set. If your project uses legacy/shared-secret `HS256` Auth JWTs, also set `SUPABASE_JWT_SECRET`.

### Issue: Token validation fails
**Solution:** For `HS256` tokens, check that the JWT secret matches Supabase project settings. For `ES256`/`RS256` tokens, check that `SUPABASE_URL` is correct and the API can reach Supabase's JWKS endpoint.

### Issue: CORS errors in browser
**Solution:** Verify CORS middleware allows `Authorization` header and credentials

### Issue: 401 errors with valid token
**Solution:** Check token hasn't expired, verify `aud` claim is "authenticated"
