import logging

from racing_coach_core.models.telemetry import TelemetrySequence

from .events import BrakingEvent

logger = logging.getLogger(__name__)


def extract_braking_events(
    sequence: TelemetrySequence, brake_threshold: float = 0.05
) -> list[BrakingEvent]:
    """Extract the braking events from the lap telemetry."""

    events: list[BrakingEvent] = []
    current_event: BrakingEvent | None = None

    for i, frame in enumerate(sequence.frames):
        if not current_event and frame.brake > brake_threshold:
            current_event = BrakingEvent(
                start_distance=frame.lap_distance,
                start_frame=i,
                max_pressure=frame.brake,
                entry_speed=frame.speed,
            )

        # In braking zone, still on the brakes
        elif current_event and frame.brake > brake_threshold:
            current_event.max_pressure = max(current_event.max_pressure, frame.brake)

        # In braking zone, off the brakes
        elif current_event and frame.brake < brake_threshold:
            current_event.end_frame = i

            duration = (
                frame.timestamp - sequence.frames[current_event.start_frame].timestamp
            )

            current_event.braking_duration = duration.total_seconds()
            current_event.minimum_speed = frame.speed

            events.append(current_event)
            current_event = None

    return events
