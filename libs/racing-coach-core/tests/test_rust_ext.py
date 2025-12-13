"""Tests for the Rust extension module (rust_ext.py).

These tests verify that the Rust extension works correctly through the Python interface.
All tests require the Rust extension to be compiled and available.
"""

from datetime import datetime, timezone

import pytest
from racing_coach_core.rust_ext import (
    compute_speed_stats,
    extract_braking_zones,
    extract_corners,
    extract_lap_metrics,
    hello_from_rust,
    is_rust_available,
)
from racing_coach_core.schemas.telemetry import TelemetryFrame, TelemetrySequence

# Skip entire module if Rust not available
pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(not is_rust_available(), reason="Rust extension required"),
]


# =============================================================================
# Fixtures
# =============================================================================


def create_telemetry_frame(
    *,
    brake: float = 0.0,
    throttle: float = 0.0,
    speed: float = 50.0,
    lap_distance_pct: float = 0.5,
    steering_angle: float = 0.0,
    lateral_acceleration: float = 0.0,
    longitudinal_acceleration: float = 0.0,
    timestamp: datetime | None = None,
    lap_number: int = 1,
) -> TelemetryFrame:
    """Create a TelemetryFrame with sensible defaults."""
    return TelemetryFrame(
        timestamp=timestamp or datetime.now(timezone.utc),
        session_time=0.0,
        lap_number=lap_number,
        lap_distance_pct=lap_distance_pct,
        lap_distance=lap_distance_pct * 5000,  # Assume 5km track
        current_lap_time=0.0,
        last_lap_time=0.0,
        best_lap_time=0.0,
        speed=speed,
        rpm=5000.0,
        gear=3,
        throttle=throttle,
        brake=brake,
        clutch=0.0,
        steering_angle=steering_angle,
        lateral_acceleration=lateral_acceleration,
        longitudinal_acceleration=longitudinal_acceleration,
        vertical_acceleration=0.0,
        yaw_rate=0.0,
        roll_rate=0.0,
        pitch_rate=0.0,
        velocity_x=speed,
        velocity_y=0.0,
        velocity_z=0.0,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
        latitude=0.0,
        longitude=0.0,
        altitude=0.0,
        tire_temps={"LF": {"left": 80.0, "middle": 85.0, "right": 82.0}},
        tire_wear={"LF": {"left": 0.95, "middle": 0.93, "right": 0.94}},
        brake_line_pressure={"LF": 2.5},
        track_temp=30.0,
        track_wetness=0,
        air_temp=25.0,
        session_flags=0,
        track_surface=1,
        on_pit_road=False,
    )


@pytest.fixture
def minimal_telemetry_sequence() -> TelemetrySequence:
    """Create minimal valid TelemetrySequence with 10 frames."""
    frames = [create_telemetry_frame(lap_distance_pct=i / 10) for i in range(10)]
    return TelemetrySequence(frames=frames)


@pytest.fixture
def braking_telemetry_sequence() -> TelemetrySequence:
    """Create sequence with clear braking events.

    Simulates:
    - Straight (0.0-0.3): full throttle, high speed
    - Braking zone (0.3-0.5): heavy braking, speed decreasing
    - Corner (0.5-0.7): light braking, turning
    - Exit (0.7-1.0): throttle application
    """
    frames = []
    num_frames = 100

    for i in range(num_frames):
        pct = i / num_frames

        if pct < 0.3:
            # Straight - full throttle
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=1.0,
                brake=0.0,
                speed=80.0,
                steering_angle=0.0,
                longitudinal_acceleration=2.0,
            )
        elif pct < 0.5:
            # Braking zone
            brake_intensity = (pct - 0.3) / 0.2  # 0 to 1 over braking zone
            speed = 80.0 - (brake_intensity * 50)  # 80 -> 30 m/s
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.0,
                brake=0.8 + brake_intensity * 0.2,  # 0.8 to 1.0
                speed=speed,
                steering_angle=0.0,
                longitudinal_acceleration=-10.0,
            )
        elif pct < 0.7:
            # Corner with trail braking
            corner_pct = (pct - 0.5) / 0.2
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.0,
                brake=0.3 - corner_pct * 0.3,  # Trail off brake
                speed=30.0 + corner_pct * 10,  # Slowly accelerating
                steering_angle=0.5,  # Turning
                lateral_acceleration=15.0,
            )
        else:
            # Exit - accelerating
            exit_pct = (pct - 0.7) / 0.3
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.5 + exit_pct * 0.5,
                brake=0.0,
                speed=40.0 + exit_pct * 30,
                steering_angle=0.3 - exit_pct * 0.3,  # Unwinding steering
                longitudinal_acceleration=5.0,
            )

        frames.append(frame)

    return TelemetrySequence(frames=frames)


