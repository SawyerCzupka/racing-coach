"""Unit tests for health check router."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from racing_coach_server.app import app
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.unit
class TestHealthRouter:
    """Unit tests for health check endpoint."""

    async def test_health_check_healthy(self):
        """Test health check returns healthy when database is accessible."""
        # Arrange
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_result

        async def mock_session_generator():
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
        assert data["status"] == "healthy"
        assert data["database_status"] == "healthy"
        assert "successful" in data["database_message"].lower()

    async def test_health_check_unhealthy_database(self):
        """Test health check returns unhealthy when database fails."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        async def mock_session_generator():
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
