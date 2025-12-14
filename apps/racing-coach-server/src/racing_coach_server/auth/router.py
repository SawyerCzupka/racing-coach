"""FastAPI route handlers for authentication."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.auth.exceptions import (
    DeviceAuthorizationDeniedError,
    DeviceAuthorizationExpiredError,
    DeviceAuthorizationPendingError,
    InvalidCredentialsError,
    SessionNotFoundError,
    UserAlreadyExistsError,
)
from racing_coach_server.auth.models import User
from racing_coach_server.auth.schemas import (
    AuthorizeDeviceRequest,
    DeviceAuthorizationRequest,
    DeviceAuthorizationResponse,
    DeviceAuthorizationStatus,
    DeviceTokenInfo,
    DeviceTokenListResponse,
    DeviceTokenRequest,
    DeviceTokenResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SessionInfo,
    SessionListResponse,
    UserResponse,
)
from racing_coach_server.auth.service import AuthService
from racing_coach_server.auth.utils import hash_token
from racing_coach_server.config import settings
from racing_coach_server.database.engine import get_async_session, transactional_session

logger = logging.getLogger(__name__)

router = APIRouter()

# Cookie configuration
SESSION_COOKIE_NAME = "session_token"
SESSION_COOKIE_MAX_AGE = settings.web_session_duration_days * 24 * 60 * 60  # in seconds

# Device token header
device_token_header = APIKeyHeader(name="X-Device-Token", auto_error=False)


# ============================================================================
# Dependencies
# ============================================================================


async def get_auth_service(
    db: AsyncSession = Depends(get_async_session),  # noqa: B008
) -> AuthService:
    """Provide AuthService with injected AsyncSession."""
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _set_session_cookie(response: Response, token: str) -> None:
    """Set httpOnly session cookie."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Clear session cookie."""
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )


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


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


