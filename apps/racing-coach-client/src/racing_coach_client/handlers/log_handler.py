import logging
import threading

from racing_coach_core.events import (
    EventBus,
    HandlerContext,
    SessionRegistry,
    SystemEvents,
)
from racing_coach_core.events.checking import method_handles
from racing_coach_core.models.events import SessionEnd, TelemetryAndSessionId
from racing_coach_core.models.telemetry import TelemetryFrame

logger = logging.getLogger(__name__)


class LogHandler:
    """This class will monitor the TELEMETRY_EVENT event and log the telemetry data."""

    def __init__(
        self, event_bus: EventBus, session_registry: SessionRegistry, log_frequency: int = 60
    ):
        self.event_bus = event_bus
        self.session_registry = session_registry

        self.log_frequency = log_frequency  # Log the current telemetry frame if the count is a multiple of this value
        self.frame_count = 0

        self._lock = threading.RLock()

        self.event_bus.subscribe(SystemEvents.TELEMETRY_EVENT, self.handle_telemetry_frame)

    @method_handles(SystemEvents.TELEMETRY_EVENT)
    def handle_telemetry_frame(self, context: HandlerContext[TelemetryAndSessionId]):
        """Handle the telemetry frame event and log the data."""
        telemetry_frame: TelemetryFrame = context.event.data.telemetry

        if not telemetry_frame:
            logger.warning("No Telemetry Frame data found in the event.")
            return

        # if self.frame_count == 24583:
        #     logger.info("HANDLED LAST TELEMETRY FRAME")

        # if self.frame_count > 24000:
        if self.frame_count % self.log_frequency == 0:
            logger.info(f"Telemetry Frame: {telemetry_frame.model_dump_json(indent=2)}")
            session = self.session_registry.get_current_session()
            if session:
                logger.info(f"Session Frame: {session.model_dump_json(indent=2)}")

        # with self._lock:
        self.frame_count += 1

    @method_handles(SystemEvents.SESSION_END)
    def handle_session_end(self, context: HandlerContext[SessionEnd]):
        logger.info(f"Collected {self.frame_count} TELEMETRY_EVENT events.")
