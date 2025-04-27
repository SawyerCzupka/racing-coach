from fastapi import Depends
from sqlalchemy.orm import Session

from racing_coach_server.database import get_db_session
from racing_coach_server.database.services import TelemetryService, TrackSessionService


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
