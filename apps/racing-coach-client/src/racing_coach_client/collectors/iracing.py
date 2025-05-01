"""
Telemetry collector class for iRacing.
"""

import logging
import threading
import time
from datetime import datetime

from racing_coach_core.events import Event, EventBus, EventType
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame

from .connection import iRacingConnectionManager

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """
    A class responsible for collecting telemetry data from iRacing and publishing
    events to an event bus.
    """

    def __init__(self, event_bus: EventBus):
        """Initialize the telemetry collector."""
        self.connection = iRacingConnectionManager()
        self.event_bus = event_bus

        self._running: bool = False
        self._collection_thread = None

        # object to hold the current session with a unique uuid
        self.current_session: SessionFrame | None = None

    def start(self):
        """Start the telemetry collector."""
        if self._running:
            logger.warning("Telemetry collector is already running.")
            return

        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop, name="TelemetryCollectorThread", daemon=True
        )
        self._collection_thread.start()
        logger.info("Telemetry collector thread started")

    def _collection_loop(self):
        """
        Main loop for collecting telemetry data.

        This method runs in a separate thread and continuously collects telemetry
        data from iRacing until the `running` flag is set to False.
        """
        if not self.connection.connect():
            logger.error("Failed to connect to iRacing")
            self._running = False
            return

        # Collect the initial session frame
        self.current_session = self.collect_session_frame()
        if not self.current_session:
            logger.error("Failed to collect session frame")
            self._running = False
            return

        try:
            while self._running:
                # Check if the connection is still valid
                if not self.connection.ensure_connected():
                    time.sleep(1)
                    continue

                self.collect_and_publish_telemetry_frame()

        except KeyboardInterrupt:
            logger.info("Stopping telemetry collection")
        finally:
            self._running = False  # not sure if this is strictly necessary
            self.connection.disconnect()

    def stop(self):
        """Stop the telemetry collector."""
        self._running = False
        self.connection.disconnect()

    def collect_and_publish_telemetry_frame(self):
        """Collect a single frame of telemetry data."""
        ir = self.connection.get_ir()

        ir.freeze_var_buffer_latest()

        telemetry_frame = TelemetryFrame.from_irsdk(ir, datetime.now())

        self.event_bus.thread_safe_publish(
            Event(
                type=EventType.TELEMETRY_FRAME,
                data={
                    "TelemetryFrame": telemetry_frame,
                    "SessionFrame": self.current_session,
                },
            )
        )

    def collect_session_frame(self) -> SessionFrame:
        """Collects and sets the current session frame."""
        ir = self.connection.get_ir()

        ir.freeze_var_buffer_latest()

        return SessionFrame.from_irsdk(ir, datetime.now())
