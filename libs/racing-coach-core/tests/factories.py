"""Factories for creating test data using factory_boy."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from factory import Factory, Faker, LazyAttribute, LazyFunction, SubFactory
from racing_coach_core.algs.events import BrakingMetrics, CornerMetrics, LapMetrics
from racing_coach_core.models.events import LapAndSession, TelemetryAndSession
from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)


class TelemetryFrameFactory(Factory[TelemetryFrame]):
    """Factory for creating TelemetryFrame instances."""

    class Meta:
        model = TelemetryFrame

    # Time
    timestamp = LazyFunction(lambda: datetime.now(timezone.utc))
    session_time = Faker("pyfloat", min_value=0, max_value=3600)

    # Lap Information
    lap_number = Faker("pyint", min_value=1, max_value=50)
    lap_distance_pct = Faker("pyfloat", min_value=0, max_value=1)
    lap_distance = Faker("pyfloat", min_value=0, max_value=5000)
    current_lap_time = Faker("pyfloat", min_value=60, max_value=180)
    last_lap_time = Faker("pyfloat", min_value=60, max_value=180)
    best_lap_time = Faker("pyfloat", min_value=60, max_value=180)

    # Vehicle State
    speed = Faker("pyfloat", min_value=0, max_value=100)
    rpm = Faker("pyfloat", min_value=1000, max_value=8000)
    gear = Faker("pyint", min_value=1, max_value=6)

    # Driver Inputs
    throttle = Faker("pyfloat", min_value=0, max_value=1)
    brake = Faker("pyfloat", min_value=0, max_value=1)
    clutch = Faker("pyfloat", min_value=0, max_value=1)
    steering_angle = Faker("pyfloat", min_value=-1.57, max_value=1.57)

    # Vehicle Dynamics
    lateral_acceleration = Faker("pyfloat", min_value=-20, max_value=20)
    longitudinal_acceleration = Faker("pyfloat", min_value=-20, max_value=20)
    vertical_acceleration = Faker("pyfloat", min_value=-10, max_value=10)
    yaw_rate = Faker("pyfloat", min_value=-1, max_value=1)
    roll_rate = Faker("pyfloat", min_value=-1, max_value=1)
    pitch_rate = Faker("pyfloat", min_value=-1, max_value=1)

    # Vehicle Position/Orientation
    position_x = Faker("pyfloat", min_value=-100, max_value=100)
    position_y = Faker("pyfloat", min_value=-100, max_value=100)
    position_z = Faker("pyfloat", min_value=-100, max_value=100)
    yaw = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    pitch = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    roll = Faker("pyfloat", min_value=-3.14, max_value=3.14)

    # Tire Data
    tire_temps: dict[str, dict[str, float]] = LazyAttribute(
        lambda _: {
            "LF": {"left": 80.0, "middle": 85.0, "right": 82.0},
            "RF": {"left": 81.0, "middle": 86.0, "right": 83.0},
            "LR": {"left": 78.0, "middle": 83.0, "right": 80.0},
            "RR": {"left": 79.0, "middle": 84.0, "right": 81.0},
        }
    )
    tire_wear: dict[str, dict[str, float]] = LazyAttribute(
        lambda _: {
            "LF": {"left": 0.95, "middle": 0.93, "right": 0.94},
            "RF": {"left": 0.94, "middle": 0.92, "right": 0.93},
            "LR": {"left": 0.96, "middle": 0.94, "right": 0.95},
            "RR": {"left": 0.95, "middle": 0.93, "right": 0.94},
        }
    )
    brake_line_pressure: dict[str, float] = LazyAttribute(
        lambda _: {
            "LF": 2.5,
            "RF": 2.5,
            "LR": 2.0,
            "RR": 2.0,
        }
    )

    # Track Conditions
    track_temp = Faker("pyfloat", min_value=15, max_value=50)
    track_wetness = Faker("pyint", min_value=0, max_value=3)
    air_temp = Faker("pyfloat", min_value=10, max_value=40)

    # Session State
    session_flags = Faker("pyint", min_value=0, max_value=65535)
    track_surface = Faker("pyint", min_value=0, max_value=3)
    on_pit_road = Faker("pybool")


class SessionFrameFactory(Factory[SessionFrame]):
    """Factory for creating SessionFrame instances."""

    class Meta:
        model = SessionFrame

    timestamp = LazyFunction(lambda: datetime.now(timezone.utc))
    session_id = LazyFunction(uuid4)

    # Track
    track_id = Faker("pyint", min_value=1, max_value=500)
    track_name = Faker("company")
    track_config_name = Faker("word")
    track_type = "road course"

    # Car
    car_id = Faker("pyint", min_value=1, max_value=200)
    car_name = Faker("company")
    car_class_id = Faker("pyint", min_value=1, max_value=50)

    # Series
    series_id = Faker("pyint", min_value=1, max_value=100)


class LapTelemetryFactory(Factory[LapTelemetry]):
    """Factory for creating LapTelemetry instances."""

    class Meta:
        model = LapTelemetry

    frames: list[TelemetryFrame] = LazyAttribute(
        lambda _: [TelemetryFrameFactory.create() for _ in range(100)]
    )
    lap_time = Faker("pyfloat", min_value=60, max_value=180)


class TelemetryAndSessionFactory(Factory[TelemetryAndSession]):
    """Factory for creating TelemetryAndSession instances."""

    class Meta:
        model = TelemetryAndSession

    TelemetryFrame: TelemetryFrame = SubFactory(TelemetryFrameFactory)  # type: ignore[assignment]
    SessionFrame: SessionFrame = SubFactory(SessionFrameFactory)  # type: ignore[assignment]


class LapAndSessionFactory(Factory[LapAndSession]):
    """Factory for creating LapAndSession instances."""

    class Meta:
        model = LapAndSession

    LapTelemetry: LapTelemetry = SubFactory(LapTelemetryFactory)  # type: ignore[assignment]
    SessionFrame: SessionFrame = SubFactory(SessionFrameFactory)  # type: ignore[assignment]


class BrakingMetricsFactory(Factory[BrakingMetrics]):
    """Factory for creating BrakingMetrics instances."""

    class Meta:
        model = BrakingMetrics

    # Location and timing
    braking_point_distance = Faker("pyfloat", min_value=0, max_value=1)
    braking_point_speed = Faker("pyfloat", min_value=30, max_value=80)
    end_distance = Faker("pyfloat", min_value=0, max_value=1)

    # Performance metrics
    max_brake_pressure = Faker("pyfloat", min_value=0.5, max_value=1.0)
    braking_duration = Faker("pyfloat", min_value=0.5, max_value=3.0)
    minimum_speed = Faker("pyfloat", min_value=10, max_value=50)

    # Advanced metrics
    initial_deceleration = Faker("pyfloat", min_value=-15, max_value=-5)
    average_deceleration = Faker("pyfloat", min_value=-12, max_value=-4)
    braking_efficiency = Faker("pyfloat", min_value=5, max_value=15)

    # Trail braking
    has_trail_braking = Faker("pybool")
    trail_brake_distance = Faker("pyfloat", min_value=0, max_value=0.05)
    trail_brake_percentage = Faker("pyfloat", min_value=0, max_value=0.8)


class CornerMetricsFactory(Factory[CornerMetrics]):
    """Factory for creating CornerMetrics instances."""

    class Meta:
        model = CornerMetrics

    # Key corner points (distances)
    turn_in_distance = Faker("pyfloat", min_value=0, max_value=1)
    apex_distance = Faker("pyfloat", min_value=0, max_value=1)
    exit_distance = Faker("pyfloat", min_value=0, max_value=1)
    throttle_application_distance = Faker("pyfloat", min_value=0, max_value=1)

    # Speeds at key points
    turn_in_speed = Faker("pyfloat", min_value=20, max_value=60)
    apex_speed = Faker("pyfloat", min_value=15, max_value=50)
    exit_speed = Faker("pyfloat", min_value=20, max_value=70)
    throttle_application_speed = Faker("pyfloat", min_value=15, max_value=55)

    # Performance metrics
    max_lateral_g = Faker("pyfloat", min_value=0.5, max_value=3.0)
    time_in_corner = Faker("pyfloat", min_value=1.0, max_value=5.0)
    corner_distance = Faker("pyfloat", min_value=0.02, max_value=0.15)

    # Steering metrics
    max_steering_angle = Faker("pyfloat", min_value=0.2, max_value=1.5)

    # Speed delta
    speed_loss = Faker("pyfloat", min_value=5, max_value=30)
    speed_gain = Faker("pyfloat", min_value=5, max_value=40)


class LapMetricsFactory(Factory[LapMetrics]):
    """Factory for creating LapMetrics instances."""

    class Meta:
        model = LapMetrics

    lap_number = Faker("pyint", min_value=1, max_value=50)
    lap_time = Faker("pyfloat", min_value=60, max_value=180)

    # Collections of all events in the lap
    braking_zones: list[BrakingMetrics] = LazyAttribute(
        lambda _: [BrakingMetricsFactory.build() for _ in range(5)]
    )
    corners: list[CornerMetrics] = LazyAttribute(
        lambda _: [CornerMetricsFactory.build() for _ in range(6)]
    )

    # Lap-wide statistics
    total_corners = LazyAttribute(lambda obj: len(obj.corners))
    total_braking_zones = LazyAttribute(lambda obj: len(obj.braking_zones))
    average_corner_speed = Faker("pyfloat", min_value=25, max_value=45)
    max_speed = Faker("pyfloat", min_value=70, max_value=100)
    min_speed = Faker("pyfloat", min_value=15, max_value=30)
