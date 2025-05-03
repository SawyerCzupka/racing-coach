import pandas as pd
from racing_coach_core.events import EventBus, EventType

from racing_coach_client.handlers.lap_upload_handler import LapUploadHandler

from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_client.handlers import LapHandler
from racing_coach_client.server_api import client

import logging

logger = logging.getLogger(__name__)


class RacingCoachClient:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        self.api_client = client.RacingCoachServerClient()
        self.event_bus.start()

        self.initialize_handlers()

        logger.info("test")
        print("Racing Coach Client initialized.")
        # You can initialize other client-specific components here if needed

    def initialize_handlers(self):
        # Initialize handlers and subscribe to events
        lap_handler = LapHandler(self.event_bus)
        lap_upload_handler = LapUploadHandler(
            self.event_bus, api_client=self.api_client
        )

    def run(self):
        print("Running Racing Coach Client...")

        self.collector.start()

        # Here you can add the main logic for your client application
        # For example, starting the telemetry collector or connecting to a server


def main():
    client = RacingCoachClient()
    client.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
