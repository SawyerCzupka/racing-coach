"""Unit tests for SessionService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from racing_coach_core.schemas.telemetry import SessionFrame
from racing_coach_server.sessions.service import SessionService
from racing_coach_server.telemetry.models import Lap, TrackSession

from tests.polyfactories import SessionFrameFactory, TrackSessionFactory


@pytest.mark.unit
class TestSessionService:
    """Unit tests for SessionService methods."""

    async def test_add_or_get_session_creates_new(
        self,
        mock_db_session: AsyncMock,
        session_frame_factory: SessionFrameFactory,
    ):
        """Test that add_or_get_session creates a new session when none exists."""
        # Arrange
        session_frame: SessionFrame = session_frame_factory.build()
        service = SessionService(mock_db_session)

        # Mock the query to return None (no existing session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
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
        mock_db_session: AsyncMock,
        session_frame_factory: SessionFrameFactory,
        track_session_factory: TrackSessionFactory,
    ):
        """Test that add_or_get_session returns existing session when found."""
        # Arrange
        session_frame: SessionFrame = session_frame_factory.build()
        existing_session = track_session_factory.build(id=session_frame.session_id)
        service = SessionService(mock_db_session)

        # Mock the query to return the existing session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_session
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.add_or_get_session(session_frame)

        # Assert
        assert result == existing_session
        mock_db_session.add.assert_not_called()
        mock_db_session.flush.assert_not_called()

    async def test_get_latest_session_returns_session(
        self,
        mock_db_session: AsyncMock,
        track_session_factory: TrackSessionFactory,
    ):
        """Test that get_latest_session returns the latest session."""
        # Arrange
        latest_session = track_session_factory.build()
        service = SessionService(mock_db_session)

        # Mock the query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = latest_session
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.get_latest_session()

        # Assert
        assert result == latest_session
        mock_db_session.execute.assert_called_once()

    async def test_get_latest_session_returns_none_when_empty(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test that get_latest_session returns None when no sessions exist."""
        # Arrange
        service = SessionService(mock_db_session)

        # Mock the query to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
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
        mock_db_session: AsyncMock,
        lap_number: int,
        lap_time: float | None,
        is_valid: bool,
    ):
        """Test that add_lap creates a lap with correct parameters."""
        # Arrange
        session_id = uuid4()
        service = SessionService(mock_db_session)

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
