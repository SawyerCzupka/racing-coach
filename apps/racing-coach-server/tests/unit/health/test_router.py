"""Unit tests for health check router."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from racing_coach_server.app import app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
class TestHealthRouter:
    """Unit tests for health check endpoint."""

    async def test_health_check_healthy(self) -> None:
        """Test health check returns healthy when database is accessible."""
        # Arrange
        from unittest.mock import Mock

        mock_db: AsyncMock = AsyncMock(spec=AsyncSession)
        mock_result: AsyncMock = AsyncMock()
        mock_result.scalar = Mock(return_value=1)  # scalar() is not async
        mock_db.execute.return_value = mock_result

        async def mock_session_generator() -> AsyncGenerator[AsyncMock, None]:
            yield mock_db

        # Use FastAPI dependency overrides
        from racing_coach_server.database.engine import get_async_session

        app.dependency_overrides[get_async_session] = mock_session_generator

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/health")

        # Clean up override
        app.dependency_overrides.clear()

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "healthy"
        assert data["database_status"] == "healthy"
        assert "successful" in data["database_message"].lower()

    async def test_health_check_unhealthy_database(self) -> None:
        """Test health check returns unhealthy when database fails."""
        # Arrange
        mock_db: AsyncMock = AsyncMock(spec=AsyncSession)
        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        async def mock_session_generator() -> AsyncGenerator[AsyncMock, None]:
            yield mock_db

        # Use FastAPI dependency overrides
        from racing_coach_server.database.engine import get_async_session

        app.dependency_overrides[get_async_session] = mock_session_generator

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/health")

        # Clean up override
        app.dependency_overrides.clear()

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database_status"] == "unhealthy"
        assert "failed" in data["database_message"].lower()
