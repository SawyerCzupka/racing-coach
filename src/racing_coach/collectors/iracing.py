"""
Telemetry collector class for iRacing.
"""

import logging
import time
from copy import deepcopy
from datetime import datetime
from typing import Any, Callable, Literal, TypeAlias

from racing_coach.core.events import Event, EventBus, EventType
from racing_coach.core.types.telemetry import LapTelemetry, TelemetryFrame

from .connection import iRacingConnectionManager

logger = logging.getLogger(__name__)


# EventType = Literal["lap_completed"]  # Add more events here
LapCallback: TypeAlias = Callable[[LapTelemetry], None]


class TelemetryCollector:
    def __init__(self, event_bus: EventBus):
        """Initialize the telemetry collector."""
        self.connection = iRacingConnectionManager()
        self.event_bus = event_bus
        self.last_time: float = time.time()
        self.running: bool = False

        self.data_buffer: list[TelemetryFrame] = []
        # self.data_buffer2: list[TelemetryFrame] = []
        self.last_lap_number = -1

    # def subscribe(self, event_type: EventType, callback: LapCallback) -> None:
    #     """Subscribe to events."""
    #     self._subscribers[event_type].append(callback)

    # def unsubscribe(self, event_type: EventType, callback: LapCallback) -> None:
    #     """Unsubscribe from events."""
    #     if callback in self._subscribers[event_type]:
    #         self._subscribers[event_type].remove(callback)

    # def notify_subscribers(self, event_type: EventType, data: Any) -> None:
    #     """Notify subscribers of a lap completion."""
    #     for subscriber in self._lap_subscribers[event_type]:
    #         try:
    #             subscriber(data)
    #         except Exception as e:
    #             logger.error(f"Error in lap subscriber callback: {e}")

    def collect_frame(self):
        """Collect a single frame of telemetry data."""
        ir = self.connection.get_ir()
        if not ir:
            return False

        ir.freeze_var_buffer_latest()

        frame = TelemetryFrame.from_irsdk(ir, datetime.now())

        self.event_bus.thread_safe_publish(
            Event(type=EventType.TELEMETRY_FRAME, data=frame)
        )

        if frame.lap_number != self.last_lap_number:
            logger.info(f"New lap: {frame.lap_number}")
            # New lap, save and reset the buffer.

            lap_frames = deepcopy(self.data_buffer)
            lap_telemetry = LapTelemetry(frames=lap_frames, lap_time=None)

            self.event_bus.thread_safe_publish(
                Event(EventType.LAP_COMPLETED, data=lap_telemetry)
            )

            if self.last_lap_number != -1:
                last_time = (
                    frame.last_lap_time
                )  # TODO: fix this, last lap isn't always the last lap

            self.last_lap_number = frame.lap_number
            self.data_buffer = []

        self.data_buffer.append(frame)

        return True

    def start(self):
        """Main loop for collecting telemetry data."""
        if not self.connection.connect():
            logger.error("Failed to connect to iRacing")
            return

        self.running = True
        try:
            while self.running:
                if not self.connection.ensure_connected():
                    time.sleep(1)
                    continue

                self.collect_frame()

        except KeyboardInterrupt:
            logger.info("Stopping telemetry collection")
        finally:
            self.stop()

    def stop(self):
        """Stop the telemetry collector."""
        self.running = False
        self.connection.disconnect()
