"""This file is responsible for monitoring the lap telemetry events and creating lap events.

It listens to the telemetry events and processes them to create lap events.

The motivation for this is that I don't want to send every telemetry event to the server (which is a lot of data),
but rather only the lap events. This way, I can reduce the amount of data sent to the server.
"""  # noqa: E501

import logging
from uuid import UUID, uuid4

from racing_coach_core.events import (
    Event,
    EventBus,
    HandlerContext,
    SessionRegistry,
    SystemEvents,
)
from racing_coach_core.events.checking import method_handles
from racing_coach_core.models.events import (
    LapAndSession,
    SessionEnd,
    SessionStart,
    TelemetryAndSessionId,
)
from racing_coach_core.models.telemetry import LapTelemetry, TelemetryFrame

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapHandler:
    def __init__(self, event_bus: EventBus, session_registry: SessionRegistry):
        self.event_bus = event_bus
        self.session_registry = session_registry

        self.current_lap: int = -1
        self.telemetry_buffer: list[TelemetryFrame] = []

        self.last_session_id: UUID | None = None

        self.num_telemetry_events: int = 0

    @method_handles(SystemEvents.SESSION_START)
    def handle_session_start(self, context: HandlerContext[SessionStart]):
        """Handle session start events and flush buffer if session changed."""
        new_session = context.event.data.SessionFrame
        if self.last_session_id is not None and new_session.session_id != self.last_session_id:
            # if len(self.telemetry_buffer) > 0:
            logger.info("New session detected, flushing incomplete lap buffer")
            self.publish_lap_and_flush_buffer()
        self.last_session_id = new_session.session_id
        self.current_lap = -1

    @method_handles(SystemEvents.SESSION_END)
    def handle_session_end(self, context: HandlerContext[SessionEnd]):
        logger.info(f"Session complete. Collected {self.num_telemetry_events} telemetry events!")

    @method_handles(SystemEvents.TELEMETRY_EVENT)
    def handle_telemetry_frame(self, context: HandlerContext[TelemetryAndSessionId]):
        telemetry_frame: TelemetryFrame = context.event.data.telemetry

        self.num_telemetry_events += 1

        # Get session from registry
        current_session = self.session_registry.get_session(context.event.data.session_id)
        if current_session is None:
            logger.warning("Received telemetry frame but no active session")
            return

        # If old lap is finished, publish the telemetry and clear the buffer
        if telemetry_frame.lap_number != self.current_lap:
            logger.info(
                f"Lap change detected: {self.current_lap} -> {telemetry_frame.lap_number}"  # noqa: E501
            )
            # Ignore laps that are not fully completed and when returning to the pits
            if (
                telemetry_frame.lap_distance_pct < settings.LAP_COMPLETION_THRESHOLD
                and telemetry_frame.lap_number == 0
            ):
                self.current_lap = telemetry_frame.lap_number
                self.telemetry_buffer.clear()
                logger.info(
                    f"Ignoring lap change to {telemetry_frame.lap_number} due to low lap distance percentage."  # noqa: E501
                )
                return

            if self.current_lap == 0 or self.current_lap == -1:
                # Starting first lap or leaving pits, just clear the buffer and set current lap  # noqa: E501
                logger.info(
                    f"Starting first lap or leaving pits. Setting current lap to "
                    f"{telemetry_frame.lap_number} and clearing buffer."
                )

                self.current_lap = telemetry_frame.lap_number
                self.telemetry_buffer.clear()
                self.telemetry_buffer.append(telemetry_frame)
                return

            if len(self.telemetry_buffer) > 0:
                logger.info(f"Lap {self.current_lap} finished. Publishing telemetry data.")
                self.publish_lap_and_flush_buffer()
            self.current_lap = telemetry_frame.lap_number

        self.telemetry_buffer.append(telemetry_frame)

    def publish_lap_and_flush_buffer(self):
        if len(self.telemetry_buffer) == 0:
            logger.warning("Telemetry buffer is empty while trying to publish lap telemetry.")
            return

        current_session = self.session_registry.get_current_session()
        if current_session is None:
            logger.warning("Current session is None while trying to publish lap telemetry.")
            return

        lap_telemetry = LapTelemetry(frames=self.telemetry_buffer, lap_time=None)

        # Generate lap_id client-side so all handlers have immediate access
        lap_id = uuid4()

        self.event_bus.thread_safe_publish(
            Event(
                type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
                data=LapAndSession(
                    LapTelemetry=lap_telemetry,
                    SessionFrame=current_session,
                    lap_id=lap_id,
                ),
            )
        )

        # Clear the buffer after publishing
        self.telemetry_buffer.clear()
