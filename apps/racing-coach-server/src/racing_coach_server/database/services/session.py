from sqlalchemy.orm import Session as SQLAlchemySession
from racing_coach_core.models.telemetry import SessionFrame
from ..repositories.session import SessionRepository
from ..models import TrackSession


class SessionService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.repository = SessionRepository(db_session)

    def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        """Add a new session or get an existing one."""
        session = self.repository.get_by_id(session_frame.session_id)

        # If the session does not exist, create a new one
        if not session:
            session = self.repository.create_from_session_frame(session_frame)

        return session
