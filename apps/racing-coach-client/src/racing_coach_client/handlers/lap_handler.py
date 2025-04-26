"""This file is responsible for monitoring the lap telemetry events and creating lap events.

It listens to the telemetry events and processes them to create lap events.

The motivation for this is that I don't want to send every telemetry event to the server (which is a lot of data),
but rather only the lap events. This way, I can reduce the amount of data sent to the server.
"""

from racing_coach_core.events import Event, EventBus, EventType, HandlerContext
from racing_coach_core.models.telemetry import (
    TelemetryFrame,
    SessionFrame,
    LapTelemetry,
)
import logging

logger = logging.getLogger(__name__)


class LapHandler:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.current_lap = -1

        self.telemetry_buffer = []

    def _validate_data(self, data):
        valid = True
        if not isinstance(data, dict):
            logger.error("Data is not a dictionary")
            valid = False
        if "TelemetryFrame" not in data:
            logger.error("Missing TelemetryFrame key in data")
            valid = False
        if "SessionFrame" not in data:
            logger.error("Missing SessionFrame key in data")
            valid = False
        if not isinstance(data["TelemetryFrame"], TelemetryFrame):
            logger.error(
                "Expected TelemetryFrame data type but got {}".format(type(data))
            )
            valid = False
        if not isinstance(data["SessionFrame"], SessionFrame):
            logger.error(
                "Expected SessionFrame data type but got {}".format(type(data))
            )
            valid = False
        return valid

    def handle_telemetry_frame(self, context: HandlerContext):
        data = context.event.data
        if not self._validate_data(data):
            logger.error("Invalid data received in handle_telemetry_frame")
            return

        telemetry_frame = data["TelemetryFrame"]

        if telemetry_frame.lap_number != self.current_lap:
            # New lap started
            if len(self.telemetry_buffer) > 0:
                self.publish_lap_and_flush_buffer()

            self.current_lap = telemetry_frame.lap_number
            self.telemetry_buffer.append(telemetry_frame)

    def publish_lap_and_flush_buffer(self):
        if len(self.telemetry_buffer) == 0:
            return

        lap_telemetry = LapTelemetry(frames=self.telemetry_buffer, lap_time=None)

        self.event_bus.publish(Event(EventType.LAP_TELEMETRY_SEQUENCE, lap_telemetry))

        # Clear the buffer after publishing
        self.telemetry_buffer.clear()
