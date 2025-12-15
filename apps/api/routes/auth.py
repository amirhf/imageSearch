"""Authentication routes"""
from fastapi import APIRouter, Depends
from typing import Optional

from apps.api.auth.dependencies import get_current_user, require_auth, require_admin
from apps.api.auth.models import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: Optional[CurrentUser] = Depends(get_current_user)):
    """
    Get current user info from JWT.
    Useful for debugging and client-side auth state management.
    Returns authenticated=false if no valid token provided.
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


@router.get("/check")
async def check_auth(current_user: CurrentUser = Depends(require_auth)):
    """
    Protected endpoint to verify authentication.
    Returns 401 if not authenticated.
    Useful for testing auth flow.
    """
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    }


# Admin routes under /admin prefix
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/health")
async def admin_health(admin: CurrentUser = Depends(require_admin)):
    """
    Admin-only endpoint for testing role-based access.
    Returns 403 if user is not an admin.
    """
    return {
        "status": "ok",
        "admin": {
            "id": admin.id,
            "email": admin.email
        }
    }
