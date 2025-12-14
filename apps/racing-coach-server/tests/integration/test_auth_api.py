"""Integration tests for auth API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAuthRegistration:
    """Integration tests for registration endpoints."""

    async def test_register_creates_user(self, test_client: AsyncClient) -> None:
        """Test that registration creates a user and returns session cookie."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "display_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["display_name"] == "New User"
        assert "user_id" in data
        assert "session_token" in response.cookies

    async def test_register_duplicate_email_fails(self, test_client: AsyncClient) -> None:
        """Test that registration with duplicate email returns 409."""
        # First registration
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
            },
        )

        # Second registration with same email
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "differentpassword",
            },
        )

        assert response.status_code == 409

    async def test_register_short_password_fails(self, test_client: AsyncClient) -> None:
        """Test that registration with short password fails validation."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid@example.com",
                "password": "short",  # Less than 8 characters
            },
        )

        assert response.status_code == 422

    async def test_register_invalid_email_fails(self, test_client: AsyncClient) -> None:
        """Test that registration with invalid email fails validation."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestAuthLogin:
    """Integration tests for login endpoints."""

    async def test_login_returns_session(self, test_client: AsyncClient) -> None:
        """Test that login with valid credentials returns session cookie."""
        # First register
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "password123",
            },
        )

        # Clear cookies
        test_client.cookies.clear()

        # Then login
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "logintest@example.com"
        assert "session_token" in response.cookies

    async def test_login_wrong_password_fails(self, test_client: AsyncClient) -> None:
        """Test that login with wrong password returns 401."""
        # First register
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "password123",
            },
        )

        # Clear cookies
        test_client.cookies.clear()

        # Try login with wrong password
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpw@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    async def test_login_nonexistent_user_fails(self, test_client: AsyncClient) -> None:
        """Test that login with nonexistent user returns 401."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthMe:
    """Integration tests for user profile endpoints."""

    async def test_get_me_authenticated(self, test_client: AsyncClient) -> None:
        """Test that authenticated user can get their profile."""
        # Register (auto-login)
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "metest@example.com",
                "password": "password123",
                "display_name": "Me Test",
            },
        )

        # Get profile
        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "metest@example.com"
        assert data["display_name"] == "Me Test"
        assert data["email_verified"] is False

    async def test_get_me_unauthenticated(self, test_client: AsyncClient) -> None:
        """Test that unauthenticated request to /me returns 401."""
        test_client.cookies.clear()

        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthSessions:
    """Integration tests for session management endpoints."""

    async def test_list_sessions(self, test_client: AsyncClient) -> None:
        """Test that user can list their sessions."""
        # Register (creates first session)
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "sessionstest@example.com",
                "password": "password123",
            },
        )

        # List sessions
        response = await test_client.get("/api/v1/auth/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1
        assert data["sessions"][0]["is_current"] is True

    async def test_logout_clears_session(self, test_client: AsyncClient) -> None:
        """Test that logout clears the session cookie."""
        # Register
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logouttest@example.com",
                "password": "password123",
            },
        )

        # Logout
        response = await test_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        # Cookie should be cleared (set to empty or deleted)
        # After logout, /me should fail
        test_client.cookies.clear()
        me_response = await test_client.get("/api/v1/auth/me")
        assert me_response.status_code == 401


@pytest.mark.integration
class TestDeviceAuthorization:
    """Integration tests for device authorization flow."""

    async def test_initiate_device_authorization(self, test_client: AsyncClient) -> None:
        """Test that device authorization can be initiated."""
        response = await test_client.post(
            "/api/v1/auth/device/authorize",
            json={"device_name": "Test Desktop Client"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "device_code" in data
        assert "user_code" in data
        assert len(data["user_code"]) == 8
        assert "verification_uri" in data
        assert "expires_in" in data
        assert "interval" in data

    async def test_poll_pending_returns_error(self, test_client: AsyncClient) -> None:
        """Test that polling before authorization returns pending error."""
        # Initiate device auth
        init_response = await test_client.post(
            "/api/v1/auth/device/authorize",
            json={"device_name": "Test Device"},
        )
        device_code = init_response.json()["device_code"]

        # Poll (should be pending)
        response = await test_client.post(
            "/api/v1/auth/device/token",
            json={"device_code": device_code},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "authorization_pending"

    async def test_full_device_flow(self, test_client: AsyncClient) -> None:
        """Test complete device authorization flow."""
        # 1. Register and login a user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "deviceflow@example.com",
                "password": "password123",
            },
        )

        # 2. Initiate device authorization
        init_response = await test_client.post(
            "/api/v1/auth/device/authorize",
            json={"device_name": "Racing Coach Desktop"},
        )
        data = init_response.json()
        device_code = data["device_code"]
        user_code = data["user_code"]

        # 3. User confirms device (authenticated)
        confirm_response = await test_client.post(
            "/api/v1/auth/device/confirm",
            json={"user_code": user_code, "approve": True},
        )
        assert confirm_response.status_code == 200

        # 4. Poll for token (should succeed)
        poll_response = await test_client.post(
            "/api/v1/auth/device/token",
            json={"device_code": device_code},
        )
        assert poll_response.status_code == 200
        token_data = poll_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"
        assert token_data["device_name"] == "Racing Coach Desktop"

        # 5. Use device token to access /me
        test_client.cookies.clear()
        me_response = await test_client.get(
            "/api/v1/auth/me",
            headers={"X-Device-Token": token_data["access_token"]},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "deviceflow@example.com"

    async def test_deny_device(self, test_client: AsyncClient) -> None:
        """Test denying a device authorization."""
        # Register user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "denydevice@example.com",
                "password": "password123",
            },
        )

        # Initiate device auth
        init_response = await test_client.post(
            "/api/v1/auth/device/authorize",
            json={"device_name": "Untrusted Device"},
        )
        data = init_response.json()
        device_code = data["device_code"]
        user_code = data["user_code"]

        # Deny device
        confirm_response = await test_client.post(
            "/api/v1/auth/device/confirm",
            json={"user_code": user_code, "approve": False},
        )
        assert confirm_response.status_code == 200

        # Poll should return denied error
        poll_response = await test_client.post(
            "/api/v1/auth/device/token",
            json={"device_code": device_code},
        )
        assert poll_response.status_code == 400
        assert poll_response.json()["detail"]["error"] == "access_denied"


@pytest.mark.integration
class TestDeviceManagement:
    """Integration tests for device token management."""

    async def test_list_devices(self, test_client: AsyncClient) -> None:
        """Test listing device tokens."""
        # Register user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "listdevices@example.com",
                "password": "password123",
            },
        )

        # List devices (should be empty initially)
        response = await test_client.get("/api/v1/auth/devices")

        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert data["total"] == 0

    async def test_revoke_device(self, test_client: AsyncClient) -> None:
        """Test revoking a device token."""
        # Register user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "revokedevice@example.com",
                "password": "password123",
            },
        )

        # Create a device token via device flow
        init_response = await test_client.post(
            "/api/v1/auth/device/authorize",
            json={"device_name": "Device To Revoke"},
        )
        data = init_response.json()
        device_code = data["device_code"]
        user_code = data["user_code"]

        # Confirm device
        await test_client.post(
            "/api/v1/auth/device/confirm",
            json={"user_code": user_code, "approve": True},
        )

        # Get token
        poll_response = await test_client.post(
            "/api/v1/auth/device/token",
            json={"device_code": device_code},
        )
        device_token = poll_response.json()["access_token"]

        # List devices to get token ID
        devices_response = await test_client.get("/api/v1/auth/devices")
        token_id = devices_response.json()["devices"][0]["token_id"]

        # Revoke device
        revoke_response = await test_client.delete(f"/api/v1/auth/devices/{token_id}")
        assert revoke_response.status_code == 200

        # Token should no longer work
        test_client.cookies.clear()
        me_response = await test_client.get(
            "/api/v1/auth/me",
            headers={"X-Device-Token": device_token},
        )
        assert me_response.status_code == 401
