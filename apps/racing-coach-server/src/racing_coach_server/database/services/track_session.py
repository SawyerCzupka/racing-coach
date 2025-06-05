from racing_coach_core.models.telemetry import SessionFrame
from sqlalchemy.orm import Session as SQLAlchemySession

from ..models import TrackSession
from ..repositories.track_session import SessionRepository


class TrackSessionService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.repository = SessionRepository(db_session)

    def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        """Add a new session or get an existing one."""
        track_session = self.repository.get_by_id(session_frame.session_id)

        # If the session does not exist, create a new one
        if not track_session:
            track_session = self.repository.create_from_session_frame(session_frame)
            self.db_session.commit()
            self.db_session.refresh(track_session)

        return track_session

    def get_latest_session(self) -> TrackSession | None:
        """Get the most recent session."""
        return self.repository.get_latest_session()