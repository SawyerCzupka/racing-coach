from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)
from sqlalchemy.orm import Session as SQLAlchemySession

from ..models import Lap, Telemetry, TrackSession
from ..repositories import LapRepository, SessionRepository, TelemetryRepository


class LapService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.lap_repository = LapRepository(db_session)
        self.track_session_repository = SessionRepository(db_session)
        self.telemetry_repository = TelemetryRepository(db_session)

    # def process_lap_telemetry(
    #     self, lap_telemetry: LapTelemetry, session: SessionFrame
    # ) -> Lap:

    #     if not lap_telemetry.frames:
    #         raise ValueError("Lap telemetry frames are empty.")

    #     lap_number = lap_telemetry.frames[0].lap_number

    #     # Get or create the track session
