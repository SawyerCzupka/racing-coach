from .client import (
    RacingCoachClientError,
    RacingCoachServerSDK,
    RequestError,
    ServerError,
)
from .models import (
    HealthCheckResponse,
    LapTelemetry,
    LapUploadResponse,
    SessionFrame,
    TelemetryFrame,
)


def hello() -> str:
    return "Hello from racing-coach-core!"


__all__ = [
    "RacingCoachServerSDK",
    "RacingCoachClientError",
    "ServerError",
    "RequestError",
    "LapTelemetry",
    "SessionFrame",
    "TelemetryFrame",
    "HealthCheckResponse",
    "LapUploadResponse",
    "hello",
]
