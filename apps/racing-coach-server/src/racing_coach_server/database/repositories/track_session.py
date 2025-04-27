import logging
import uuid

from racing_coach_core.models.telemetry import SessionFrame
from sqlalchemy import desc, func, select

from ..models import TrackSession
from .base import BaseRepository

logger = logging.getLogger(__name__)


class SessionRepository(BaseRepository):
    """Repository for managing session data."""

    def create_from_session_frame(self, session_frame: SessionFrame) -> TrackSession:
        """Create a new session from a SessionFrame."""
        track_session = TrackSession(
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

        self.db_session.add(track_session)
        self.db_session.commit()

        return track_session

    def get_by_id(self, session_id: uuid.UUID) -> TrackSession | None:
        """Get a session by its ID."""
        stmt = select(TrackSession).where(TrackSession.id == session_id)

        result = self.db_session.execute(stmt).scalars().first()
        return result

    def get_latest_session(self) -> TrackSession | None:
        """Get the most recent session."""
        stmt = select(TrackSession).order_by(desc(TrackSession.created_at)).limit(1)

        result = self.db_session.execute(stmt).scalars().first()
        return result
