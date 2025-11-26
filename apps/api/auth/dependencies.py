"""
FastAPI dependencies for authentication and authorization.
Provides JWT validation and role-based access control.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from apps.api.auth.models import CurrentUser, TokenPayload
from apps.api.storage.models import Profile

logger = logging.getLogger(__name__)

# Database session for profile management
_profile_session = None

def get_profile_session():
    """Get or create database session for profile management"""
    global _profile_session
    if _profile_session is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL not configured")
        engine = create_engine(db_url, pool_pre_ping=True)
        _profile_session = sessionmaker(bind=engine)
    return _profile_session()

# HTTP Bearer token security scheme (extracts "Bearer <token>" from Authorization header)
security = HTTPBearer(auto_error=False)


def ensure_profile_exists(user_id: str, email: str, role: str) -> None:
    """
    Ensure a profile exists for the user. Create one if it doesn't exist.
    This is called automatically when a user authenticates.
    """
    db = None
    try:
        logger.info(f"Checking profile for user {user_id}")
        db = get_profile_session()
        # Check if profile exists
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if not profile:
            logger.info(f"Profile not found, creating for user {user_id} ({email})")
            # Create new profile
            profile = Profile(
                id=user_id,
                email=email,
                role=role
            )
            db.add(profile)
            db.commit()
            logger.info(f"✓ Created profile for user {user_id} ({email})")
        else:
            logger.info(f"Profile already exists for user {user_id}")
    except IntegrityError as e:
        # Log the full error details
        error_msg = str(e)
        logger.error(f"IntegrityError creating profile for {user_id}: {error_msg}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        
        # Check if it's a duplicate key error (profile already exists)
        if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
            logger.info(f"Profile already exists (race condition): {user_id}")
            if db:
                db.rollback()
        else:
            # Different integrity error - log and re-raise
            logger.error(f"NON-DUPLICATE IntegrityError creating profile for {user_id}", exc_info=True)
            if db:
                db.rollback()
            raise
    except Exception as e:
        logger.error(f"ERROR ensuring profile exists for {user_id}: {str(e)}", exc_info=True)
        if db:
            db.rollback()
        raise  # Re-raise to see the error
    finally:
        if db:
            db.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Extract and validate Supabase JWT from Authorization header.
    Returns None for anonymous users (no authentication required).
    
    Also supports SEEDING_API_KEY for automated seeding scripts.
    
    This is the main authentication dependency. Use it for endpoints that
    work differently for authenticated vs anonymous users.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(user: Optional[CurrentUser] = Depends(get_current_user)):
            if user:
                # Authenticated user logic
            else:
                # Anonymous user logic
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
    
    Returns:
        CurrentUser if authenticated, None if anonymous
    
    Raises:
        HTTPException: 401 if token is invalid or expired
        HTTPException: 500 if JWT secret is not configured
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Check for seeding API key (for automated scripts)
    seeding_api_key = os.getenv("SEEDING_API_KEY")
    if seeding_api_key and token == seeding_api_key:
        admin_user_id = os.getenv("ADMIN_USER_ID")
        if not admin_user_id:
            logger.error("SEEDING_API_KEY provided but ADMIN_USER_ID not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Seeding not configured properly"
            )
        
        logger.info(f"Seeding API key authenticated - using admin user {admin_user_id}")
        # Return admin user for seeding
        return CurrentUser(
            id=admin_user_id,
            email="seeding@example.com",
            role="admin"
        )
    
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured"
        )
    
    try:
        # Decode and validate JWT
        # Supabase uses HS256 algorithm and "authenticated" audience
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True, "verify_exp": True}
        )
        
        # Parse token payload
        token_data = TokenPayload(**payload)
        
        if not token_data.sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        
        # Ensure profile exists in database (auto-create if needed)
        user_id = token_data.sub
        email = token_data.email or ""
        # Map Supabase roles to our application roles
        # Supabase uses 'authenticated' for regular users, we use 'user'
        supabase_role = token_data.role or "authenticated"
        role = "admin" if supabase_role == "admin" else "user"
        ensure_profile_exists(user_id, email, role)
        
        # Create CurrentUser from token
        return CurrentUser(
            id=user_id,
            email=email,
            role=role
        )
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def require_auth(
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> CurrentUser:
    """
    Require authentication (401 if not logged in).
    
    Use this for endpoints that require a logged-in user.
    
    Usage:
        @app.post("/images")
        async def create_image(user: CurrentUser = Depends(require_auth)):
            # user is guaranteed to be authenticated
            # user.id, user.email, user.role are available
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        CurrentUser (guaranteed to be not None)
    
    Raises:
        HTTPException: 401 if user is not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(require_auth)
) -> CurrentUser:
    """
    Require admin role (403 if not admin).
    
    Use this for admin-only endpoints.
    
    Usage:
        @app.delete("/admin/images/{id}")
        async def admin_delete(
            id: str,
            admin: CurrentUser = Depends(require_admin)
        ):
            # admin is guaranteed to have admin role
    
    Args:
        current_user: Current user from require_auth dependency
    
    Returns:
        CurrentUser with admin role
    
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Same as get_current_user but doesn't raise exceptions.
    Returns None if token is invalid or missing.
    
    Useful for endpoints that work differently for authenticated vs anonymous users
    but don't want to fail on invalid tokens.
    
    Usage:
        @app.get("/search")
        async def search(user: Optional[CurrentUser] = Depends(get_optional_user)):
            # user might be None (anonymous or invalid token)
            # Handle gracefully without raising exceptions
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
    
    Returns:
        CurrentUser if authenticated and valid, None otherwise
    """
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
