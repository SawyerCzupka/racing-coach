"""Session registry for tracking active session state.

Provides a centralized, thread-safe way for handlers to access the current session
without coupling them to the TelemetryCollector.
"""

import logging
import threading
from uuid import UUID

from ..schemas.telemetry import SessionFrame

logger = logging.getLogger(__name__)


class SessionRegistry:
    """Thread-safe registry for tracking the current active session.

    Handlers inject this registry and query it when they need session information.
    The TelemetryCollector updates it when sessions start/end.
    """

    def __init__(self) -> None:
        # self._current_session_id: UUID | None = None
        self._current_session: SessionFrame | None = None
        self._sessions: dict[UUID, SessionFrame] = {}
        self._lock = threading.RLock()

    def start_session(self, session: SessionFrame) -> None:
        """Register a new session as active."""
        with self._lock:
            if self._current_session is not None:
                logger.warning(
                    f"Starting new session {session.session_id} while "
                    f"session {self._current_session.session_id} is still active"
                )
            self._current_session = session
            self._sessions[session.session_id] = session
            logger.info(f"Session started: {session.session_id}")

    def end_session(self, session_id: UUID) -> None:
        """Mark a session as ended."""
        with self._lock:
            if self._current_session is None:
                logger.warning(f"Attempted to end session {session_id} but no session is active")
                return
            if self._current_session.session_id != session_id:
                logger.warning(
                    f"Attempted to end session {session_id} but active session is "
                    f"{self._current_session.session_id}"
                )
                return
            logger.info(f"Session ended: {session_id}")
            self._current_session = None

    def get_current_session(self) -> SessionFrame | None:
        """Get the current active session, or None if no session is active."""
        with self._lock:
            return self._current_session

    def get_session(self, session_id: UUID) -> SessionFrame | None:
        return self._sessions.get(session_id, None)

    @property
    def has_active_session(self) -> bool:
        """Check if there is an active session."""
        with self._lock:
            return self._current_session is not None
