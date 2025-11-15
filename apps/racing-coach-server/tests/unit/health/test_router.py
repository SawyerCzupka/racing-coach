"""Unit tests for health check router."""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import AsyncMock, patch

from racing_coach_server.app import app


@pytest.mark.unit
class TestHealthRouter:
    """Unit tests for health check endpoint."""

    async def test_health_check_healthy(self):
        """Test health check returns healthy when database is accessible."""
        # Arrange
        with patch("racing_coach_server.health.router.get_async_session") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(base_url="http://test", app=app) as client:
                # Act
                response = await client.get("/api/v1/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "healthy"
            assert "successful" in data["database_message"].lower()

    async def test_health_check_unhealthy_database(self):
        """Test health check returns unhealthy when database fails."""
        # Arrange
        with patch("racing_coach_server.health.router.get_async_session") as mock_get_db:
            mock_db = AsyncMock()
            mock_db.execute.side_effect = SQLAlchemyError("Connection failed")
            mock_get_db.return_value = mock_db

            async with AsyncClient(base_url="http://test", app=app) as client:
                # Act
                response = await client.get("/api/v1/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "unhealthy"
            assert "failed" in data["database_message"].lower()
