"""
Telemetry collector class for iRacing.
"""

import logging
import threading
import time
from datetime import datetime
from racing_coach_core.events import Event, EventBus, EventType
from racing_coach_core.models.telemetry import (
    SessionFrame,
    TelemetryFrame,
)

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

        self.session_frame: SessionFrame | None = None

        self.running: bool = False

        self._collection_thread = None

    def start(self):
        """Start the telemetry collector."""
        if self.running:
            logger.warning("Telemetry collector is already running.")
            return

        self.running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop, name="TelemetryCollectorThread", daemon=True
        )
        self._collection_thread.start()
        logger.info("Telemetry collector thread started")

    def _collection_loop(self):
        """Main loop for collecting telemetry data."""
        if not self.connection.connect():
            logger.error("Failed to connect to iRacing")
            self.running = False
            return

        self.set_session_frame()
        try:
            while self.running:
                # Check if the connection is still valid
                if not self.connection.ensure_connected():
                    time.sleep(1)
                    continue

                self.collect_and_publish_telemetry_frame()

        except KeyboardInterrupt:
            logger.info("Stopping telemetry collection")
        finally:
            self.running = False  # not sure if this is strictly necessary
            self.connection.disconnect()

    def stop(self):
        """Stop the telemetry collector."""
        self.running = False
        self.connection.disconnect()

    def collect_and_publish_telemetry_frame(self):
        """Collect a single frame of telemetry data."""
        ir = self.connection.get_ir()
        assert ir, "iRacing connection is not established."

        ir.freeze_var_buffer_latest()

        frame = TelemetryFrame.from_irsdk(ir, datetime.now())

        self.event_bus.thread_safe_publish(
            Event(
                type=EventType.TELEMETRY_FRAME,
                data={"TelemetryFrame": frame, "SessionFrame": self.session_frame},
            )
        )

    def set_session_frame(self) -> SessionFrame:
        """Set the session frame."""
        ir = self.connection.get_ir()

        assert ir, "iRacing connection is not established."
        assert (
            self.connection.is_connected() == True
        ), "iRacing connection is not established."

        ir.freeze_var_buffer_latest()

        self.session_frame = SessionFrame.from_irsdk(ir, datetime.now())

        assert self.session_frame, "Session frame is not initialized."
        return self.session_frame
