from uuid import UUID

from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
    TelemetrySequence,
)
from sqlalchemy.orm import Session as SQLAlchemySession

from ..models import Lap, Telemetry, TrackSession
from ..repositories import LapRepository, SessionRepository, TelemetryRepository


class TelemetryService:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
        self.telemetry_repository = TelemetryRepository(db_session)

    def add_telemetry_sequence(
        self, telemetry_sequence: TelemetrySequence, lap_id: UUID, session_id: UUID
    ) -> None:
        """
        Adds a sequence of telemetry frames to the database for a specific lap and session.

        Iterates over each frame in the provided TelemetrySequence and creates a corresponding
        telemetry record in the database, associating each frame with the given lap and session IDs.
        Commits the transaction after all frames have been added.

        Args:
            telemetry_sequence (TelemetrySequence): The sequence of telemetry frames to add.
            lap_id (UUID): The unique identifier of the lap to associate with the telemetry frames.
            session_id (UUID): The unique identifier of the session to associate with the telemetry frames.

        Returns:
            None
        """
        for frame in telemetry_sequence.frames:
            self.telemetry_repository.create_from_telemetry_frame(
                telemetry_frame=frame, lap_id=lap_id, session_id=session_id
            )
        self.db_session.commit()
