from racing_coach_core.models.telemetry import TelemetrySequence

from .events import BrakingEvent, CornerEvent

D_STEERING_THRESHOLD: float = 0.15  # TODO: find a good value for this


def extract_corner_from_braking(
    sequence: TelemetrySequence,
    brake_event: BrakingEvent | None = None,
    steering_threshold: float = D_STEERING_THRESHOLD,
) -> list[CornerEvent]:
    events: list[CornerEvent] = []

    entry_dst: float | None = None
    apex_dst: float | None = None
    exit_dst: float | None = None

    max_lateral_accel: float = 0.0

    for frame in sequence.frames:
        if not entry_dst and frame.steering_angle > steering_threshold:
            entry_dst = frame.lap_distance

        elif entry_dst and not exit_dst:
            if frame.lateral_acceleration > max_lateral_accel:
                max_lateral_accel = frame.lateral_acceleration
                apex_dst = frame.lap_distance

            if frame.steering_angle < steering_threshold:
                exit_dst = frame.lap_distance

                if entry_dst and apex_dst and exit_dst:
                    events.append(
                        CornerEvent(
                            entry_distance=entry_dst,
                            apex_distance=apex_dst,
                            exit_distance=exit_dst,
                        )
                    )

                    entry_dst = None
                    apex_dst = None
                    exit_dst = None
                    max_lateral_accel = 0.0

    return events
