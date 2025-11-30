"""
Python wrapper for the Rust extension module.

This module provides a clean interface to the Rust functions and handles
the case where the Rust extension isn't available (e.g., during development
without compiling Rust).

Usage:
    from racing_coach_core.rust_ext import (
        is_rust_available,
        extract_lap_metrics,
        extract_braking_zones,
        extract_corners,
    )

    # Check if Rust is available
    if is_rust_available():
        print("Using Rust for high-performance analysis!")

    # Extract full lap metrics (recommended for best performance)
    metrics = extract_lap_metrics(sequence, lap_number=1, lap_time=90.5)

    # Or extract individual event types
    braking_zones = extract_braking_zones(sequence)
    corners = extract_corners(sequence)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from racing_coach_core.algs.events import BrakingMetrics, CornerMetrics, LapMetrics
    from racing_coach_core.models.telemetry import TelemetrySequence

# Try to import the Rust extension, fall back to Python implementations if not available
_RUST_AVAILABLE = False

try:
    from racing_coach_core._rs import AnalysisConfig as _rs_AnalysisConfig
    from racing_coach_core._rs import TelemetryFrame as _rs_TelemetryFrame
    from racing_coach_core._rs import compute_speed_stats as _rs_compute_speed_stats
    from racing_coach_core._rs import hello_from_rust as _rs_hello_from_rust
    from racing_coach_core._rs import py_extract_braking_zones as _rs_extract_braking_zones
    from racing_coach_core._rs import py_extract_corners as _rs_extract_corners
    from racing_coach_core._rs import py_extract_lap_metrics as _rs_extract_lap_metrics

    _RUST_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    _rs_hello_from_rust = None  # type: ignore[assignment]
    _rs_compute_speed_stats = None  # type: ignore[assignment]
    _rs_extract_lap_metrics = None  # type: ignore[assignment]
    _rs_extract_braking_zones = None  # type: ignore[assignment]
    _rs_extract_corners = None  # type: ignore[assignment]
    _rs_TelemetryFrame = None  # type: ignore[assignment]
    _rs_AnalysisConfig = None  # type: ignore[assignment]


def is_rust_available() -> bool:
    """Check if the Rust extension is available."""
    return _RUST_AVAILABLE


def hello_from_rust(name: str | None = None) -> str:
    """
    Say hello from Rust (or Python fallback).

    Args:
        name: Optional name to greet. If None, returns generic greeting.

    Returns:
        Greeting string.
    """
    if _RUST_AVAILABLE and _rs_hello_from_rust is not None:
        return _rs_hello_from_rust(name)

    # Python fallback
    if name:
        return f"Hello, {name}! Greetings from Python (Rust not available)."
    return "Hello from Python! (Rust extension not available)"


def compute_speed_stats(speeds: list[float]) -> tuple[float, float, float]:
    """
    Compute min, max, and mean of a list of speeds.

    Args:
        speeds: List of speed values.

    Returns:
        Tuple of (min, max, mean) speeds.
    """
    if _RUST_AVAILABLE and _rs_compute_speed_stats is not None:
        return _rs_compute_speed_stats(speeds)

    # Python fallback
    if not speeds:
        return (0.0, 0.0, 0.0)

    return (min(speeds), max(speeds), sum(speeds) / len(speeds))


def _convert_sequence_to_rust_frames(sequence: TelemetrySequence) -> list:
    """Convert a TelemetrySequence to Rust-compatible TelemetryFrame objects."""
    if _rs_TelemetryFrame is None:
        raise RuntimeError("Rust extension not available")

    return [
        _rs_TelemetryFrame(
            brake=frame.brake,
            throttle=frame.throttle,
            speed=frame.speed,
            lap_distance=frame.lap_distance,
            steering_angle=frame.steering_angle,
            lateral_acceleration=frame.lateral_acceleration,
            longitudinal_acceleration=frame.longitudinal_acceleration,
            timestamp=frame.timestamp.timestamp(),
        )
        for frame in sequence.frames
    ]


def _convert_rust_braking_metrics(rust_metrics) -> BrakingMetrics:
    """Convert Rust BrakingMetrics to Python BrakingMetrics."""
    from racing_coach_core.algs.events import BrakingMetrics

    return BrakingMetrics(
        braking_point_distance=rust_metrics.braking_point_distance,
        braking_point_speed=rust_metrics.braking_point_speed,
        end_distance=rust_metrics.end_distance,
        max_brake_pressure=rust_metrics.max_brake_pressure,
        braking_duration=rust_metrics.braking_duration,
        minimum_speed=rust_metrics.minimum_speed,
        initial_deceleration=rust_metrics.initial_deceleration,
        average_deceleration=rust_metrics.average_deceleration,
        braking_efficiency=rust_metrics.braking_efficiency,
        has_trail_braking=rust_metrics.has_trail_braking,
        trail_brake_distance=rust_metrics.trail_brake_distance,
        trail_brake_percentage=rust_metrics.trail_brake_percentage,
    )


def _convert_rust_corner_metrics(rust_metrics) -> CornerMetrics:
    """Convert Rust CornerMetrics to Python CornerMetrics."""
    from racing_coach_core.algs.events import CornerMetrics

    return CornerMetrics(
        turn_in_distance=rust_metrics.turn_in_distance,
        apex_distance=rust_metrics.apex_distance,
        exit_distance=rust_metrics.exit_distance,
        throttle_application_distance=rust_metrics.throttle_application_distance,
        turn_in_speed=rust_metrics.turn_in_speed,
        apex_speed=rust_metrics.apex_speed,
        exit_speed=rust_metrics.exit_speed,
        throttle_application_speed=rust_metrics.throttle_application_speed,
        max_lateral_g=rust_metrics.max_lateral_g,
        time_in_corner=rust_metrics.time_in_corner,
        corner_distance=rust_metrics.corner_distance,
        max_steering_angle=rust_metrics.max_steering_angle,
        speed_loss=rust_metrics.speed_loss,
        speed_gain=rust_metrics.speed_gain,
    )


def _convert_rust_lap_metrics(rust_metrics) -> LapMetrics:
    """Convert Rust LapMetrics to Python LapMetrics."""
    from racing_coach_core.algs.events import LapMetrics

    return LapMetrics(
        lap_number=rust_metrics.lap_number,
        lap_time=rust_metrics.lap_time,
        braking_zones=[_convert_rust_braking_metrics(b) for b in rust_metrics.braking_zones],
        corners=[_convert_rust_corner_metrics(c) for c in rust_metrics.corners],
        total_corners=rust_metrics.total_corners,
        total_braking_zones=rust_metrics.total_braking_zones,
        average_corner_speed=rust_metrics.average_corner_speed,
        max_speed=rust_metrics.max_speed,
        min_speed=rust_metrics.min_speed,
    )


def extract_lap_metrics(
    sequence: TelemetrySequence,
    lap_number: int | None = None,
    lap_time: float | None = None,
    brake_threshold: float = 0.05,
    steering_threshold: float = 0.15,
    throttle_threshold: float = 0.05,
) -> LapMetrics:
    """
    Extract comprehensive lap metrics from telemetry data.

    This is the main entry point for lap analysis. When Rust is available,
    it performs a highly optimized single-pass analysis. Otherwise, it
    falls back to the pure Python implementation.

    Args:
        sequence: TelemetrySequence containing telemetry frames.
        lap_number: The lap number (default: extracted from first frame).
        lap_time: Optional lap time in seconds.
        brake_threshold: Minimum brake pressure to consider as braking (default 0.05).
        steering_threshold: Minimum steering angle for turning (default 0.15 radians).
        throttle_threshold: Minimum throttle for acceleration (default 0.05).

    Returns:
        LapMetrics containing all detected braking zones, corners, and statistics.
    """
    if (
        _RUST_AVAILABLE
        and _rs_extract_lap_metrics is not None
        and _rs_TelemetryFrame is not None
        and _rs_AnalysisConfig is not None
    ):
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig(
            brake_threshold=brake_threshold,
            steering_threshold=steering_threshold,
            throttle_threshold=throttle_threshold,
        )

        # Get lap_number from first frame if not provided
        if lap_number is None and sequence.frames:
            lap_number = sequence.frames[0].lap_number

        rust_result = _rs_extract_lap_metrics(
            rust_frames,
            lap_number=lap_number or 0,
            lap_time=lap_time,
            config=config,
        )

        return _convert_rust_lap_metrics(rust_result)

    # Python fallback
    from racing_coach_core.algs.metrics import extract_lap_metrics as py_extract_lap_metrics

    return py_extract_lap_metrics(
        sequence,
        lap_number=lap_number,
        brake_threshold=brake_threshold,
        steering_threshold=steering_threshold,
        throttle_threshold=throttle_threshold,
    )


def extract_braking_zones(
    sequence: TelemetrySequence,
    brake_threshold: float = 0.05,
    steering_threshold: float = 0.15,
) -> list[BrakingMetrics]:
    """
    Extract braking zones from telemetry data.

    Args:
        sequence: TelemetrySequence containing telemetry frames.
        brake_threshold: Minimum brake pressure to consider as braking (default 0.05).
        steering_threshold: Minimum steering angle for trail braking detection (default 0.15).

    Returns:
        List of BrakingMetrics for each detected braking zone.
    """
    if (
        _RUST_AVAILABLE
        and _rs_extract_braking_zones is not None
        and _rs_TelemetryFrame is not None
        and _rs_AnalysisConfig is not None
    ):
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig(
            brake_threshold=brake_threshold,
            steering_threshold=steering_threshold,
        )

        rust_results = _rs_extract_braking_zones(rust_frames, config=config)
        return [_convert_rust_braking_metrics(r) for r in rust_results]

    # Python fallback
    from racing_coach_core.algs.metrics import _extract_braking_zones

    return _extract_braking_zones(sequence.frames, brake_threshold, steering_threshold)


def extract_corners(
    sequence: TelemetrySequence,
    steering_threshold: float = 0.15,
    throttle_threshold: float = 0.05,
) -> list[CornerMetrics]:
    """
    Extract corners from telemetry data.

    Args:
        sequence: TelemetrySequence containing telemetry frames.
        steering_threshold: Minimum steering angle to consider as turning (default 0.15).
        throttle_threshold: Minimum throttle for throttle application detection (default 0.05).

    Returns:
        List of CornerMetrics for each detected corner.
    """
    if (
        _RUST_AVAILABLE
        and _rs_extract_corners is not None
        and _rs_TelemetryFrame is not None
        and _rs_AnalysisConfig is not None
    ):
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig(
            steering_threshold=steering_threshold,
            throttle_threshold=throttle_threshold,
        )

        rust_results = _rs_extract_corners(rust_frames, config=config)
        return [_convert_rust_corner_metrics(r) for r in rust_results]

    # Python fallback
    from racing_coach_core.algs.metrics import _extract_corners

    return _extract_corners(sequence.frames, steering_threshold, throttle_threshold)
