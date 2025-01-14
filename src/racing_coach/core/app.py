import logging

from racing_coach.core.types.telemetry import LapTelemetry
from racing_coach.collectors.iracing import TelemetryCollector

logger = logging.getLogger(__name__)


class RacingCoach:
    def __init__(self):
        self.collector = TelemetryCollector()

        self.collector.subscribe("lap_completed", self._handle_lap_completed)

    def _handle_lap_completed(self, lap: LapTelemetry) -> None:
        """Handle a completed lap."""

        pass

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
