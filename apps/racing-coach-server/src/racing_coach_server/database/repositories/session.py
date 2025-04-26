import logging
import uuid

from racing_coach_core.models.telemetry import SessionFrame
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session as SQLAlchemySession

from ..models import Session
from .base import BaseRepository

logger = logging.getLogger(__name__)


class SessionRepository(BaseRepository):
    """Repository for managing session data."""

    def __init__(self, db_session: SQLAlchemySession):
        super().__init__(db_session)

    def create_from_session_frame(self, session_frame: SessionFrame) -> Session:
        """Create a new session from a SessionFrame."""
        session = Session(
            track_id=session_frame.track_id,
            track_name=session_frame.track_name,
            track_config_name=session_frame.track_config_name,
            track_type=session_frame.track_type,
            car_id=session_frame.car_id,
            car_name=session_frame.car_name,
            car_class_id=session_frame.car_class_id,
            series_id=session_frame.series_id,
        )

        self.db_session.add(session)
        self.db_session.commit()

        return session

    def get_by_id(self, session_id: uuid.UUID) -> Session | None:
        """Get a session by its ID."""
        return self.db_session.query(Session).filter(Session.id == session_id).first()

    def get_latest_session(self) -> Session | None:
        """Get the most recent session."""
        return self.db_session.query(Session).order_by(desc(Session.created_at)).first()
