"""Pydantic schemas for authentication API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ============================================================================
# Registration & Login
# ============================================================================


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)


class RegisterResponse(BaseModel):
    """Response model for successful registration."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    display_name: str | None
    message: str = "Registration successful"


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response model for successful login."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    display_name: str | None
    message: str = "Login successful"


# ============================================================================
# User Profile
# ============================================================================


class UserResponse(BaseModel):
    """Response model for current user."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    display_name: str | None
    email_verified: bool
    is_admin: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""

    display_name: str | None = Field(None, max_length=100)


# ============================================================================
# Sessions Management
# ============================================================================


class AuthSessionInfo(BaseModel):
    """Information about an active session."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_active_at: datetime
    is_current: bool = False


class AuthSessionListResponse(BaseModel):
    """Response model for listing user sessions."""

    sessions: list[AuthSessionInfo]
    total: int


# ============================================================================
# Device Tokens
# ============================================================================


class DeviceTokenInfo(BaseModel):
    """Information about a device token."""

    model_config = ConfigDict(from_attributes=True)

    token_id: str
    device_name: str
    created_at: datetime
    last_used_at: datetime | None


class DeviceTokenListResponse(BaseModel):
    """Response model for listing device tokens."""

    devices: list[DeviceTokenInfo]
    total: int


# ============================================================================
# Device Authorization Flow (RFC 8628 style)
# ============================================================================


class DeviceAuthorizationRequest(BaseModel):
    """Request model for initiating device authorization."""

    device_name: str = Field(max_length=100)


class DeviceAuthorizationResponse(BaseModel):
    """Response model for device authorization initiation."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int  # seconds
    interval: int  # polling interval in seconds


class DeviceTokenRequest(BaseModel):
    """Request model for polling device token."""

    device_code: str


class DeviceTokenResponse(BaseModel):
    """Response model for successful device token exchange."""

    access_token: str
    token_type: str = "Bearer"
    device_name: str


class DeviceAuthorizationError(BaseModel):
    """Error response for device authorization."""

    error: str  # authorization_pending, slow_down, access_denied, expired_token
    error_description: str | None = None


class AuthorizeDeviceRequest(BaseModel):
    """Request model for authorizing a device (from web UI)."""

    user_code: str = Field(min_length=8, max_length=8)
    approve: bool = True


class DeviceAuthorizationStatus(BaseModel):
    """Response model for checking device authorization status."""

    device_name: str
    status: str  # pending, authorized, denied, expired
    created_at: datetime
    expires_at: datetime
