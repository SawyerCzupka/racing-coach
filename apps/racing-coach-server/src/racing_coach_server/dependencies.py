"""Dependency injection functions for FastAPI route handlers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.auth.router import (
    AuthServiceDep,
    CurrentUser,
    OptionalUser,
    get_auth_service,
    get_current_user,
    get_current_user_optional,
)
from racing_coach_server.auth.service import AuthService
from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService
from racing_coach_server.telemetry.services import (
    LapService,
    MetricsService,
    SessionService,
    TelemetryDataService,
)


# Legacy service - kept for backward compatibility
async def get_telemetry_service(
    db: AsyncSession = Depends(get_async_session),
) -> TelemetryService:
    """Provide TelemetryService with injected AsyncSession."""
    return TelemetryService(db)


TelemetryServiceDep = Annotated[TelemetryService, Depends(get_telemetry_service)]


# New focused services
async def get_session_service(
    db: AsyncSession = Depends(get_async_session),
) -> SessionService:
    """Provide SessionService with injected AsyncSession."""
    return SessionService(db)


async def get_lap_service(
    db: AsyncSession = Depends(get_async_session),
) -> LapService:
    """Provide LapService with injected AsyncSession."""
    return LapService(db)


async def get_metrics_service(
    db: AsyncSession = Depends(get_async_session),
) -> MetricsService:
    """Provide MetricsService with injected AsyncSession."""
    return MetricsService(db)


async def get_telemetry_data_service(
    db: AsyncSession = Depends(get_async_session),
) -> TelemetryDataService:
    """Provide TelemetryDataService with injected AsyncSession."""
    return TelemetryDataService(db)


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
LapServiceDep = Annotated[LapService, Depends(get_lap_service)]
MetricsServiceDep = Annotated[MetricsService, Depends(get_metrics_service)]
TelemetryDataServiceDep = Annotated[TelemetryDataService, Depends(get_telemetry_data_service)]

# Auth dependencies re-exported for convenience
__all__ = [
    # Telemetry
    "get_telemetry_service",
    "TelemetryServiceDep",
    "get_session_service",
    "SessionServiceDep",
    "get_lap_service",
    "LapServiceDep",
    "get_metrics_service",
    "MetricsServiceDep",
    "get_telemetry_data_service",
    "TelemetryDataServiceDep",
    # Auth
    "get_auth_service",
    "AuthService",
    "AuthServiceDep",
    "get_current_user",
    "get_current_user_optional",
    "CurrentUser",
    "OptionalUser",
]