@pytest.fixture
def cornering_telemetry_sequence() -> TelemetrySequence:
    """Create sequence with clear cornering events."""
    frames = []
    num_frames = 100

    for i in range(num_frames):
        pct = i / num_frames

        if pct < 0.2:
            # Approach
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.8,
                speed=60.0,
                steering_angle=0.0,
                lateral_acceleration=0.0,
            )
        elif pct < 0.4:
            # Turn in
            turn_pct = (pct - 0.2) / 0.2
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.3,
                speed=50.0 - turn_pct * 15,
                steering_angle=turn_pct * 0.8,  # Increasing steering
                lateral_acceleration=turn_pct * 20,
            )
        elif pct < 0.6:
            # Apex
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.2,
                speed=35.0,
                steering_angle=0.8,  # Max steering
                lateral_acceleration=25.0,  # Max lateral G
            )
        elif pct < 0.8:
            # Exit
            exit_pct = (pct - 0.6) / 0.2
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.5 + exit_pct * 0.5,
                speed=35.0 + exit_pct * 25,
                steering_angle=0.8 - exit_pct * 0.6,  # Unwinding
                lateral_acceleration=25.0 - exit_pct * 20,
            )
        else:
            # Straight
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=1.0,
                speed=60.0,
                steering_angle=0.1,
                lateral_acceleration=2.0,
            )

        frames.append(frame)

    return TelemetrySequence(frames=frames)


# =============================================================================
# Test Classes
# =============================================================================


class TestRustExtBasic:
    """Basic function tests (hello_from_rust, is_rust_available)."""

    def test_is_rust_available_returns_bool(self) -> None:
        """is_rust_available should return a boolean."""
        result = is_rust_available()
        assert isinstance(result, bool)

    def test_is_rust_available_is_true(self) -> None:
        """Since we skipped if not available, it should be True here."""
        assert is_rust_available() is True

    def test_hello_from_rust_without_name(self) -> None:
        """hello_from_rust without name returns greeting."""
        result = hello_from_rust()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Hello" in result or "hello" in result.lower()

    def test_hello_from_rust_with_name(self) -> None:
        """hello_from_rust with name includes the name."""
        result = hello_from_rust("Alice")
        assert isinstance(result, str)
        assert "Alice" in result

    def test_hello_from_rust_with_none(self) -> None:
        """hello_from_rust with None is same as no argument."""
        result = hello_from_rust(None)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSpeedStats:
    """compute_speed_stats tests."""

    def test_normal_list(self) -> None:
        """Normal list returns correct (min, max, mean)."""
        speeds = [10.0, 20.0, 30.0, 40.0, 50.0]
        min_speed, max_speed, mean_speed = compute_speed_stats(speeds)

        assert min_speed == 10.0
        assert max_speed == 50.0
        assert mean_speed == 30.0

    def test_empty_list(self) -> None:
        """Empty list returns (0.0, 0.0, 0.0)."""
        result = compute_speed_stats([])
        assert result == (0.0, 0.0, 0.0)

    def test_single_value(self) -> None:
        """Single value: min == max == mean."""
        result = compute_speed_stats([42.5])
        assert result == (42.5, 42.5, 42.5)

    def test_two_values(self) -> None:
        """Two values calculates correctly."""
        min_speed, max_speed, mean_speed = compute_speed_stats([10.0, 30.0])

        assert min_speed == 10.0
        assert max_speed == 30.0
        assert mean_speed == 20.0

    def test_all_same_values(self) -> None:
        """All same values returns that value for all."""
        result = compute_speed_stats([25.0, 25.0, 25.0, 25.0])
        assert result == (25.0, 25.0, 25.0)

    def test_negative_values(self) -> None:
        """Handles negative values (edge case)."""
        min_speed, max_speed, mean_speed = compute_speed_stats([-5.0, 0.0, 5.0])

        assert min_speed == -5.0
        assert max_speed == 5.0
        assert mean_speed == 0.0

    def test_large_list(self) -> None:
        """Handles large lists efficiently."""
        speeds = list(range(1, 1001))  # 1 to 1000
        speeds_float = [float(s) for s in speeds]

        min_speed, max_speed, mean_speed = compute_speed_stats(speeds_float)

        assert min_speed == 1.0
        assert max_speed == 1000.0
        assert mean_speed == 500.5


