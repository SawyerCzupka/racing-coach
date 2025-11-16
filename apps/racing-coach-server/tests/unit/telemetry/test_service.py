"""Unit tests for TelemetryService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame
from racing_coach_server.telemetry.models import Lap, Telemetry, TrackSession
from racing_coach_server.telemetry.service import TelemetryService
from sqlalchemy import select


@pytest.mark.unit
class TestTelemetryService:
    """Unit tests for TelemetryService methods."""

    async def test_add_or_get_session_creates_new(
        self,
        mock_db_session,
        session_frame_factory,
    ):
        """Test that add_or_get_session creates a new session when none exists."""
        # Arrange
        session_frame: SessionFrame = session_frame_factory.build()
        service = TelemetryService(mock_db_session)

        # Mock the query to return None (no existing session)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.add_or_get_session(session_frame)

        # Assert
        assert isinstance(result, TrackSession)
        assert result.id == session_frame.session_id
        assert result.track_id == session_frame.track_id
        assert result.track_name == session_frame.track_name
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    async def test_add_or_get_session_returns_existing(
        self,
        mock_db_session,
        session_frame_factory,
        track_session_factory,
    ):
        """Test that add_or_get_session returns existing session when found."""
        # Arrange
        session_frame: SessionFrame = session_frame_factory.build()
        existing_session = track_session_factory.build(id=session_frame.session_id)
        service = TelemetryService(mock_db_session)

        # Mock the query to return the existing session
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: existing_session
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.add_or_get_session(session_frame)

        # Assert
        assert result == existing_session
        mock_db_session.add.assert_not_called()
        mock_db_session.flush.assert_not_called()

    async def test_get_latest_session_returns_session(
        self,
        mock_db_session,
        track_session_factory,
    ):
        """Test that get_latest_session returns the latest session."""
        # Arrange
        latest_session = track_session_factory.build()
        service = TelemetryService(mock_db_session)

        # Mock the query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: latest_session
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.get_latest_session()

        # Assert
        assert result == latest_session
        mock_db_session.execute.assert_called_once()

    async def test_get_latest_session_returns_none_when_empty(
        self,
        mock_db_session,
    ):
        """Test that get_latest_session returns None when no sessions exist."""
        # Arrange
        service = TelemetryService(mock_db_session)

        # Mock the query to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.get_latest_session()

        # Assert
        assert result is None

    @pytest.mark.parametrize(
        "lap_number,lap_time,is_valid",
        [
            (1, 90.5, True),
            (5, None, False),
            (10, 85.3, True),
        ],
    )
    async def test_add_lap(
        self,
        mock_db_session,
        lap_number,
        lap_time,
        is_valid,
    ):
        """Test that add_lap creates a lap with correct parameters."""
        # Arrange
        session_id = uuid4()
        service = TelemetryService(mock_db_session)

        # Act
        result = await service.add_lap(
            track_session_id=session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )

        # Assert
        assert isinstance(result, Lap)
        assert result.track_session_id == session_id
        assert result.lap_number == lap_number
        assert result.lap_time == lap_time
        assert result.is_valid == is_valid
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    async def test_add_telemetry_sequence(
        self,
        mock_db_session,
        telemetry_frame_factory,
    ):
        """Test that add_telemetry_sequence creates telemetry records."""
        # Arrange
        lap_id = uuid4()
        session_id = uuid4()
        service = TelemetryService(mock_db_session)

        # Create a sequence with 10 frames
        frames = [telemetry_frame_factory.build() for _ in range(10)]

        # Create a mock LapTelemetry object
        class MockLapTelemetry:
            def __init__(self, frames):
                self.frames = frames

        telemetry_sequence = MockLapTelemetry(frames)

        # Act
        await service.add_telemetry_sequence(telemetry_sequence, lap_id, session_id)

        # Assert
        mock_db_session.add_all.assert_called_once()
        added_frames = mock_db_session.add_all.call_args[0][0]
        assert len(added_frames) == 10
        assert all(isinstance(frame, Telemetry) for frame in added_frames)
        assert all(frame.lap_id == lap_id for frame in added_frames)
        assert all(frame.track_session_id == session_id for frame in added_frames)

    async def test_add_telemetry_sequence_preserves_tire_data(
        self,
        mock_db_session,
        telemetry_frame_factory,
    ):
        """Test that add_telemetry_sequence correctly maps tire data."""
        # Arrange
        lap_id = uuid4()
        session_id = uuid4()
        service = TelemetryService(mock_db_session)

        # Create a frame with specific tire data
        frame = telemetry_frame_factory.build(
            tire_temps={
                "LF": {"left": 80.0, "middle": 85.0, "right": 82.0},
                "RF": {"left": 81.0, "middle": 86.0, "right": 83.0},
                "LR": {"left": 78.0, "middle": 83.0, "right": 80.0},
                "RR": {"left": 79.0, "middle": 84.0, "right": 81.0},
            },
            tire_wear={
                "LF": {"left": 0.95, "middle": 0.93, "right": 0.94},
                "RF": {"left": 0.94, "middle": 0.92, "right": 0.93},
                "LR": {"left": 0.96, "middle": 0.94, "right": 0.95},
                "RR": {"left": 0.95, "middle": 0.93, "right": 0.94},
            },
            brake_line_pressure={"LF": 2.5, "RF": 2.5, "LR": 2.0, "RR": 2.0},
        )

        class MockLapTelemetry:
            def __init__(self, frames):
                self.frames = frames

        telemetry_sequence = MockLapTelemetry([frame])

        # Act
        await service.add_telemetry_sequence(telemetry_sequence, lap_id, session_id)

        # Assert
        added_frames = mock_db_session.add_all.call_args[0][0]
        telemetry = added_frames[0]

        # Verify tire temperatures
        assert telemetry.lf_tire_temp_left == 80.0
        assert telemetry.lf_tire_temp_middle == 85.0
        assert telemetry.rf_tire_temp_right == 83.0

        # Verify tire wear
        assert telemetry.lf_tire_wear_left == 0.95
        assert telemetry.rf_tire_wear_middle == 0.92

        # Verify brake pressure
        assert telemetry.lf_brake_pressure == 2.5
        assert telemetry.lr_brake_pressure == 2.0
