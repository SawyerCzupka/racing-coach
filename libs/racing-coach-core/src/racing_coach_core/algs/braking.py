import logging
from dataclasses import dataclass

from racing_coach_core.models.telemetry import TelemetrySequence

# from racing_coach.core.settings import get_settings  # Not sure how to provide this

# settings = get_settings()


logger = logging.getLogger(__name__)

# brake_threshold: float = settings.BRAKE_ZONE_MIN_PCT


@dataclass
class BrakingEvent:
    start_distance: float
    start_frame: int
    entry_speed: float
    max_pressure: float
    end_frame: int = -1
    braking_duration: float = -1
    minimum_speed: float = -1


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
