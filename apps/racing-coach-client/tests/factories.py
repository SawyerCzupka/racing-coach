"""Factories for creating test data using polyfactory."""

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.fields import Use
from racing_coach_core.schemas.events import LapAndSession
from racing_coach_core.schemas.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)


def _default_tire_temps() -> dict[str, dict[str, float]]:
    """Generate default tire temperature data."""
    return {
        "LF": {"left": 80.0, "middle": 85.0, "right": 82.0},
        "RF": {"left": 81.0, "middle": 86.0, "right": 83.0},
        "LR": {"left": 78.0, "middle": 83.0, "right": 80.0},
        "RR": {"left": 79.0, "middle": 84.0, "right": 81.0},
    }


def _default_tire_wear() -> dict[str, dict[str, float]]:
    """Generate default tire wear data."""
    return {
        "LF": {"left": 0.95, "middle": 0.93, "right": 0.94},
        "RF": {"left": 0.94, "middle": 0.92, "right": 0.93},
        "LR": {"left": 0.96, "middle": 0.94, "right": 0.95},
        "RR": {"left": 0.95, "middle": 0.93, "right": 0.94},
    }


def _default_brake_line_pressure() -> dict[str, float]:
    """Generate default brake line pressure data."""
    return {"LF": 2.5, "RF": 2.5, "LR": 2.0, "RR": 2.0}


class TelemetryFrameFactory(ModelFactory[TelemetryFrame]):
    """Factory for creating TelemetryFrame instances."""

    tire_temps = Use(_default_tire_temps)
    tire_wear = Use(_default_tire_wear)
    brake_line_pressure = Use(_default_brake_line_pressure)


class SessionFrameFactory(ModelFactory[SessionFrame]): ...


class LapTelemetryFactory(ModelFactory[LapTelemetry]): ...


class LapAndSessionFactory(ModelFactory[LapAndSession]): ...
