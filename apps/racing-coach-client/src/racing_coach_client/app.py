import logging
import time
from typing import Any

from racing_coach_core.events import (
    EventBus,
    Handler,
    SystemEvents,
)
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.schemas.events import (
    LapAndSession,
    SessionEnd,
    SessionStart,
    TelemetryAndSessionId,
)
from racing_coach_server_client import AuthenticatedClient

from racing_coach_client.auth import get_authenticated_client
from racing_coach_client.collectors.factory import create_telemetry_source
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_client.config import settings
from racing_coach_client.handlers import (
    LapHandler,
    LapUploadHandler,
    LogHandler,
    MetricsHandler,
    MetricsUploadHandler,
)
from racing_coach_client.logging_config import setup_logging

logger = logging.getLogger(__name__)


class RacingCoachClient:
    """
    Main application class for the Racing Coach Client.

    This class orchestrates the telemetry collection, event handling, and
    communication with the Racing Coach server.
    """

    def __init__(self, api_client: AuthenticatedClient):
        """
        Initialize the Racing Coach Client.

        Creates the event bus, telemetry source, collector, and handlers.
        The telemetry source type (live or replay) is determined by the
        application configuration.

        Args:
            api_client: Authenticated API client for server communication.
        """
        self.api_client = api_client

        # Create event bus
        self.event_bus = EventBus(max_queue_size=100_000)

        # Create session registry
        self.session_registry = SessionRegistry()

        # Create telemetry source based on configuration
        logger.info(f"Initializing telemetry source (mode: {settings.TELEMETRY_MODE})")
        telemetry_source = create_telemetry_source(settings)

        # Create telemetry collector with the source
        self.collector = TelemetryCollector(self.event_bus, telemetry_source, self.session_registry)

        # Start event bus
        self.event_bus.start()

        # Register event handlers
        self.initialize_handlers(upload=True)

        logger.info("Racing Coach Client initialized")
        print("Racing Coach Client initialized.")

    def initialize_handlers(self, upload: bool = False):
        handlers: list[Handler[Any]] = []

        lap_handler = LapHandler(self.event_bus, self.session_registry)
        handlers.append(
            Handler[SessionStart](
                SystemEvents.SESSION_START,
                lap_handler.handle_session_start,
            )
        )
        handlers.append(
            Handler[SessionEnd](
                SystemEvents.SESSION_END,
                lap_handler.handle_session_end,
            )
        )
        handlers.append(
            Handler[TelemetryAndSessionId](
                SystemEvents.TELEMETRY_EVENT,
                lap_handler.handle_telemetry_frame,
            )
        )

        if upload:
            lap_upload_handler = LapUploadHandler(self.event_bus, self.api_client)
            handlers.append(
                Handler[LapAndSession](
                    SystemEvents.LAP_TELEMETRY_SEQUENCE,
                    lap_upload_handler.handle_lap_complete_event,
                )
            )

        # Metrics extraction handler
        metrics_handler = MetricsHandler(self.event_bus)
        handlers.append(
            Handler[LapAndSession](
                SystemEvents.LAP_TELEMETRY_SEQUENCE,
                metrics_handler.handle_lap_telemetry,
            )
        )

        # Metrics upload handler
        if upload:
            metrics_upload_handler = MetricsUploadHandler(self.event_bus, self.api_client)
            handlers.append(
                Handler(
                    type=SystemEvents.LAP_METRICS_EXTRACTED,
                    fn=metrics_upload_handler.handle_metrics_extracted,
                )
            )

        log_handler = LogHandler(self.event_bus, self.session_registry, log_frequency=100_000)
        handlers.append(Handler(type=SystemEvents.SESSION_END, fn=log_handler.handle_session_end))

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
    # Configure logging first
    setup_logging(
        level=settings.LOG_LEVEL,
        use_color=settings.LOG_COLOR,
        show_module=settings.LOG_SHOW_MODULE,
    )

    # Authenticate with server (may prompt user for device authorization)
    logger.info("Authenticating with server...")
    api_client = get_authenticated_client(settings.SERVER_URL)

    # Create the racing coach client
    client = RacingCoachClient(api_client)

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
    main()
