"""Unit tests for metrics extraction algorithms."""

from datetime import datetime, timedelta, timezone

import pytest
from racing_coach_core.algs.events import BrakingMetrics, CornerMetrics, LapMetrics
from racing_coach_core.algs.metrics import (
    BRAKE_THRESHOLD,
    STEERING_THRESHOLD,
    THROTTLE_THRESHOLD,
    extract_lap_metrics,
)
from racing_coach_core.models.telemetry import LapTelemetry, TelemetryFrame, TelemetrySequence


class TestExtractLapMetrics:
    """Test suite for extract_lap_metrics function."""

    def test_extract_metrics_from_empty_sequence_raises_error(self) -> None:
        """Test that extracting metrics from empty sequence raises ValueError."""
        empty_sequence = TelemetrySequence(frames=[], lap_time=None)

        with pytest.raises(ValueError, match="Cannot extract metrics from empty telemetry"):
            extract_lap_metrics(empty_sequence)

    def test_extract_metrics_from_single_frame(self) -> None:
        """Test extracting metrics from a single telemetry frame."""
        base_time = datetime.now(timezone.utc)
        frame = TelemetryFrame(
            timestamp=base_time,
            session_time=0.0,
            lap_number=1,
            lap_distance_pct=0.5,
            lap_distance=0.5,
            current_lap_time=30.0,
            last_lap_time=60.0,
            best_lap_time=60.0,
            speed=50.0,
            rpm=5000.0,
            gear=3,
            throttle=0.8,
            brake=0.0,
            clutch=0.0,
            steering_angle=0.0,
            lateral_acceleration=0.0,
            longitudinal_acceleration=0.0,
            vertical_acceleration=0.0,
            yaw_rate=0.0,
            roll_rate=0.0,
            pitch_rate=0.0,
            velocity_x=0.0,
            velocity_y=0.0,
            velocity_z=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            latitude=0.0,
            longitude=0.0,
            altitude=0.0,
            tire_temps={
                "LF": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "RF": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "LR": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "RR": {"left": 80.0, "middle": 80.0, "right": 80.0},
            },
            tire_wear={
                "LF": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "RF": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "LR": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "RR": {"left": 1.0, "middle": 1.0, "right": 1.0},
            },
            brake_line_pressure={"LF": 0.0, "RF": 0.0, "LR": 0.0, "RR": 0.0},
            track_temp=25.0,
            track_wetness=0,
            air_temp=20.0,
            session_flags=0,
            track_surface=0,
            on_pit_road=False,
        )

        sequence = LapTelemetry(frames=[frame], lap_time=60.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.lap_number == 1
        assert metrics.lap_time == 60.0
        assert metrics.total_braking_zones == 0
        assert metrics.total_corners == 0
        assert metrics.max_speed == 50.0
        assert metrics.min_speed == 50.0

    def test_detect_simple_braking_zone(self) -> None:
        """Test detection of a simple braking zone."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames: no braking -> braking -> no braking
        for i in range(10):
            brake_pressure = 0.8 if 3 <= i <= 6 else 0.0
            speed = 80.0 if i < 3 else (80.0 - (i - 2) * 10) if i <= 6 else 50.0

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.1,
                brake=brake_pressure,
                speed=speed,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=80.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_braking_zones == 1
        assert len(metrics.braking_zones) == 1

        braking_zone = metrics.braking_zones[0]
        assert braking_zone.braking_point_distance == pytest.approx(0.3, abs=0.01)
        assert braking_zone.max_brake_pressure == pytest.approx(0.8, abs=0.01)
        assert braking_zone.braking_point_speed > braking_zone.minimum_speed

    def test_detect_simple_corner(self) -> None:
        """Test detection of a simple corner."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames: straight -> turn -> straight
        for i in range(15):
            steering = 0.3 if 5 <= i <= 10 else 0.0
            speed = 60.0 if i < 5 else (60.0 - (i - 4) * 2) if i <= 7 else 50.0 + (i - 7) * 2

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.05,
                steering_angle=steering,
                speed=speed,
                throttle=0.5 if i >= 8 else 0.2,
                lateral_acceleration=1.5 if 5 <= i <= 10 else 0.0,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=90.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_corners == 1
        assert len(metrics.corners) == 1

        corner = metrics.corners[0]
        assert corner.turn_in_distance == pytest.approx(0.25, abs=0.01)
        assert corner.turn_in_speed > corner.apex_speed
        assert corner.exit_speed > corner.apex_speed

    def test_detect_trail_braking(self) -> None:
        """Test detection of trail braking (braking while turning)."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames with overlapping braking and steering
        for i in range(20):
            brake = 0.9 if 3 <= i <= 8 else 0.0
            steering = 0.3 if 6 <= i <= 12 else 0.0
            speed = 70.0 - i * 2 if i < 10 else 50.0

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.04,
                brake=brake,
                steering_angle=steering,
                speed=speed,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=100.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_braking_zones >= 1
        # Find braking zone with trail braking
        trail_braking_zone = next(
            (zone for zone in metrics.braking_zones if zone.has_trail_braking), None
        )
        assert trail_braking_zone is not None
        assert trail_braking_zone.trail_brake_distance > 0

    def test_no_braking_zones_detected(self) -> None:
        """Test lap with no braking (e.g., oval racing with constant throttle)."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames with no braking
        for i in range(100):
            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.01,
                brake=0.0,
                throttle=0.9,
                speed=85.0,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=100.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_braking_zones == 0
        assert len(metrics.braking_zones) == 0

    def test_no_corners_detected(self) -> None:
        """Test lap with minimal steering (straight line)."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames with minimal steering
        for i in range(100):
            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.01,
                steering_angle=0.05,  # Below threshold
                speed=90.0,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=90.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_corners == 0
        assert len(metrics.corners) == 0

    def test_lap_wrap_around_corner(self) -> None:
        """Test corner that wraps around start/finish line."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames with corner wrapping around (distance goes from 0.95 -> 1.0 -> 0.05)
        distances = [0.92, 0.94, 0.96, 0.98, 0.99, 0.01, 0.03, 0.05, 0.07]
        for i, dist in enumerate(distances):
            steering = 0.4  # Strong steering throughout
            speed = 40.0

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=dist,
                steering_angle=steering,
                speed=speed,
                lap_number=2 if dist < 0.5 else 1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=85.0)
        metrics = extract_lap_metrics(sequence)

        # Should detect the corner even though it wraps
        assert metrics.total_corners >= 1

    def test_multiple_braking_zones_and_corners(self) -> None:
        """Test lap with multiple braking zones and corners."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Simulate 3 corners with braking
        for corner_idx in range(3):
            base_dist = corner_idx * 0.3

            # Approach
            for i in range(5):
                frame = self._create_frame(
                    timestamp=base_time + timedelta(seconds=(corner_idx * 20 + i) * 0.1),
                    lap_distance=base_dist + i * 0.01,
                    speed=80.0,
                    brake=0.0,
                    steering_angle=0.0,
                    lap_number=1,
                )
                frames.append(frame)

            # Braking
            for i in range(5):
                frame = self._create_frame(
                    timestamp=base_time + timedelta(seconds=(corner_idx * 20 + 5 + i) * 0.1),
                    lap_distance=base_dist + 0.05 + i * 0.01,
                    speed=80.0 - i * 10,
                    brake=0.9,
                    steering_angle=0.0,
                    lap_number=1,
                )
                frames.append(frame)

            # Corner
            for i in range(10):
                frame = self._create_frame(
                    timestamp=base_time + timedelta(seconds=(corner_idx * 20 + 10 + i) * 0.1),
                    lap_distance=base_dist + 0.1 + i * 0.01,
                    speed=40.0 + i * 2,
                    brake=0.0,
                    steering_angle=0.4,
                    throttle=0.3 + i * 0.05,
                    lateral_acceleration=2.0,
                    lap_number=1,
                )
                frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=120.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.total_braking_zones == 3
        assert metrics.total_corners == 3

    def test_custom_thresholds(self) -> None:
        """Test that custom thresholds are respected."""
        base_time = datetime.now(timezone.utc)
        frames = []

        # Create frames with moderate brake pressure
        # (above MIN_BRAKE_PRESSURE=0.10 but below default threshold=0.05 won't work,
        # so we test with pressure above min filter but checking threshold behavior)
        for i in range(20):
            # 0.08 is above MIN_BRAKE_PRESSURE (0.10) but below default BRAKE_THRESHOLD (0.05)
            # Actually, 0.08 > 0.05 so it would be detected with default threshold
            # Let's use: 0.04 is below default 0.05, and test with 0.03 threshold
            # But MIN_BRAKE_PRESSURE is 0.10, so we need pressure >= 0.10
            # Use 0.12 pressure which is: > MIN_BRAKE_PRESSURE (0.10), and test threshold at 0.15
            brake = 0.12 if 3 <= i <= 12 else 0.0  # Duration ~1s to pass MIN_BRAKE_DURATION

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.1,
                brake=brake,
                speed=60.0,
                lap_number=1,
            )
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames, lap_time=60.0)

        # With high threshold (0.15), should not detect braking since max pressure is 0.12
        metrics_high_threshold = extract_lap_metrics(sequence, brake_threshold=0.15)
        assert metrics_high_threshold.total_braking_zones == 0

        # With lower threshold (0.10), should detect braking
        metrics_low_threshold = extract_lap_metrics(sequence, brake_threshold=0.10)
        assert metrics_low_threshold.total_braking_zones == 1

    def test_lap_statistics_calculation(self) -> None:
        """Test that lap-wide statistics are calculated correctly."""
        base_time = datetime.now(timezone.utc)
        frames = []

        speeds = [50.0, 60.0, 70.0, 80.0, 90.0, 85.0, 75.0, 65.0]
        for i, speed in enumerate(speeds):
            steering = 0.3 if i >= 4 else 0.0

            frame = self._create_frame(
                timestamp=base_time + timedelta(seconds=i * 0.1),
                lap_distance=i * 0.1,
                speed=speed,
                steering_angle=steering,
                lap_number=1,
            )
            frames.append(frame)

        sequence = LapTelemetry(frames=frames, lap_time=72.0)
        metrics = extract_lap_metrics(sequence)

        assert metrics.max_speed == 90.0
        assert metrics.min_speed == 50.0
        assert metrics.lap_time == 72.0

    # Helper method to create telemetry frames
    def _create_frame(
        self,
        timestamp: datetime,
        lap_distance: float,
        lap_number: int,
        speed: float = 60.0,
        brake: float = 0.0,
        throttle: float = 0.5,
        steering_angle: float = 0.0,
        lateral_acceleration: float = 0.0,
    ) -> TelemetryFrame:
        """Create a telemetry frame with specified parameters."""
        return TelemetryFrame(
            timestamp=timestamp,
            session_time=0.0,
            lap_number=lap_number,
            lap_distance_pct=lap_distance,
            lap_distance=lap_distance,
            current_lap_time=30.0,
            last_lap_time=60.0,
            best_lap_time=60.0,
            speed=speed,
            rpm=5000.0,
            gear=3,
            throttle=throttle,
            brake=brake,
            clutch=0.0,
            steering_angle=steering_angle,
            lateral_acceleration=lateral_acceleration,
            longitudinal_acceleration=0.0,
            vertical_acceleration=0.0,
            yaw_rate=0.0,
            roll_rate=0.0,
            pitch_rate=0.0,
            velocity_x=0.0,
            velocity_y=0.0,
            velocity_z=0.0,
            latitude=0.0,
            longitude=0.0,
            altitude=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            tire_temps={
                "LF": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "RF": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "LR": {"left": 80.0, "middle": 80.0, "right": 80.0},
                "RR": {"left": 80.0, "middle": 80.0, "right": 80.0},
            },
            tire_wear={
                "LF": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "RF": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "LR": {"left": 1.0, "middle": 1.0, "right": 1.0},
                "RR": {"left": 1.0, "middle": 1.0, "right": 1.0},
            },
            brake_line_pressure={"LF": brake, "RF": brake, "LR": brake, "RR": brake},
            track_temp=25.0,
            track_wetness=0,
            air_temp=20.0,
            session_flags=0,
            track_surface=0,
            on_pit_road=False,
        )
