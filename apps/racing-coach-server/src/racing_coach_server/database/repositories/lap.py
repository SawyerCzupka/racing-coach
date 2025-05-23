import logging
import uuid

from ..models import Lap
from .base import BaseRepository

logger = logging.getLogger(__name__)


class LapRepository(BaseRepository):
    def create(
        self,
        track_session_id: uuid.UUID,
        lap_number: int,
        lap_time: float | None = None,
        is_valid: bool = False,
    ) -> Lap:
        """Create a new lap record."""
        lap = Lap(
            track_session_id=track_session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )

        self.db_session.add(lap)
        # self.db_session.commit()
        # self.db_session.refresh(lap)
        return lap
