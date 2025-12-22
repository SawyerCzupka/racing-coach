"""Feature-specific exceptions for the sessions domain."""

from racing_coach_server.exceptions import NotFoundError, RacingCoachException


class SessionsException(RacingCoachException):
    """Base exception for sessions domain errors."""


class SessionNotFoundError(NotFoundError, SessionsException):
    """Raised when a session cannot be found."""

    def __init__(self, session_id: str | None = None) -> None:
        message = f"Session {session_id} not found" if session_id else "Session not found"
        super().__init__(message)


class LapNotFoundError(NotFoundError, SessionsException):
    """Raised when a lap cannot be found."""

    def __init__(self, lap_id: str | None = None) -> None:
        message = f"Lap {lap_id} not found" if lap_id else "Lap not found"
        super().__init__(message)
