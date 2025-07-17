from dataclasses import dataclass


@dataclass
class BrakingEvent:
    start_distance: float
    start_frame: int
    entry_speed: float
    max_pressure: float
    end_frame: int = -1
    braking_duration: float = -1
    minimum_speed: float = -1


""" 
Want to be able to track:
- Entry Point
- Apex
- Exit Point (Essentially how much of the track is used on exit)

"""


@dataclass
class CornerEvent:
    entry_distance: float
    apex_distance: float  # Most important and telling
    exit_distance: float
