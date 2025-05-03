import pandas as pd
from racing_coach_core.events import EventBus, EventType

from racing_coach_client.handlers.lap_upload_handler import LapUploadHandler

from .collectors.iracing import TelemetryCollector
from .handlers import LapHandler
from .server_api import client


class RacingCoachClient:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        self.api_client = client.RacingCoachServerClient()
        self.event_bus.start()

        self.initialize_handlers()

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

        self.collector._collection_loop()

        # Here you can add the main logic for your client application
        # For example, starting the telemetry collector or connecting to a server


def main():
    client = RacingCoachClient()
    client.run()


if __name__ == "__main__":
    main()
