import pandas as pd
from racing_coach_core.events import EventBus, EventType

from racing_coach_client.handlers.lap_upload_handler import LapUploadHandler

from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_client.handlers import LapHandler
from racing_coach_client.server_api import client

import logging
import signal
import time

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
        try:
            while True:
                # Keep the main thread alive, periodically checking for shutdown signals
                # or other conditions.
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down Racing Coach Client...")
        if self.collector:
            self.collector.stop()
        if self.event_bus:
            self.event_bus.stop()
        logger.info("Racing Coach Client shut down gracefully.")


def main():
    client = RacingCoachClient()

    # Graceful shutdown handling
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received, initiating shutdown...")
        client.shutdown()
        # Ensure the program exits after shutdown, especially if shutdown doesn't exit itself
        # or if it's called from a non-main thread context that might not exit.
        # We might need to exit more forcefully if threads don't terminate.
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Handle termination signals

    client.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
