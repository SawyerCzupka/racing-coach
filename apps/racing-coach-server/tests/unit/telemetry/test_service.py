"""Unit tests for TelemetryService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from racing_coach_server.telemetry.models import Telemetry
from racing_coach_server.telemetry.service import TelemetryService

from tests.polyfactories import LapTelemetryFactory, TelemetryFrameFactory


@pytest.mark.unit
class TestTelemetryService:
    """Unit tests for TelemetryService methods."""

    async def test_add_telemetry_sequence(
        self,
        mock_db_session: AsyncMock,
        telemetry_frame_factory: TelemetryFrameFactory,
        lap_telemetry_factory: LapTelemetryFactory,
    ):
        """Test that add_telemetry_sequence creates telemetry records."""
        # Arrange
        lap_id = uuid4()
        session_id = uuid4()
        service = TelemetryService(mock_db_session)

        # Create a sequence with 10 frames
        frames = [telemetry_frame_factory.build() for _ in range(10)]
        telemetry_sequence = lap_telemetry_factory.build(frames=frames)

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
        mock_db_session: AsyncMock,
        telemetry_frame_factory: TelemetryFrameFactory,
        lap_telemetry_factory: LapTelemetryFactory,
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

        telemetry_sequence = lap_telemetry_factory.build(frames=[frame])

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
