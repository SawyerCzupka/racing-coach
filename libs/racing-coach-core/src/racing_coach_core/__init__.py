from .schemas import (
    HealthCheckResponse,
    LapTelemetry,
    LapUploadResponse,
    SessionFrame,
    TelemetryFrame,
)


def hello() -> str:
    return "Hello from racing-coach-core!"


__all__ = [
    "LapTelemetry",
    "SessionFrame",
    "TelemetryFrame",
    "HealthCheckResponse",
    "LapUploadResponse",
    "hello",
]
