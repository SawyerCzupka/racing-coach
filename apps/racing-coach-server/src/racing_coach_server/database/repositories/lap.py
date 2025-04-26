from ..models import Lap
from .base import BaseRepository
import uuid
import logging

logger = logging.getLogger(__name__)


class LapRepository(BaseRepository):
    def create(
        self,
        session_id: uuid.UUID,
        lap_number: int,
        lap_time: float | None = None,
        is_valid: bool = False,
    ) -> Lap:
        """Create a new lap record."""
        lap = Lap(
            session_id=session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )

        self.db_session.add(lap)
        self.db_session.commit()
        self.db_session.refresh(lap)

        logger.info(f"Created new lap record with ID: {lap.id}")
        return lap
