"""Dependency injection functions for FastAPI route handlers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService


async def get_telemetry_service(
    db: AsyncSession = Depends(get_async_session),
) -> TelemetryService:
    """Provide TelemetryService with injected AsyncSession."""
    return TelemetryService(db)


TelemetryServiceDep = Annotated[TelemetryService, Depends(get_telemetry_service)]
