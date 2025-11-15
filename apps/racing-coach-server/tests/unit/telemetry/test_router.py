"""Unit tests for telemetry router endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from racing_coach_server.app import app
from racing_coach_server.telemetry.models import Lap, TrackSession


@pytest.mark.unit
class TestTelemetryRouter:
    """Unit tests for telemetry API endpoints."""

    async def test_upload_lap_success(
        self,
        telemetry_frame_factory,
        session_frame_factory,
    ):
        """Test successful lap upload."""
        # Arrange
        frames = [telemetry_frame_factory.build(lap_number=1) for _ in range(100)]
        lap_telemetry = type("LapTelemetry", (), {"frames": frames})()
        session_frame = session_frame_factory.build()

        mock_track_session = TrackSession(
            id=session_frame.session_id,
            track_id=session_frame.track_id,
            track_name=session_frame.track_name,
            track_config_name=session_frame.track_config_name,
            track_type=session_frame.track_type,
            car_id=session_frame.car_id,
            car_name=session_frame.car_name,
            car_class_id=session_frame.car_class_id,
            series_id=session_frame.series_id,
        )

        lap_id = uuid4()
        mock_lap = Lap(
            id=lap_id,
            track_session_id=session_frame.session_id,
            lap_number=1,
            lap_time=None,
            is_valid=False,
        )

        with patch(
            "racing_coach_server.telemetry.router.get_telemetry_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.db = AsyncMock()
            mock_service.add_or_get_session.return_value = mock_track_session
            mock_service.add_lap.return_value = mock_lap
            mock_service.add_telemetry_sequence.return_value = None
            mock_get_service.return_value = mock_service

            async with AsyncClient(base_url="http://test", app=app) as client:
                # Act
                response = await client.post(
                    "/api/v1/telemetry/lap",
                    json={
                        "lap": {
                            "frames": [
                                {
                                    **frame.model_dump(),
                                    "timestamp": frame.timestamp.isoformat(),
                                }
                                for frame in frames
                            ],
                            "lap_time": 90.5,
                        },
                        "session": {
                            **session_frame.model_dump(),
                            "timestamp": session_frame.timestamp.isoformat(),
                            "session_id": str(session_frame.session_id),
                        },
                    },
                )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["lap_id"] == str(lap_id)
            mock_service.add_or_get_session.assert_called_once()
            mock_service.add_lap.assert_called_once()
            mock_service.add_telemetry_sequence.assert_called_once()

    async def test_get_latest_session_success(
        self,
        track_session_factory,
    ):
        """Test retrieving the latest session."""
        # Arrange
        mock_session = track_session_factory.build()

        with patch(
            "racing_coach_server.telemetry.router.get_telemetry_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_latest_session.return_value = mock_session
            mock_get_service.return_value = mock_service

            async with AsyncClient(base_url="http://test", app=app) as client:
                # Act
                response = await client.get("/api/v1/telemetry/sessions/latest")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["track_id"] == mock_session.track_id
            assert data["track_name"] == mock_session.track_name
            assert data["car_id"] == mock_session.car_id

    async def test_get_latest_session_not_found(self):
        """Test retrieving latest session when none exists."""
        # Arrange
        with patch(
            "racing_coach_server.telemetry.router.get_telemetry_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_latest_session.return_value = None
            mock_get_service.return_value = mock_service

            async with AsyncClient(base_url="http://test", app=app) as client:
                # Act
                response = await client.get("/api/v1/telemetry/sessions/latest")

            # Assert
            assert response.status_code == 404
            assert "No sessions found" in response.json()["detail"]
