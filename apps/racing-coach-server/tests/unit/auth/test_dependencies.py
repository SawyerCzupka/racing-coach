"""Unit tests for auth dependencies."""

import pytest
from fastapi import HTTPException
from racing_coach_server.auth.dependencies import require_admin

from tests.polyfactories import UserFactory


@pytest.mark.unit
class TestRequireAdmin:
    """Unit tests for require_admin dependency."""

    async def test_require_admin_allows_admin_user(self, user_factory: UserFactory) -> None:
        """Test that admin users are allowed through."""
        admin_user = user_factory.build(is_admin=True)

        # Should not raise, just return the user
        result = await require_admin(admin_user)
        assert result.is_admin is True

    async def test_require_admin_denies_regular_user(self, user_factory: UserFactory) -> None:
        """Test that regular users get 403 Forbidden."""
        regular_user = user_factory.build(is_admin=False)

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(regular_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"
