"""Unit tests for AuthService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from racing_coach_server.auth.exceptions import (
    DeviceAuthorizationDeniedError,
    DeviceAuthorizationExpiredError,
    DeviceAuthorizationPendingError,
    InvalidCredentialsError,
    SessionNotFoundError,
    UserAlreadyExistsError,
)
from racing_coach_server.auth.models import DeviceAuthorization, DeviceToken, User, UserSession
from racing_coach_server.auth.service import AuthService
from racing_coach_server.auth.utils import hash_password, hash_token

from tests.polyfactories import DeviceAuthorizationFactory, UserFactory, UserSessionFactory


@pytest.mark.unit
class TestAuthServiceUserManagement:
    """Unit tests for user management in AuthService."""

    async def test_register_user_creates_user(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that register_user creates a new user."""
        # Arrange
        service = AuthService(mock_db_session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        user = await service.register_user(
            email="test@example.com",
            password="password123",
            display_name="Test User",
        )

        # Assert
        assert isinstance(user, User)
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.password_hash != "password123"  # Should be hashed
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    async def test_register_user_lowercases_email(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that register_user lowercases the email."""
        # Arrange
        service = AuthService(mock_db_session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        user = await service.register_user(
            email="Test@EXAMPLE.com",
            password="password123",
        )

        # Assert
        assert user.email == "test@example.com"

    async def test_register_user_raises_if_exists(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
    ) -> None:
        """Test that register_user raises UserAlreadyExistsError if user exists."""
        # Arrange
        service = AuthService(mock_db_session)
        existing_user = user_factory.build()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: existing_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await service.register_user(
                email="test@example.com",
                password="password123",
            )

    async def test_authenticate_user_returns_user(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
    ) -> None:
        """Test that authenticate_user returns user for valid credentials."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build(
            email="test@example.com",
            password_hash=hash_password("password123"),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.authenticate_user("test@example.com", "password123")

        # Assert
        assert result == user

    async def test_authenticate_user_raises_for_wrong_password(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
    ) -> None:
        """Test that authenticate_user raises InvalidCredentialsError for wrong password."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build(
            email="test@example.com",
            password_hash=hash_password("password123"),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user("test@example.com", "wrongpassword")

    async def test_authenticate_user_raises_for_nonexistent_user(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that authenticate_user raises InvalidCredentialsError for nonexistent user."""
        # Arrange
        service = AuthService(mock_db_session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user("nonexistent@example.com", "password123")

    async def test_authenticate_user_raises_for_inactive_user(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
    ) -> None:
        """Test that authenticate_user raises InvalidCredentialsError for inactive user."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build(
            email="test@example.com",
            password_hash=hash_password("password123"),
            is_active=False,
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user("test@example.com", "password123")


@pytest.mark.unit
class TestAuthServiceSessionManagement:
    """Unit tests for session management in AuthService."""

    async def test_create_session_returns_session_and_token(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
    ) -> None:
        """Test that create_session returns a session and raw token."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build()

        # Act
        session, token = await service.create_session(
            user=user,
            user_agent="Test Browser",
            ip_address="127.0.0.1",
        )

        # Assert
        assert isinstance(session, UserSession)
        assert session.user_id == user.id
        assert session.user_agent == "Test Browser"
        assert session.ip_address == "127.0.0.1"
        assert isinstance(token, str)
        assert len(token) > 0
        # Verify token hash is different from raw token
        assert session.token_hash != token
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    async def test_validate_session_returns_user(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
        user_session_factory: UserSessionFactory,
    ) -> None:
        """Test that validate_session returns user for valid session."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build()
        raw_token = "test_token"
        session = user_session_factory.build(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=None,
        )

        # First call returns session, second call returns user
        mock_result_session = AsyncMock()
        mock_result_session.scalar_one_or_none = lambda: session
        mock_result_user = AsyncMock()
        mock_result_user.scalar_one_or_none = lambda: user
        mock_db_session.execute = AsyncMock(side_effect=[mock_result_session, mock_result_user])

        # Act
        result = await service.validate_session(raw_token)

        # Assert
        assert result == user

    async def test_validate_session_returns_none_for_expired(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that validate_session returns None for expired session."""
        # Arrange
        service = AuthService(mock_db_session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None  # Query excludes expired
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.validate_session("some_token")

        # Assert
        assert result is None

    async def test_revoke_session_sets_revoked_at(
        self,
        mock_db_session: AsyncMock,
        user_session_factory: UserSessionFactory,
    ) -> None:
        """Test that revoke_session sets revoked_at timestamp."""
        # Arrange
        service = AuthService(mock_db_session)
        user_id = uuid4()
        session = user_session_factory.build(user_id=user_id)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: session
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        await service.revoke_session(session.id, user_id)

        # Assert
        assert session.revoked_at is not None
        mock_db_session.flush.assert_called_once()

    async def test_revoke_session_raises_for_not_found(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that revoke_session raises SessionNotFoundError if not found."""
        # Arrange
        service = AuthService(mock_db_session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(SessionNotFoundError):
            await service.revoke_session(uuid4(), uuid4())


@pytest.mark.unit
class TestAuthServiceDeviceAuthorization:
    """Unit tests for device authorization in AuthService."""

    async def test_initiate_device_authorization_creates_auth(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that initiate_device_authorization creates authorization."""
        # Arrange
        service = AuthService(mock_db_session)

        # Act
        auth = await service.initiate_device_authorization("Test Device")

        # Assert
        assert isinstance(auth, DeviceAuthorization)
        assert auth.device_name == "Test Device"
        assert auth.status == "pending"
        assert len(auth.device_code) > 0
        assert len(auth.user_code) == 8
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    async def test_authorize_device_sets_authorized(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that authorize_device sets status to authorized."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build()
        auth = device_authorization_factory.build(
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        await service.authorize_device(auth.user_code, user, approve=True)

        # Assert
        assert auth.status == "authorized"
        assert auth.user_id == user.id
        assert auth.authorized_at is not None

    async def test_authorize_device_sets_denied(
        self,
        mock_db_session: AsyncMock,
        user_factory: UserFactory,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that authorize_device sets status to denied when not approved."""
        # Arrange
        service = AuthService(mock_db_session)
        user = user_factory.build()
        auth = device_authorization_factory.build(
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        await service.authorize_device(auth.user_code, user, approve=False)

        # Assert
        assert auth.status == "denied"

    async def test_poll_device_authorization_pending(
        self,
        mock_db_session: AsyncMock,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that poll raises DeviceAuthorizationPendingError when pending."""
        # Arrange
        service = AuthService(mock_db_session)
        auth = device_authorization_factory.build(
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(DeviceAuthorizationPendingError):
            await service.poll_device_authorization(auth.device_code)

    async def test_poll_device_authorization_denied(
        self,
        mock_db_session: AsyncMock,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that poll raises DeviceAuthorizationDeniedError when denied."""
        # Arrange
        service = AuthService(mock_db_session)
        auth = device_authorization_factory.build(
            status="denied",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(DeviceAuthorizationDeniedError):
            await service.poll_device_authorization(auth.device_code)

    async def test_poll_device_authorization_expired(
        self,
        mock_db_session: AsyncMock,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that poll raises DeviceAuthorizationExpiredError when expired."""
        # Arrange
        service = AuthService(mock_db_session)
        auth = device_authorization_factory.build(
            status="pending",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(DeviceAuthorizationExpiredError):
            await service.poll_device_authorization(auth.device_code)

    async def test_poll_device_authorization_returns_token(
        self,
        mock_db_session: AsyncMock,
        device_authorization_factory: DeviceAuthorizationFactory,
    ) -> None:
        """Test that poll returns device token when authorized."""
        # Arrange
        service = AuthService(mock_db_session)
        user_id = uuid4()
        auth = device_authorization_factory.build(
            status="authorized",
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: auth
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        device_token, raw_token = await service.poll_device_authorization(auth.device_code)

        # Assert
        assert isinstance(device_token, DeviceToken)
        assert device_token.user_id == user_id
        assert isinstance(raw_token, str)
        assert len(raw_token) > 0
        assert auth.status == "consumed"
