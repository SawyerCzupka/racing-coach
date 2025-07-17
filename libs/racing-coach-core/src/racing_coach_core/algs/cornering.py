from racing_coach_core.models.telemetry import TelemetrySequence

from .events import CornerEvent, BrakingEvent

D_STEERING_THRESHOLD: float = 0.15 # TODO: find a good value for this


def extract_corner_from_braking(
    sequence: TelemetrySequence,
    brake_event: BrakingEvent,
    steering_threshold: float = D_STEERING_THRESHOLD,
):
    events: list[CornerEvent] = []
    
    entry_dst: float | None = None
    apex_dst: float | None = None
    exit_dst: float | None = None
    
    
    
    for i, frame in enumerate(sequence.frames):
        if not entry_dst and frame.steering_angle > steering_threshold:
            entry_dst = frame.lap_distance
        
        elif entry_dst and not apex_dst:
            