"""Factories for creating test data for racing-coach-server tests."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from factory import Factory, Faker, LazyAttribute, LazyFunction, post_generation
from factory.builder import BuildStep
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame
from racing_coach_server.telemetry.models import (
    BrakingMetricsDB,
    CornerMetricsDB,
    Lap,
    LapMetricsDB,
    Telemetry,
    TrackSession,
)

# Type alias for tire temperature/wear data structure
type TireData = dict[str, dict[str, float]]
type BrakePressureData = dict[str, float]

# ============================================================================
# Core Library Factories (Re-exported from racing-coach-core)
# ============================================================================


class TelemetryFrameFactory(Factory[TelemetryFrame]):
    """
    Factory for creating TelemetryFrame instances.

    Generates realistic telemetry data for testing racing simulation features.
    All values are randomly generated with realistic ranges for sim racing data.
    """

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

    # Vehicle Velocity
    velocity_x = Faker("pyfloat", min_value=-100, max_value=100)
    velocity_y = Faker("pyfloat", min_value=-100, max_value=100)
    velocity_z = Faker("pyfloat", min_value=-100, max_value=100)

    # Vehicle Orientation
    yaw = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    pitch = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    roll = Faker("pyfloat", min_value=-3.14, max_value=3.14)

    # GPS Position
    latitude = Faker("pyfloat", min_value=-90, max_value=90)
    longitude = Faker("pyfloat", min_value=-180, max_value=180)
    altitude = Faker("pyfloat", min_value=0, max_value=3000)

    # Tire Data
    tire_temps: TireData = LazyAttribute(
        lambda _: {
            "LF": {"left": 80.0, "middle": 85.0, "right": 82.0},
            "RF": {"left": 81.0, "middle": 86.0, "right": 83.0},
            "LR": {"left": 78.0, "middle": 83.0, "right": 80.0},
            "RR": {"left": 79.0, "middle": 84.0, "right": 81.0},
        }
    )
    tire_wear: TireData = LazyAttribute(
        lambda _: {
            "LF": {"left": 0.95, "middle": 0.93, "right": 0.94},
            "RF": {"left": 0.94, "middle": 0.92, "right": 0.93},
            "LR": {"left": 0.96, "middle": 0.94, "right": 0.95},
            "RR": {"left": 0.95, "middle": 0.93, "right": 0.94},
        }
    )
    brake_line_pressure: BrakePressureData = LazyAttribute(
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
    """
    Factory for creating SessionFrame instances.

    Generates session metadata including track, car, and series information.
    Useful for testing session creation and management features.
    """

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


# ============================================================================
# Database Model Factories
# ============================================================================


class TrackSessionFactory(Factory[TrackSession]):
    """
    Factory for creating TrackSession database model instances.

    Generates TrackSession records with realistic track and car metadata.
    Automatically sets created_at and updated_at timestamps via post_generation hook.
    """

    class Meta:
        model = TrackSession

    id = LazyFunction(uuid4)
    track_id = Faker("pyint", min_value=1, max_value=500)
    track_name = Faker("company")
    track_config_name = Faker("word")
    track_type = "road course"
    car_id = Faker("pyint", min_value=1, max_value=200)
    car_name = Faker("company")
    car_class_id = Faker("pyint", min_value=1, max_value=50)
    series_id = Faker("pyint", min_value=1, max_value=100)

    @post_generation
    def set_timestamps(
        obj: TrackSession,
        create: bool,
        extracted: Any,
        **kwargs: Any,
    ) -> None:
        """
        Set timestamps after object creation.

        Args:
            obj: The TrackSession instance being created.
            create: Whether the object should be saved to database.
            extracted: Extracted value from the factory call.
            **kwargs: Additional keyword arguments.
        """
        obj.created_at = datetime.now(timezone.utc)
        obj.updated_at = datetime.now(timezone.utc)


class LapFactory(Factory[Lap]):
    """
    Factory for creating Lap database model instances.

    Generates Lap records with lap numbers and times.
    Useful for testing lap tracking and timing features.
    """

    class Meta:
        model = Lap

    id = LazyFunction(uuid4)
    track_session_id = LazyFunction(uuid4)
    lap_number = Faker("pyint", min_value=1, max_value=50)
    lap_time = Faker("pyfloat", min_value=60, max_value=180)
    is_valid = True


class TelemetryFactory(Factory[Telemetry]):
    """
    Factory for creating Telemetry database model instances.

    Generates comprehensive telemetry data records with all vehicle sensors,
    tire data, and environmental conditions. Useful for testing telemetry
    storage and retrieval features.
    """

    class Meta:
        model = Telemetry

    id = LazyFunction(uuid4)
    track_session_id = LazyFunction(uuid4)
    lap_id = LazyFunction(uuid4)

    # Time fields
    timestamp = LazyFunction(lambda: datetime.now(timezone.utc))
    session_time = Faker("pyfloat", min_value=0, max_value=3600)

    # Lap information
    lap_number = Faker("pyint", min_value=1, max_value=50)
    lap_distance_pct = Faker("pyfloat", min_value=0, max_value=1)
    lap_distance = Faker("pyfloat", min_value=0, max_value=5000)
    current_lap_time = Faker("pyfloat", min_value=60, max_value=180)
    last_lap_time = Faker("pyfloat", min_value=60, max_value=180)
    best_lap_time = Faker("pyfloat", min_value=60, max_value=180)

    # Vehicle state
    speed = Faker("pyfloat", min_value=0, max_value=100)
    rpm = Faker("pyfloat", min_value=1000, max_value=8000)
    gear = Faker("pyint", min_value=1, max_value=6)

    # Driver inputs
    throttle = Faker("pyfloat", min_value=0, max_value=1)
    brake = Faker("pyfloat", min_value=0, max_value=1)
    clutch = Faker("pyfloat", min_value=0, max_value=1)
    steering_angle = Faker("pyfloat", min_value=-1.57, max_value=1.57)

    # Vehicle dynamics
    lateral_acceleration = Faker("pyfloat", min_value=-20, max_value=20)
    longitudinal_acceleration = Faker("pyfloat", min_value=-20, max_value=20)
    vertical_acceleration = Faker("pyfloat", min_value=-10, max_value=10)
    yaw_rate = Faker("pyfloat", min_value=-1, max_value=1)
    roll_rate = Faker("pyfloat", min_value=-1, max_value=1)
    pitch_rate = Faker("pyfloat", min_value=-1, max_value=1)

    # Vehicle velocity
    velocity_x = Faker("pyfloat", min_value=-100, max_value=100)
    velocity_y = Faker("pyfloat", min_value=-100, max_value=100)
    velocity_z = Faker("pyfloat", min_value=-100, max_value=100)

    # Vehicle orientation
    yaw = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    pitch = Faker("pyfloat", min_value=-3.14, max_value=3.14)
    roll = Faker("pyfloat", min_value=-3.14, max_value=3.14)

    # GPS position
    latitude = Faker("pyfloat", min_value=-90, max_value=90)
    longitude = Faker("pyfloat", min_value=-180, max_value=180)
    altitude = Faker("pyfloat", min_value=0, max_value=3000)

    # Tire temperatures
    lf_tire_temp_left = Faker("pyfloat", min_value=70, max_value=90)
    lf_tire_temp_middle = Faker("pyfloat", min_value=70, max_value=90)
    lf_tire_temp_right = Faker("pyfloat", min_value=70, max_value=90)
    rf_tire_temp_left = Faker("pyfloat", min_value=70, max_value=90)
    rf_tire_temp_middle = Faker("pyfloat", min_value=70, max_value=90)
    rf_tire_temp_right = Faker("pyfloat", min_value=70, max_value=90)
    lr_tire_temp_left = Faker("pyfloat", min_value=70, max_value=90)
    lr_tire_temp_middle = Faker("pyfloat", min_value=70, max_value=90)
    lr_tire_temp_right = Faker("pyfloat", min_value=70, max_value=90)
    rr_tire_temp_left = Faker("pyfloat", min_value=70, max_value=90)
    rr_tire_temp_middle = Faker("pyfloat", min_value=70, max_value=90)
    rr_tire_temp_right = Faker("pyfloat", min_value=70, max_value=90)

    # Tire wear
    lf_tire_wear_left = Faker("pyfloat", min_value=0.9, max_value=1.0)
    lf_tire_wear_middle = Faker("pyfloat", min_value=0.9, max_value=1.0)
    lf_tire_wear_right = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rf_tire_wear_left = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rf_tire_wear_middle = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rf_tire_wear_right = Faker("pyfloat", min_value=0.9, max_value=1.0)
    lr_tire_wear_left = Faker("pyfloat", min_value=0.9, max_value=1.0)
    lr_tire_wear_middle = Faker("pyfloat", min_value=0.9, max_value=1.0)
    lr_tire_wear_right = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rr_tire_wear_left = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rr_tire_wear_middle = Faker("pyfloat", min_value=0.9, max_value=1.0)
    rr_tire_wear_right = Faker("pyfloat", min_value=0.9, max_value=1.0)

    # Brake pressure
    lf_brake_pressure = Faker("pyfloat", min_value=1.5, max_value=3.5)
    rf_brake_pressure = Faker("pyfloat", min_value=1.5, max_value=3.5)
    lr_brake_pressure = Faker("pyfloat", min_value=1.5, max_value=3.5)
    rr_brake_pressure = Faker("pyfloat", min_value=1.5, max_value=3.5)

    # Track conditions
    track_temp = Faker("pyfloat", min_value=15, max_value=50)
    track_wetness = Faker("pyint", min_value=0, max_value=3)
    air_temp = Faker("pyfloat", min_value=10, max_value=40)

    # Session state
    session_flags = Faker("pyint", min_value=0, max_value=65535)
    track_surface = Faker("pyint", min_value=0, max_value=3)
    on_pit_road = Faker("pybool")


# ============================================================================
# Metrics Database Model Factories
# ============================================================================


class LapMetricsDBFactory(Factory[LapMetricsDB]):
    """Factory for creating LapMetricsDB database model instances."""

    class Meta:
        model = LapMetricsDB

    lap_id = LazyFunction(uuid4)
    lap_time = Faker("pyfloat", min_value=60, max_value=180)
    total_corners = Faker("pyint", min_value=3, max_value=15)
    total_braking_zones = Faker("pyint", min_value=3, max_value=15)
    average_corner_speed = Faker("pyfloat", min_value=25, max_value=45)
    max_speed = Faker("pyfloat", min_value=70, max_value=100)
    min_speed = Faker("pyfloat", min_value=15, max_value=30)


class BrakingMetricsDBFactory(Factory[BrakingMetricsDB]):
    """Factory for creating BrakingMetricsDB database model instances."""

    class Meta:
        model = BrakingMetricsDB

    lap_metrics_id = LazyFunction(uuid4)
    zone_number = Faker("pyint", min_value=1, max_value=10)

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


class CornerMetricsDBFactory(Factory[CornerMetricsDB]):
    """Factory for creating CornerMetricsDB database model instances."""

    class Meta:
        model = CornerMetricsDB

    lap_metrics_id = LazyFunction(uuid4)
    corner_number = Faker("pyint", min_value=1, max_value=12)

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
