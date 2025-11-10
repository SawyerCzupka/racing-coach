import logging
import time
from typing import Any

from racing_coach_core.events import EventBus, Handler, HandlerContext, SystemEvents
from racing_coach_core.events.checking import func_handles
from racing_coach_core.models.events import LapAndSession, TelemetryAndSession

from racing_coach_client.collectors.factory import create_telemetry_source
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_client.config import settings
from racing_coach_client.handlers import LapHandler, LapUploadHandler

logger = logging.getLogger(__name__)


@func_handles(SystemEvents.LAP_TELEMETRY_SEQUENCE)
def test_laps_handler(context: HandlerContext[LapAndSession]):
    pass


class RacingCoachClient:
    """
    Main application class for the Racing Coach Client.

    This class orchestrates the telemetry collection, event handling, and
    communication with the Racing Coach server.
    """

    def __init__(self):
        """
        Initialize the Racing Coach Client.

        Creates the event bus, telemetry source, collector, and handlers.
        The telemetry source type (live or replay) is determined by the
        application configuration.
        """
        # Create event bus
        self.event_bus = EventBus()

        # Create telemetry source based on configuration
        logger.info(f"Initializing telemetry source (mode: {settings.TELEMETRY_MODE})")
        telemetry_source = create_telemetry_source(settings)

        # Create telemetry collector with the source
        self.collector = TelemetryCollector(self.event_bus, telemetry_source)

        # Start event bus
        self.event_bus.start()

        # Register event handlers
        self.initialize_handlers()

        logger.info("Racing Coach Client initialized")
        print("Racing Coach Client initialized.")

    def initialize_handlers(self):
        handlers: list[Handler[Any]] = []

        lap_handler = LapHandler(self.event_bus)
        handlers.append(
            Handler[TelemetryAndSession](
                SystemEvents.TELEMETRY_FRAME,
                lap_handler.handle_telemetry_frame,
            )
        )

        lap_upload_handler = LapUploadHandler(self.event_bus)
        handlers.append(
            Handler[LapAndSession](
                SystemEvents.LAP_TELEMETRY_SEQUENCE,
                lap_upload_handler.handle_lap_complete_event,
            )
        )

        handlers.append(
            Handler(
                type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
                fn=test_laps_handler,
            )
        )

        self.event_bus.register_handlers(handlers)

    def run(self):
        print("Running Racing Coach Client...")

        self.collector.start()

        # Main loop to keep the client running
        try:
            while True:
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
    import signal

    def signal_handler(signum, frame):  # type: ignore
        logger.info(f"Signal {signum} received, initiating shutdown...")
        client.shutdown()
        # Ensure the program exits after shutdown, especially if shutdown doesn't exit
        # itself or if it's called from a non-main thread context that might not exit.
        # We might need to exit more forcefully if threads don't terminate.
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)  # type: ignore # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # type: ignore # Handle termination signals

    client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
