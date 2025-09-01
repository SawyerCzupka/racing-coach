import logging

from racing_coach_core.events import (
    EventBus,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.models.events import TelemetryAndSession

logger = logging.getLogger(__name__)


class LogHandler:
    """This class will monitor the TELEMETRY_FRAME event and log the telemetry data."""

    def __init__(self, event_bus: EventBus, log_frequency: int = 60):
        self.event_bus = event_bus

        self.log_frequency = log_frequency  # Log the current telemetry frame if the count is a multiple of this value
        self.frame_count = -1

        self.event_bus.subscribe(
            SystemEvents.TELEMETRY_FRAME, self.handle_telemetry_frame
        )

    def handle_telemetry_frame(self, context: HandlerContext[TelemetryAndSession]):
        """Handle the telemetry frame event and log the data."""
        data = context.event.data

        if not data.TelemetryFrame:
            logger.warning("No Telemetry Frame data found in the event.")
            return

        self.frame_count += 1

        if self.frame_count % self.log_frequency == 0:
            logger.info(
                f"Telemetry Frame: {data.TelemetryFrame.model_dump_json(indent=2)}"
            )
            logger.info(f"Session Frame: {data.SessionFrame.model_dump_json(indent=2)}")
