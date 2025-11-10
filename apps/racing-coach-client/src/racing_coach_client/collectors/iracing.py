"""
Telemetry collector class for iRacing.

This module provides the main telemetry collection loop that works with
any TelemetrySource implementation (live or replay).
"""

import logging
import threading
import time
from datetime import datetime

from racing_coach_core.events import Event, EventBus, SystemEvents
from racing_coach_core.models.events import TelemetryAndSession
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame

from .sources import TelemetrySource

logger = logging.getLogger(__name__)

# Target telemetry collection rate (Hz)
COLLECTION_RATE_HZ = 60
FRAME_TIME_SECONDS = 1.0 / COLLECTION_RATE_HZ


class TelemetryCollector:
    """
    Collects telemetry data from a source and publishes events.

    This class manages the collection loop that reads telemetry data from
    any TelemetrySource implementation and publishes it to the event bus
    for processing by handlers.

    The collector runs in a separate thread and maintains the configured
    collection rate.

    Attributes:
        source: The telemetry data source (live or replay).
        event_bus: Event bus for publishing telemetry events.
        current_session: Current session metadata.
    """

    def __init__(self, event_bus: EventBus, source: TelemetrySource) -> None:
        """
        Initialize the telemetry collector.

        Args:
            event_bus: Event bus for publishing telemetry events.
            source: Telemetry source to collect data from.
        """
        self.source = source
        self.event_bus = event_bus

        self._running: bool = False
        self._collection_thread: threading.Thread | None = None

        # Current session metadata with unique UUID
        self.current_session: SessionFrame | None = None

    def start(self) -> None:
        """
        Start the telemetry collector thread.

        Spawns a new daemon thread that runs the collection loop.
        """
        if self._running:
            logger.warning("Telemetry collector is already running")
            return

        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            name="TelemetryCollectorThread",
            daemon=True,
        )
        self._collection_thread.start()
        logger.info("Telemetry collector thread started")

    def _collection_loop(self) -> None:
        """
        Main loop for collecting telemetry data.

        This method runs in a separate thread and continuously collects telemetry
        data from the source until stopped. It maintains the configured collection
        rate and handles connection failures gracefully.
        """
        # Initialize the telemetry source
        if not self.source.startup():
            logger.error("Failed to start telemetry source")
            self._running = False
            return

        # Collect the initial session frame
        try:
            self.current_session = self.collect_session_frame()
        except Exception as e:
            logger.error(f"Failed to collect initial session frame: {e}")
            self._running = False
            self.source.shutdown()
            return

        logger.info("Telemetry collection loop started")

        try:
            while self._running:
                # Check if the source is still connected
                if not self.source.is_connected():
                    logger.warning("Telemetry source disconnected, attempting to reconnect...")
                    if hasattr(self.source, "ensure_connected"):
                        # LiveTelemetrySource has ensure_connected method
                        if not self.source.ensure_connected():  # type: ignore
                            logger.error("Failed to reconnect, waiting before retry")
                            time.sleep(1)
                            continue
                    else:
                        # ReplayTelemetrySource doesn't reconnect
                        logger.error("Telemetry source disconnected")
                        break

                # Collect and publish the next frame
                try:
                    self.collect_and_publish_telemetry_frame()
                except Exception as e:
                    logger.error(f"Error collecting telemetry frame: {e}", exc_info=True)
                    # Continue collecting even if one frame fails
                    time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Telemetry collection interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in collection loop: {e}", exc_info=True)
        finally:
            self._running = False
            self.source.shutdown()
            logger.info("Telemetry collection loop stopped")

    def stop(self) -> None:
        """
        Stop the telemetry collector.

        Signals the collection thread to stop and shuts down the telemetry source.
        """
        logger.info("Stopping telemetry collector")
        self._running = False
        self.source.shutdown()

    def collect_and_publish_telemetry_frame(self) -> None:
        """
        Collect a single frame of telemetry data and publish it to the event bus.

        This method freezes the current telemetry buffer, creates a TelemetryFrame,
        and publishes it along with the session metadata.

        Raises:
            RuntimeError: If no session frame has been collected yet.
        """
        if self.current_session is None:
            raise RuntimeError("Cannot collect telemetry: no session frame available")

        # Freeze the buffer to get a consistent snapshot
        self.source.freeze_var_buffer_latest()

        # Create telemetry frame from the source
        telemetry_frame = TelemetryFrame.from_irsdk(self.source, datetime.now())

        # Publish to event bus
        self.event_bus.thread_safe_publish(
            Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(
                    TelemetryFrame=telemetry_frame,
                    SessionFrame=self.current_session,
                ),
            )
        )

    def collect_session_frame(self) -> SessionFrame:
        """
        Collect the current session metadata.

        This method freezes the telemetry buffer and extracts session information
        like track, car, and series details.

        Returns:
            SessionFrame: The collected session metadata.
        """
        self.source.freeze_var_buffer_latest()
        return SessionFrame.from_irsdk(self.source, datetime.now())
