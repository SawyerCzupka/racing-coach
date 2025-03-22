import logging
import asyncio

from racing_coach.core.schema.telemetry import LapTelemetry, TelemetryFrame
from racing_coach.collectors.iracing import TelemetryCollector
from racing_coach.core.events import EventBus, EventType, HandlerContext

logger = logging.getLogger(__name__)


class RacingCoach:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        self.event_bus.subscribe(EventType.LAP_COMPLETED, self._handle_lap_completed)
        self.event_bus.subscribe(EventType.TELEMETRY_FRAME, self._log_frame)
        # asyncio.run(self.event_bus.start())
        self.event_bus.start()

    def _handle_lap_completed(self, context: HandlerContext) -> None:
        """Handle a completed lap."""

        lap: LapTelemetry = context.event.data

        logger.info(lap.is_valid())

    def _log_frame(self, context: HandlerContext) -> None:
        frame: TelemetryFrame = context.event.data

        logger.info(frame.throttle)

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
