"""Factories for creating test data for racing-coach-client tests."""

from factory import Faker, LazyAttribute
from racing_coach_core.tests.factories import (
    LapAndSessionFactory,
    LapTelemetryFactory,
    SessionFrameFactory,
    TelemetryAndSessionFactory,
    TelemetryFrameFactory,
)

# Re-export core factories for convenience
__all__ = [
    "TelemetryFrameFactory",
    "SessionFrameFactory",
    "LapTelemetryFactory",
    "TelemetryAndSessionFactory",
    "LapAndSessionFactory",
    "EnhancedTelemetryFrameFactory",
]


class EnhancedTelemetryFrameFactory(TelemetryFrameFactory):
    """
    Extended TelemetryFrameFactory with more realistic value ranges.

    Uses wider ranges for certain values to better match real-world racing data.
    """

    # Expand steering angle to full range (-π to π radians)
    steering_angle = Faker("pyfloat", min_value=-3.14159, max_value=3.14159)

    # More realistic tire temperatures (30-120°C)
    tire_temps: dict[str, dict[str, float]] = LazyAttribute(
        lambda _: {
            "LF": {
                "left": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "middle": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "right": Faker("pyfloat", min_value=30, max_value=120).generate(),
            },
            "RF": {
                "left": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "middle": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "right": Faker("pyfloat", min_value=30, max_value=120).generate(),
            },
            "LR": {
                "left": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "middle": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "right": Faker("pyfloat", min_value=30, max_value=120).generate(),
            },
            "RR": {
                "left": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "middle": Faker("pyfloat", min_value=30, max_value=120).generate(),
                "right": Faker("pyfloat", min_value=30, max_value=120).generate(),
            },
        }
    )
