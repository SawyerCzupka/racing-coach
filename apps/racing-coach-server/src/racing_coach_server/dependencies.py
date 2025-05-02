from fastapi import Depends
from sqlalchemy.orm import Session

from racing_coach_server.database import get_db_session
from racing_coach_server.database.services import (
    TelemetryService,
    TrackSessionService,
    LapService,
)
from typing import Annotated


def get_track_session_service(
    db: Session = Depends(get_db_session),
) -> TrackSessionService:
    """Dependency to get an instance of TrackSessionService."""
    return TrackSessionService(db_session=db)


def get_telemetry_service(
    db: Session = Depends(get_db_session),
) -> TelemetryService:
    """Dependency to get an instance of TelemetryService."""
    return TelemetryService(db_session=db)


def get_lap_service(
    db: Session = Depends(get_db_session),
) -> LapService:
    """Dependency to get an instance of LapService."""
    return LapService(db_session=db)


TrackSessionServiceDep = Annotated[
    TrackSessionService, Depends(get_track_session_service)
]
TelemetryServiceDep = Annotated[TelemetryService, Depends(get_telemetry_service)]
LapServiceDep = Annotated[LapService, Depends(get_lap_service)]
