"""Feature-specific exceptions for the telemetry domain."""

from racing_coach_server.exceptions import RacingCoachException, ValidationError


class TelemetryException(RacingCoachException):
    """Base exception for telemetry domain errors."""


class InvalidTelemetryDataError(ValidationError, TelemetryException):
    """Raised when telemetry data is invalid."""

    def __init__(self, message: str = "Invalid telemetry data") -> None:
        super().__init__(message)
