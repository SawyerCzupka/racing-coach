import logging
from dataclasses import dataclass

from racing_coach.core.types.telemetry import LapTelemetry

from racing_coach.core.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


@dataclass
class BrakingEvent:
    start_distance: float
    start_frame: int
    entry_speed: float
    max_pressure: float
    end_frame: int = -1
    braking_duration: float = -1
    minimum_speed: float = -1


class BrakingEventAnalyzer:
    brake_threshold: float = settings.BRAKE_ZONE_MIN_PCT

    @staticmethod
    def analyze(lap: LapTelemetry) -> list[BrakingEvent]:
        """Extract the braking events from the lap telemetry."""

        events: list[BrakingEvent] = []

        current_event: BrakingEvent | None = None

        in_brake_event = False

        for i, frame in enumerate(lap.frames):
            # if not frame.brake > BrakingEventAnalyzer.brake_threshold:
            #     continue

            if (
                not in_brake_event
                and frame.brake > BrakingEventAnalyzer.brake_threshold
            ):
                in_brake_event = True

                current_event = BrakingEvent(
                    start_distance=frame.lap_distance,
                    start_frame=i,
                    max_pressure=frame.brake,
                    entry_speed=frame.speed,
                )

            # In braking zone, still on the brakes
            elif in_brake_event and frame.brake > BrakingEventAnalyzer.brake_threshold:
                current_event.max_pressure = max(
                    current_event.max_pressure, frame.brake
                )

            # In braking zone, off the brakes
            elif in_brake_event and frame.brake < BrakingEventAnalyzer.brake_threshold:
                in_brake_event = False

                current_event.end_frame = i

                current_event.braking_duration = (
                    frame.timestamp - lap.frames[current_event.start_frame].timestamp
                )

                current_event.minimum_speed = frame.speed

                events.append(current_event)

        return events