class TestMetricExtraction:
    """Metric extraction function tests."""

    def test_extract_lap_metrics_returns_lap_metrics(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """extract_lap_metrics returns a LapMetrics object."""
        from racing_coach_core.algs.events import LapMetrics

        result = extract_lap_metrics(minimal_telemetry_sequence)
        assert isinstance(result, LapMetrics)

    def test_extract_lap_metrics_has_correct_lap_number(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """lap_number is extracted from first frame."""
        result = extract_lap_metrics(minimal_telemetry_sequence)
        assert result.lap_number == 1

    def test_extract_lap_metrics_with_explicit_lap_number(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """Explicit lap_number overrides frame value."""
        result = extract_lap_metrics(minimal_telemetry_sequence, lap_number=5)
        assert result.lap_number == 5

    def test_extract_lap_metrics_with_lap_time(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """lap_time is set when provided."""
        result = extract_lap_metrics(minimal_telemetry_sequence, lap_time=90.5)
        assert result.lap_time == 90.5

    def test_extract_lap_metrics_braking_zones_is_list(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """braking_zones is a list."""
        result = extract_lap_metrics(minimal_telemetry_sequence)
        assert isinstance(result.braking_zones, list)

    def test_extract_lap_metrics_corners_is_list(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """corners is a list."""
        result = extract_lap_metrics(minimal_telemetry_sequence)
        assert isinstance(result.corners, list)

    def test_extract_braking_zones_returns_list(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """extract_braking_zones returns a list."""
        result = extract_braking_zones(minimal_telemetry_sequence)
        assert isinstance(result, list)

    def test_extract_corners_returns_list(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """extract_corners returns a list."""
        result = extract_corners(minimal_telemetry_sequence)
        assert isinstance(result, list)

    def test_extract_lap_metrics_custom_thresholds(
        self, minimal_telemetry_sequence: TelemetrySequence
    ) -> None:
        """Custom threshold parameters are accepted."""
        # Should not raise
        result = extract_lap_metrics(
            minimal_telemetry_sequence,
            brake_threshold=0.1,
            steering_threshold=0.2,
            throttle_threshold=0.1,
        )
        assert isinstance(result.braking_zones, list)


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_sequence(self) -> None:
        """Empty sequence doesn't crash."""
        empty_seq = TelemetrySequence(frames=[])
        result = extract_lap_metrics(empty_seq)

        assert result.total_braking_zones == 0
        assert result.total_corners == 0

    def test_single_frame_sequence(self) -> None:
        """Single frame sequence doesn't crash."""
        single_frame_seq = TelemetrySequence(frames=[create_telemetry_frame()])
        result = extract_lap_metrics(single_frame_seq)

        assert result.total_braking_zones == 0
        assert result.total_corners == 0

    def test_two_frame_sequence(self) -> None:
        """Two frame sequence doesn't crash."""
        two_frame_seq = TelemetrySequence(
            frames=[
                create_telemetry_frame(lap_distance_pct=0.0),
                create_telemetry_frame(lap_distance_pct=0.5),
            ]
        )
        result = extract_lap_metrics(two_frame_seq)
        assert isinstance(result.braking_zones, list)

    def test_sequence_with_no_braking(self) -> None:
        """Sequence with brake always 0 returns no braking zones."""
        frames = [
            create_telemetry_frame(
                lap_distance_pct=i / 20,
                brake=0.0,
                throttle=1.0,
                speed=60.0,
            )
            for i in range(20)
        ]
        seq = TelemetrySequence(frames=frames)

        result = extract_braking_zones(seq)
        assert len(result) == 0

    def test_sequence_with_no_turning(self) -> None:
        """Sequence with steering always 0 returns no corners."""
        frames = [
            create_telemetry_frame(
                lap_distance_pct=i / 20,
                steering_angle=0.0,
                lateral_acceleration=0.0,
            )
            for i in range(20)
        ]
        seq = TelemetrySequence(frames=frames)

        result = extract_corners(seq)
        assert len(result) == 0


class TestSyntheticData:
    """Tests with realistic synthetic telemetry that verify detection."""

    def test_braking_zone_detected(self, braking_telemetry_sequence: TelemetrySequence) -> None:
        """Braking zones are detected in realistic data."""
        result = extract_lap_metrics(braking_telemetry_sequence)

        # Should detect at least one braking zone
        assert result.total_braking_zones >= 1, (
            f"Expected at least 1 braking zone, got {result.total_braking_zones}"
        )

    def test_braking_metrics_have_valid_fields(
        self, braking_telemetry_sequence: TelemetrySequence
    ) -> None:
        """Detected braking zones have valid field values."""
        zones = extract_braking_zones(braking_telemetry_sequence)

        if len(zones) > 0:
            zone = zones[0]

            # Check location metrics (distance is in meters, not normalized)
            assert zone.braking_point_distance >= 0
            assert zone.braking_point_speed > 0

            # Check performance metrics
            assert 0.0 <= zone.max_brake_pressure <= 1.0
            assert zone.braking_duration >= 0

    def test_corner_detected(self, cornering_telemetry_sequence: TelemetrySequence) -> None:
        """Corners are detected in realistic data."""
        result = extract_lap_metrics(cornering_telemetry_sequence)

        # Should detect at least one corner
        assert result.total_corners >= 1, f"Expected at least 1 corner, got {result.total_corners}"

    def test_corner_metrics_have_valid_fields(
        self, cornering_telemetry_sequence: TelemetrySequence
    ) -> None:
        """Detected corners have valid field values."""
        corners = extract_corners(cornering_telemetry_sequence)

        if len(corners) > 0:
            corner = corners[0]

            # Check location metrics (distance is in meters, not normalized)
            assert corner.turn_in_distance >= 0
            assert corner.apex_distance >= 0
            assert corner.exit_distance >= 0

            # Check speed metrics
            assert corner.apex_speed > 0
            assert corner.max_lateral_g >= 0
            assert corner.time_in_corner >= 0

    def test_lap_metrics_speed_stats(self, braking_telemetry_sequence: TelemetrySequence) -> None:
        """Lap metrics includes valid speed statistics."""
        result = extract_lap_metrics(braking_telemetry_sequence)

        assert result.max_speed >= result.min_speed
        assert result.max_speed > 0

    def test_braking_with_trail_braking_detection(
        self, braking_telemetry_sequence: TelemetrySequence
    ) -> None:
        """Trail braking can be detected when present."""
        zones = extract_braking_zones(braking_telemetry_sequence)

        # Just verify the fields exist and are boolean/numeric
        for zone in zones:
            assert isinstance(zone.has_trail_braking, bool)
            assert isinstance(zone.trail_brake_distance, float)
            assert isinstance(zone.trail_brake_percentage, float)
