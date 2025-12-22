"""Feature-specific exceptions for the metrics domain."""

from racing_coach_server.exceptions import NotFoundError, RacingCoachException


class MetricsException(RacingCoachException):
    """Base exception for metrics domain errors."""


class MetricsNotFoundError(NotFoundError, MetricsException):
    """Raised when metrics cannot be found."""

    def __init__(self, lap_id: str | None = None) -> None:
        message = f"Metrics not found for lap {lap_id}" if lap_id else "Metrics not found"
        super().__init__(message)
