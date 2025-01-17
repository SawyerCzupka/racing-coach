import logging

from racing_coach.core.types.telemetry import LapTelemetry
from racing_coach.collectors.iracing import TelemetryCollector
from racing_coach.core.events import EventBus, EventType, HandlerContext

logger = logging.getLogger(__name__)


class RacingCoach:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        self.event_bus.subscribe(EventType.LAP_COMPLETED, self._handle_lap_completed)

    def _handle_lap_completed(self, context: HandlerContext) -> None:
        """Handle a completed lap."""

        lap: LapTelemetry = context.event.data

        print(lap.is_valid())

    def run(self):
        """Run the racing coach.

        1. Probe iRacing until it is connected successfully
        2. Start the collector

        """

        self.collector.connect()
        self.collector.start()

        logger.info("Racing coach started")


if __name__ == "__main__":
    coach = RacingCoach()
    coach.run()
