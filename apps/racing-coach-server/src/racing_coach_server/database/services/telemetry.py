from sqlalchemy.orm import Session as SQLAlchemySession
from racing_coach_core.models.telemetry import (
    SessionFrame,
    TelemetryFrame,
    LapTelemetry,
)
from ..repositories import SessionRepository, TelemetryRepository, LapRepository
from ..models import TrackSession, Telemetry, Lap


class TelemetryService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.telemetry_repository = TelemetryRepository(db_session)
