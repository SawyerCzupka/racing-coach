"""Feature-specific exceptions for the telemetry domain."""

from racing_coach_server.exceptions import RacingCoachException


class TelemetryException(RacingCoachException):
    """Base exception for telemetry domain errors."""


class SessionNotFoundError(TelemetryException):
    """Raised when a session cannot be found."""


class InvalidLapDataError(TelemetryException):
    """Raised when lap data is invalid."""


class LapNotFoundError(TelemetryException):
    """Raised when a lap cannot be found."""