# ============================================================================
# Registration & Login
# ============================================================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
async def register(
    request_body: RegisterRequest,
    response: Response,
    request: Request,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> RegisterResponse:
    """Register a new user account."""
    try:
        async with transactional_session(db):
            user = await auth_service.register_user(
                email=request_body.email,
                password=request_body.password,
                display_name=request_body.display_name,
            )

            # Auto-login after registration
            _, token = await auth_service.create_session(
                user=user,
                user_agent=request.headers.get("user-agent"),
                ip_address=request.client.host if request.client else None,
            )
            _set_session_cookie(response, token)

            return RegisterResponse(
                user_id=str(user.id),
                email=user.email,
                display_name=user.display_name,
            )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post(
    "/login",
    response_model=LoginResponse,
    tags=["auth"],
)
async def login(
    request_body: LoginRequest,
    response: Response,
    request: Request,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    """Login with email and password."""
    try:
        async with transactional_session(db):
            user = await auth_service.authenticate_user(
                email=request_body.email,
                password=request_body.password,
            )

            _, token = await auth_service.create_session(
                user=user,
                user_agent=request.headers.get("user-agent"),
                ip_address=request.client.host if request.client else None,
            )
            _set_session_cookie(response, token)

            return LoginResponse(
                user_id=str(user.id),
                email=user.email,
                display_name=user.display_name,
            )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None


@router.post("/logout", tags=["auth"])
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Logout current session."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        async with transactional_session(db):
            # Find and revoke the current session
            token_hash = hash_token(session_token)
            session = await auth_service.get_session_by_token_hash(token_hash)
            if session:
                await auth_service.revoke_session(session.id, current_user.id)

    _clear_session_cookie(response)
    return {"message": "Logged out successfully"}


# ============================================================================
# User Profile
# ============================================================================


@router.get("/me", response_model=UserResponse, tags=["auth"])
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current user profile."""
    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        email_verified=current_user.email_verified_at is not None,
        created_at=current_user.created_at,
    )


# ============================================================================
# Session Management
# ============================================================================


@router.get("/sessions", response_model=SessionListResponse, tags=["auth"])
async def list_sessions(
    request: Request,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> SessionListResponse:
    """List all active sessions for current user."""
    sessions = await auth_service.get_user_sessions(current_user.id)
    current_token = request.cookies.get(SESSION_COOKIE_NAME)
    current_hash = hash_token(current_token) if current_token else None

    return SessionListResponse(
        sessions=[
            SessionInfo(
                session_id=str(s.id),
                user_agent=s.user_agent,
                ip_address=s.ip_address,
                created_at=s.created_at,
                last_active_at=s.last_active_at,
                is_current=s.token_hash == current_hash if current_hash else False,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.delete("/sessions/{session_id}", tags=["auth"])
async def revoke_session(
    session_id: UUID,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Revoke a specific session."""
    try:
        async with transactional_session(db):
            await auth_service.revoke_session(session_id, current_user.id)
            return {"message": "Session revoked"}
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from None


# ============================================================================
# Device Token Management
# ============================================================================


@router.get("/devices", response_model=DeviceTokenListResponse, tags=["auth"])
async def list_devices(
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> DeviceTokenListResponse:
    """List all device tokens for current user."""
    tokens = await auth_service.get_user_device_tokens(current_user.id)
    return DeviceTokenListResponse(
        devices=[
            DeviceTokenInfo(
                token_id=str(t.id),
                device_name=t.device_name,
                created_at=t.created_at,
                last_used_at=t.last_used_at,
            )
            for t in tokens
        ],
        total=len(tokens),
    )


@router.delete("/devices/{token_id}", tags=["auth"])
async def revoke_device(
    token_id: UUID,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Revoke a device token."""
    try:
        async with transactional_session(db):
            await auth_service.revoke_device_token(token_id, current_user.id)
            return {"message": "Device revoked"}
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        ) from None


# ============================================================================
# Device Authorization Flow
# ============================================================================


@router.post(
    "/device/authorize",
    response_model=DeviceAuthorizationResponse,
    tags=["auth", "device"],
)
async def initiate_device_authorization(
    request_body: DeviceAuthorizationRequest,
    request: Request,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> DeviceAuthorizationResponse:
    """
    Initiate OAuth device authorization flow.

    Called by desktop client to get device_code and user_code.
    The user_code should be displayed to the user who then enters it
    at the verification_uri in their browser.
    """
    async with transactional_session(db):
        auth = await auth_service.initiate_device_authorization(request_body.device_name)

        # Build verification URI based on request
        base_url = str(request.base_url).rstrip("/")
        verification_uri = f"{base_url}/auth/device"

        return DeviceAuthorizationResponse(
            device_code=auth.device_code,
            user_code=auth.user_code,
            verification_uri=verification_uri,
            expires_in=settings.device_auth_expiration_minutes * 60,
            interval=auth.interval,
        )


@router.post("/device/token", tags=["auth", "device"])
async def poll_device_token(
    request_body: DeviceTokenRequest,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> DeviceTokenResponse:
    """
    Poll for device token.

    Called by desktop client after initiating device authorization.
    The client should poll at the interval specified in the authorization response.

    Returns the access token if authorized, or an error response if still pending,
    denied, or expired.
    """
    try:
        async with transactional_session(db):
            device_token, raw_token = await auth_service.poll_device_authorization(
                request_body.device_code
            )
            return DeviceTokenResponse(
                access_token=raw_token,
                device_name=device_token.device_name,
            )
    except DeviceAuthorizationPendingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "authorization_pending",
                "error_description": "User has not yet authorized",
            },
        ) from None
    except DeviceAuthorizationDeniedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "access_denied",
                "error_description": "User denied authorization",
            },
        ) from None
    except DeviceAuthorizationExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "expired_token",
                "error_description": "Authorization has expired",
            },
        ) from None
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "Device authorization not found",
            },
        ) from None


@router.post("/device/confirm", tags=["auth", "device"])
async def authorize_device_from_web(
    request_body: AuthorizeDeviceRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Authorize a device from web UI.

    User enters the user_code shown on their desktop client.
    This endpoint requires authentication (user must be logged in via web).
    """
    try:
        async with transactional_session(db):
            await auth_service.authorize_device(
                user_code=request_body.user_code,
                user=current_user,
                approve=request_body.approve,
            )
            action = "approved" if request_body.approve else "denied"
            return {"message": f"Device {action} successfully"}
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device authorization not found or already processed",
        ) from None
    except DeviceAuthorizationExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device authorization has expired",
        ) from None


@router.get(
    "/device/status/{user_code}", response_model=DeviceAuthorizationStatus, tags=["auth", "device"]
)
async def get_device_authorization_status(
    user_code: str,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> DeviceAuthorizationStatus:
    """
    Get the status of a device authorization.

    Used by the web UI to show device details before confirming.
    """
    auth = await auth_service.get_device_authorization_by_user_code(user_code)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device authorization not found",
        )

    return DeviceAuthorizationStatus(
        device_name=auth.device_name,
        status=auth.status,
        created_at=auth.created_at,
        expires_at=auth.expires_at,
    )
