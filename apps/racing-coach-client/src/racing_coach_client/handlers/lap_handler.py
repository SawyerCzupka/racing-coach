"""This file is responsible for monitoring the lap telemetry events and creating lap events.

It listens to the telemetry events and processes them to create lap events.

The motivation for this is that I don't want to send every telemetry event to the server (which is a lot of data),
but rather only the lap events. This way, I can reduce the amount of data sent to the server.
"""  # noqa: E501

import logging

from racing_coach_core.events import (
    Event,
    EventBus,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.events.checking import handler_for  # type: ignore # noqa: F401
from racing_coach_core.models.events import LapAndSession, TelemetryAndSession
from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapHandler:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.current_lap: int = -1
        self.telemetry_buffer: list[TelemetryFrame] = []

        self.current_session: SessionFrame | None = None

    # @handler_for(SystemEvents.TELEMETRY_FRAME)
    def handle_telemetry_frame(self, context: HandlerContext[TelemetryAndSession]):
        data = context.event.data

        telemetry_frame: TelemetryFrame = data.TelemetryFrame

        if self.current_session is None:
            self.current_session = data.SessionFrame

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
                logger.info(
                    f"Lap {self.current_lap} finished. Publishing telemetry data."
                )
                self.publish_lap_and_flush_buffer()
            self.current_lap = telemetry_frame.lap_number

        self.telemetry_buffer.append(telemetry_frame)

    def publish_lap_and_flush_buffer(self):
        if len(self.telemetry_buffer) == 0:
            logger.warning(
                "Telemetry buffer is empty while trying to publish lap telemetry."
            )
            return

        if self.current_session is None:
            logger.warning(
                "Current session is None while trying to publish lap telemetry."
            )
            return

        lap_telemetry = LapTelemetry(frames=self.telemetry_buffer, lap_time=None)

        self.event_bus.thread_safe_publish(
            Event(
                type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
                data=LapAndSession(
                    LapTelemetry=lap_telemetry, SessionFrame=self.current_session
                ),
            )
        )

        # Clear the buffer after publishing
        self.telemetry_buffer.clear()
