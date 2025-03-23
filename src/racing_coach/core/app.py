import asyncio
import logging

from racing_coach.collectors.iracing import TelemetryCollector
from racing_coach.core.events import EventBus, EventType, HandlerContext
from racing_coach.core.schema.telemetry import (
    LapTelemetry,
    TelemetryFrame,
    SessionFrame,
)
from racing_coach.core.settings import settings
from racing_coach.database import DatabaseManager, DatabaseHandler

logger = logging.getLogger(__name__)


class RacingCoach:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        if settings.DB_ENABLED:
            self.db_manager = DatabaseManager(force_recreate=True)
            self.db_handler = DatabaseHandler(self.event_bus, self.db_manager)
            logger.info("Database enabled")

        self.event_bus.subscribe(EventType.LAP_COMPLETED, self._handle_lap_completed)
        self.event_bus.subscribe(EventType.TELEMETRY_FRAME, self._log_frame)
        self.event_bus.subscribe(EventType.SESSION_FRAME, self._log_session_frame)
        # asyncio.run(self.event_bus.start())
        self.event_bus.start()

    def _handle_lap_completed(self, context: HandlerContext) -> None:
        """Handle a completed lap."""

        lap: LapTelemetry = context.event.data

        logger.info(lap.is_valid())

    def _log_frame(self, context: HandlerContext) -> None:
        frame: TelemetryFrame = context.event.data

        logger.info(frame.throttle)

    def _log_session_frame(self, context: HandlerContext) -> None:
        frame: SessionFrame = context.event.data

        logger.info(f"Session Frame from Event Bus: {frame.model_dump()}")

    def run(self):
        """Run the racing coach.

        1. Probe iRacing until it is connected successfully
        2. Start the collector

        """

        # self.collector.connect()
        self.collector.start()

        logger.info("Racing coach started")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main():
    setup_logging()

    coach = RacingCoach()
    coach.run()


if __name__ == "__main__":
    main()
