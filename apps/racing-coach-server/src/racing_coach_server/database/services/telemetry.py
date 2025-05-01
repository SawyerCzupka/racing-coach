from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)
from sqlalchemy.orm import Session as SQLAlchemySession

from ..models import Lap, Telemetry, TrackSession
from ..repositories import LapRepository, SessionRepository, TelemetryRepository


class TelemetryService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.telemetry_repository = TelemetryRepository(db_session)
