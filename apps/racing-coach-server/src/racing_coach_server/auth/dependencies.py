"""Authentication dependency injection functions for FastAPI route handlers.

This module is separate from the router to avoid circular imports.
The main dependencies.py module re-exports these for convenience.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from racing_coach_server.auth.models import User
from racing_coach_server.auth.service import AuthService
from racing_coach_server.database.dependencies import AsyncSessionDep

# Device token header
device_token_header = APIKeyHeader(name="X-Device-Token", auto_error=False)

# Cookie configuration (imported from config in router.py, but we need the name here)
SESSION_COOKIE_NAME = "session_token"


async def get_auth_service(db: AsyncSessionDep) -> AuthService:
    """Provide AuthService with injected AsyncSession."""
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user_optional(
    request: Request,
    device_token: Annotated[str | None, Depends(device_token_header)],
    auth_service: AuthServiceDep,
) -> User | None:
    """Get current user from session cookie or device token (optional)."""
    # Try device token first (for desktop client)
    if device_token:
        user = await auth_service.validate_device_token(device_token)
        if user:
            return user

    # Try session cookie (for web)
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        return await auth_service.validate_session(session_token)

    return None


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Require authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[User | None, Depends(get_current_user_optional)]


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require authenticated admin user."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


AdminUserDep = Annotated[User, Depends(require_admin)]
