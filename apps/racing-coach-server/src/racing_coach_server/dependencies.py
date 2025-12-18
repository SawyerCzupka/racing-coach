"""Dependency injection functions for FastAPI route handlers."""

from typing import Annotated

from fastapi import Depends

from racing_coach_server.auth.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    OptionalUserDep,
    get_auth_service,
    get_current_user,
    get_current_user_optional,
)
from racing_coach_server.auth.service import AuthService
from racing_coach_server.database.dependencies import AsyncSessionDep
from racing_coach_server.metrics.service import MetricsService
from racing_coach_server.sessions.service import SessionService
from racing_coach_server.telemetry.service import TelemetryService


# Session service (sessions + laps)
async def get_session_service(
    db: AsyncSessionDep,
) -> SessionService:
    """Provide SessionService with injected AsyncSession."""
    return SessionService(db)


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


# Metrics service
async def get_metrics_service(
    db: AsyncSessionDep,
) -> MetricsService:
    """Provide MetricsService with injected AsyncSession."""
    return MetricsService(db)


MetricsServiceDep = Annotated[MetricsService, Depends(get_metrics_service)]


# Telemetry service (telemetry data/frames)
async def get_telemetry_service(
    db: AsyncSessionDep,
) -> TelemetryService:
    """Provide TelemetryService with injected AsyncSession."""
    return TelemetryService(db)


TelemetryServiceDep = Annotated[TelemetryService, Depends(get_telemetry_service)]


# Re-exported for convenience
__all__ = [
    # Database
    "AsyncSessionDep",
    # Sessions
    "get_session_service",
    "SessionServiceDep",
    # Metrics
    "get_metrics_service",
    "MetricsServiceDep",
    # Telemetry
    "get_telemetry_service",
    "TelemetryServiceDep",
    # Auth
    "get_auth_service",
    "AuthService",
    "AuthServiceDep",
    "get_current_user",
    "get_current_user_optional",
    "CurrentUserDep",
    "OptionalUserDep",
]
