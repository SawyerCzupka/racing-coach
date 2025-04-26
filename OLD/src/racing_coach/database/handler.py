from racing_coach.core.events import EventBus, HandlerContext, EventType
from racing_coach.core.schema.telemetry import SessionFrame, TelemetryFrame
from racing_coach.core.settings import settings

from .connector import DatabaseManager

import logging

logger = logging.getLogger(__name__)


class DatabaseHandler:
    def __init__(self, event_bus: EventBus, database: DatabaseManager):
        self.event_bus = event_bus
        self.db_manager = database

        self._frame_buffer: list[TelemetryFrame] = []
        self._frame_buffer_cache: list[TelemetryFrame] = []
        self._buffer_size = settings.DB_BATCH_SIZE

        self.session_info: SessionFrame | None = None
        self._session_started = False

        self.event_bus.subscribe(EventType.SESSION_FRAME, self._handle_session_frame)
        self.event_bus.subscribe(
            EventType.TELEMETRY_FRAME, self._handle_telemetry_frame
        )

    def _handle_session_frame(self, context: HandlerContext) -> None:
        frame: SessionFrame = context.event.data
        logger.info(f"Session started")
        self.session_info = frame
        try:
            self.db_manager.start_session(self.session_info)
        except Exception as e:
            logger.error(f"Failed to start session: {e}", stack_info=True)
        self._session_started = True

    def _handle_telemetry_frame(self, context: HandlerContext) -> None:
        if not self._session_started:
            return

        frame: TelemetryFrame = context.event.data
        self._frame_buffer.append(frame)

        if len(self._frame_buffer) >= self._buffer_size:
            self._frame_buffer_cache = self._frame_buffer.copy()
            self._frame_buffer = []
            self._save_buffered_frames()

    def _save_buffered_frames(self):
        logger.info(
            f"Saving {len(self._frame_buffer_cache)} telemetry frames to database"
        )
        if self._session_started:
            self.db_manager.save_telemetry_frame_batch(self._frame_buffer_cache)

    def start_session(self):
        if self.session_info is None:
            raise ValueError("Session info not set")
