"""
Authentication module for multi-tenant support.
Provides JWT validation and user authentication via Supabase.
"""
from apps.api.auth.models import CurrentUser, TokenPayload
from apps.api.auth.dependencies import (
    get_current_user,
    require_auth,
    require_admin,
    get_optional_user
)

__all__ = [
    "CurrentUser",
    "TokenPayload",
    "get_current_user",
    "require_auth",
    "require_admin",
    "get_optional_user",
]
