import pandas as pd
from racing_coach_core.events import EventBus, EventType
from .collectors.iracing import TelemetryCollector
from .handlers import LapHandler


class RacingCoachClient:
    def __init__(self):
        self.event_bus = EventBus()
        self.collector = TelemetryCollector(self.event_bus)

        self.event_bus.start()

        self.initialize_handlers()

        print("Racing Coach Client initialized.")
        # You can initialize other client-specific components here if needed

    def initialize_handlers(self):
        # Initialize handlers and subscribe to events
        lap_handler = LapHandler(self.event_bus)

        self.event_bus.subscribe(
            EventType.TELEMETRY_FRAME, lap_handler.handle_telemetry_frame
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
