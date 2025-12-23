"""Authentication service for business logic."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.auth.exceptions import (
    DeviceAuthorizationDeniedError,
    DeviceAuthorizationExpiredError,
    DeviceAuthorizationPendingError,
    InvalidCredentialsError,
    SessionNotFoundError,
    UserAlreadyExistsError,
)
from racing_coach_server.auth.models import DeviceAuthorization, DeviceToken, User, UserSession
from racing_coach_server.auth.utils import (
    generate_device_code,
    generate_session_token,
    generate_user_code,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from racing_coach_server.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the auth service.

        Args:
            db: The async database session.
        """
        self.db = db

    # ========================================================================
    # User Management
    # ========================================================================

    async def register_user(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        """Register a new user.

        Args:
            email: The user's email address.
            password: The user's plaintext password.
            display_name: Optional display name.

        Returns:
            The created User object.

        Raises:
            UserAlreadyExistsError: If a user with this email already exists.
        """
        # Check if user already exists
        existing = await self._get_user_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info(f"Registered new user: {user.id}")
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials.

        Args:
            email: The user's email address.
            password: The user's plaintext password.

        Returns:
            The authenticated User object.

        Raises:
            InvalidCredentialsError: If credentials are invalid.
        """
        user = await self._get_user_by_email(email.lower())
        if not user or not user.is_active:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        # Rehash password if needed (e.g., after algorithm update)
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            await self.db.flush()

        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The User object or None if not found.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: The email address to look up.

        Returns:
            The User object or None if not found.
        """
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================================================
    # Web Session Management
    # ========================================================================

    async def create_session(
        self,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[UserSession, str]:
        """Create a new web session.

        Args:
            user: The user to create a session for.
            user_agent: The client's user agent string.
            ip_address: The client's IP address.

        Returns:
            A tuple of (UserSession, raw_token). The raw_token should be sent
            to the client; only the hash is stored.
        """
        token = generate_session_token()

        session = UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.web_session_duration_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(session)
        await self.db.flush()
        logger.info(f"Created session for user {user.id}")
        return session, token

    async def validate_session(self, token: str) -> User | None:
        """Validate session token and return user if valid.

        Args:
            token: The raw session token from the client.

        Returns:
            The User object if the session is valid, None otherwise.
        """
        token_hash = hash_token(token)

        stmt = select(UserSession).where(
            and_(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Update last active timestamp
        session.last_active_at = datetime.now(timezone.utc)
        await self.db.flush()

        return await self.get_user_by_id(session.user_id)

    async def get_user_sessions(self, user_id: UUID) -> list[UserSession]:
        """Get all active sessions for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of active UserSession objects.
        """
        stmt = (
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
            )
            .order_by(UserSession.last_active_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_session_by_token_hash(self, token_hash: str) -> UserSession | None:
        """Get a session by its token hash.

        Args:
            token_hash: The SHA-256 hash of the session token.

        Returns:
            The UserSession object or None if not found.
        """
        stmt = select(UserSession).where(UserSession.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: UUID, user_id: UUID) -> None:
        """Revoke a session (logout).

        Args:
            session_id: The session's UUID.
            user_id: The user's UUID (for authorization).

        Raises:
            SessionNotFoundError: If the session is not found.
        """
        stmt = select(UserSession).where(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        session.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        logger.info(f"Revoked session {session_id} for user {user_id}")

    async def revoke_all_sessions(
        self, user_id: UUID, except_session_id: UUID | None = None
    ) -> int:
        """Revoke all sessions for a user, optionally keeping one.

        Args:
            user_id: The user's UUID.
            except_session_id: Optional session ID to keep active.

        Returns:
            The number of sessions revoked.
        """
        sessions = await self.get_user_sessions(user_id)
        count = 0
        for session in sessions:
            if session.id != except_session_id:
                session.revoked_at = datetime.now(timezone.utc)
                count += 1
        await self.db.flush()
        return count

    # ========================================================================
    # Device Token Management
    # ========================================================================

    async def validate_device_token(self, token: str) -> User | None:
        """Validate device token and return user if valid.

        Args:
            token: The raw device token from the client.

        Returns:
            The User object if the token is valid, None otherwise.
        """
        token_hash = hash_token(token)

        stmt = select(DeviceToken).where(
            and_(
                DeviceToken.token_hash == token_hash,
                DeviceToken.revoked_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        device_token = result.scalar_one_or_none()

        if not device_token:
            return None

        # Check expiration if set
        if device_token.expires_at and device_token.expires_at < datetime.now(timezone.utc):
            return None

        # Update last used timestamp
        device_token.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        return await self.get_user_by_id(device_token.user_id)

    async def get_user_device_tokens(self, user_id: UUID) -> list[DeviceToken]:
        """Get all active device tokens for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of active DeviceToken objects.
        """
        stmt = (
            select(DeviceToken)
            .where(
                and_(
                    DeviceToken.user_id == user_id,
                    DeviceToken.revoked_at.is_(None),
                )
            )
            .order_by(DeviceToken.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def revoke_device_token(self, token_id: UUID, user_id: UUID) -> None:
        """Revoke a device token.

        Args:
            token_id: The device token's UUID.
            user_id: The user's UUID (for authorization).

        Raises:
            SessionNotFoundError: If the device token is not found.
        """
        stmt = select(DeviceToken).where(
            and_(
                DeviceToken.id == token_id,
                DeviceToken.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise SessionNotFoundError(f"Device token {token_id} not found")

        token.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        logger.info(f"Revoked device token {token_id} for user {user_id}")

    # ========================================================================
    # Device Authorization Flow (RFC 8628)
    # ========================================================================

    async def initiate_device_authorization(self, device_name: str) -> DeviceAuthorization:
        """Start OAuth device authorization flow.

        Args:
            device_name: A human-readable name for the device.

        Returns:
            The created DeviceAuthorization object.
        """
        auth = DeviceAuthorization(
            device_code=generate_device_code(),
            user_code=generate_user_code(),
            device_name=device_name,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.device_auth_expiration_minutes),
        )
        self.db.add(auth)
        await self.db.flush()
        logger.info(f"Initiated device authorization with user code {auth.user_code}")
        return auth

    async def get_device_authorization_by_user_code(
        self, user_code: str
    ) -> DeviceAuthorization | None:
        """Get device authorization by user code.

        Args:
            user_code: The user-facing code.

        Returns:
            The DeviceAuthorization object or None if not found.
        """
        stmt = select(DeviceAuthorization).where(DeviceAuthorization.user_code == user_code.upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def authorize_device(self, user_code: str, user: User, approve: bool) -> None:
        """Authorize or deny a device from web UI.

        Args:
            user_code: The user-facing code.
            user: The user authorizing the device.
            approve: Whether to approve or deny the authorization.

        Raises:
            SessionNotFoundError: If the authorization is not found.
            DeviceAuthorizationExpiredError: If the authorization has expired.
        """
        auth = await self.get_device_authorization_by_user_code(user_code)
        if not auth or auth.status != "pending":
            raise SessionNotFoundError("Device authorization not found or already processed")

        if auth.expires_at < datetime.now(timezone.utc):
            auth.status = "expired"
            await self.db.flush()
            raise DeviceAuthorizationExpiredError("Device authorization has expired")

        if approve:
            auth.status = "authorized"
            auth.user_id = user.id
            auth.authorized_at = datetime.now(timezone.utc)
            logger.info(f"User {user.id} authorized device {auth.device_name}")
        else:
            auth.status = "denied"
            logger.info(f"User {user.id} denied device {auth.device_name}")

        await self.db.flush()

    async def poll_device_authorization(self, device_code: str) -> tuple[DeviceToken, str]:
        """Poll for device authorization status.

        Args:
            device_code: The device code from initiation.

        Returns:
            A tuple of (DeviceToken, raw_token) if authorized.

        Raises:
            SessionNotFoundError: If the authorization is not found.
            DeviceAuthorizationPendingError: If authorization is still pending.
            DeviceAuthorizationDeniedError: If authorization was denied.
            DeviceAuthorizationExpiredError: If authorization has expired.
        """
        stmt = select(DeviceAuthorization).where(DeviceAuthorization.device_code == device_code)
        result = await self.db.execute(stmt)
        auth = result.scalar_one_or_none()

        if not auth:
            raise SessionNotFoundError("Device authorization not found")

        if auth.expires_at < datetime.now(timezone.utc):
            auth.status = "expired"
            await self.db.flush()
            raise DeviceAuthorizationExpiredError("Device authorization has expired")

        if auth.status == "pending":
            raise DeviceAuthorizationPendingError("Authorization pending")

        if auth.status == "denied":
            raise DeviceAuthorizationDeniedError("Authorization was denied")

        if auth.status == "authorized" and auth.user_id:
            # Create device token
            raw_token = generate_session_token()
            device_token = DeviceToken(
                user_id=auth.user_id,
                token_hash=hash_token(raw_token),
                device_name=auth.device_name,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.device_token_duration_days),
            )
            self.db.add(device_token)

            # Mark authorization as consumed
            auth.status = "consumed"
            await self.db.flush()

            logger.info(f"Created device token for user {auth.user_id}")
            return device_token, raw_token

        raise DeviceAuthorizationExpiredError("Invalid authorization state")
