from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)
from sqlalchemy.orm import Session as SQLAlchemySession
from uuid import UUID
from ..models import Lap, Telemetry, TrackSession
from ..repositories import LapRepository, SessionRepository, TelemetryRepository


class LapService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.lap_repository = LapRepository(db_session)
        self.track_session_repository = SessionRepository(db_session)
        self.telemetry_repository = TelemetryRepository(db_session)

    def add_lap(
        self,
        track_session_id: UUID,
        lap_number: int,
        lap_time: float | None = None,
        is_valid: bool = False,
    ) -> Lap:
        """
        Adds a new lap to the database for a specific track session.

        Args:
            track_session_id (UUID): The unique identifier of the track session.
            lap_number (int): The lap number to be added.

        Returns:
            Lap: The created Lap object.
        """
        lap = self.lap_repository.create(
            track_session_id=track_session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )
        self.db_session.commit()
        return lap
