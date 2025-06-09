from racing_coach_core.events import (
    Event,
    EventBus,
    EventType,
    HandlerContext,
    subscribe,
    EventHandler,
)

from racing_coach_core.models.telemetry import TelemetryFrame
import logging

logger = logging.getLogger(__name__)


class LogHandler(EventHandler):
    """This class will monitor the TELEMETRY_FRAME event and log the telemetry data."""

    def __init__(self, event_bus: EventBus, log_frequency: int = 60):
        super().__init__(event_bus)

        self.log_frequency = log_frequency  # Log the current telemetry frame if the count is a multiple of this value
        self.frame_count = -1

        self.event_bus.subscribe(EventType.TELEMETRY_FRAME, self.handle_telemetry_frame)

    def handle_telemetry_frame(self, context: HandlerContext):
        """Handle the telemetry frame event and log the data."""
        self.frame_count += 1
        telemetry_frame: TelemetryFrame = context.event.data.get("TelemetryFrame")
        session_frame = context.event.data.get("SessionFrame")
        if telemetry_frame and self.frame_count % self.log_frequency == 0:
            # Log the telemetry data
            logger.info(f"Telemetry Frame: {telemetry_frame}")
            logger.info(f"Session Frame: {session_frame}")

        else:
            logger.warning("No Telemetry Frame data found in the event.")
