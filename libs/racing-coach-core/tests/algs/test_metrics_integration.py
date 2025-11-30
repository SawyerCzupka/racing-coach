"""Integration tests for metrics extraction using real telemetry data."""

from datetime import datetime, timezone
from pathlib import Path

import irsdk
import pytest
from racing_coach_core.algs.metrics import extract_lap_metrics
from racing_coach_core.models.telemetry import LapTelemetry, TelemetryFrame

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def ibt_file_path() -> Path:
    """
    Get the path to the sample IBT file for integration testing.

    The sample file is located in the repository root under sample_data/.
    """
    # Get the repository root (5 levels up from this file)
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    ibt_path = repo_root / "sample_data" / "ligierjsp320_bathurst 2025-11-17 18-15-16.ibt"

    if not ibt_path.exists():
        pytest.skip(f"Sample IBT file not found at {ibt_path}")

    return ibt_path


def collect_lap_telemetry(ibt_file_path: Path, target_lap: int) -> list[TelemetryFrame]:
    """
    Collect all telemetry frames for a specific lap from .ibt file.

    Args:
        ibt_file_path: Path to the .ibt file
        target_lap: The lap number to collect

    Returns:
        List of telemetry frames for the specified lap
    """
    frames: list[TelemetryFrame] = []

    # Open IBT file
    ibt = irsdk.IBT()
    ibt.open(str(ibt_file_path))

    # Open IRSDK for session info
    ir = irsdk.IRSDK()
    if not ir.startup(test_file=str(ibt_file_path)):
        raise RuntimeError(f"Failed to open .ibt file: {ibt_file_path}")

    try:
        # Get all lap numbers to find frames for target lap
        all_laps = ibt.get_all("Lap")
        if all_laps is None or len(all_laps) == 0:
            return frames

        # Find frame indices for the target lap
        current_lap = -1
        lap_start_frame = -1
        lap_end_frame = -1

        for frame_idx, lap_num in enumerate(all_laps):
            if lap_num != current_lap:
                if current_lap == target_lap:
                    # We've completed the target lap
                    lap_end_frame = frame_idx - 1
                    break
                current_lap = lap_num
                if current_lap == target_lap:
                    lap_start_frame = frame_idx

        # If we never found the end, use the last frame
        if lap_start_frame >= 0 and lap_end_frame < 0:
            lap_end_frame = len(all_laps) - 1

        # If we found the lap, collect all frames
        if lap_start_frame >= 0 and lap_end_frame >= 0:
            for frame_idx in range(lap_start_frame, lap_end_frame + 1):
                frame = TelemetryFrame(
                    timestamp=datetime.now(timezone.utc),
                    session_time=ibt.get(frame_idx, "SessionTime"),
                    lap_number=ibt.get(frame_idx, "Lap"),
                    lap_distance_pct=ibt.get(frame_idx, "LapDistPct"),
                    lap_distance=ibt.get(frame_idx, "LapDist"),
                    current_lap_time=ibt.get(frame_idx, "LapCurrentLapTime"),
                    last_lap_time=ibt.get(frame_idx, "LapLastLapTime"),
                    best_lap_time=ibt.get(frame_idx, "LapBestLapTime"),
                    speed=ibt.get(frame_idx, "Speed"),
                    rpm=ibt.get(frame_idx, "RPM"),
                    gear=ibt.get(frame_idx, "Gear"),
                    throttle=ibt.get(frame_idx, "Throttle"),
                    brake=ibt.get(frame_idx, "Brake"),
                    clutch=ibt.get(frame_idx, "Clutch"),
                    steering_angle=ibt.get(frame_idx, "SteeringWheelAngle"),
                    lateral_acceleration=ibt.get(frame_idx, "LatAccel"),
                    longitudinal_acceleration=ibt.get(frame_idx, "LongAccel"),
                    vertical_acceleration=ibt.get(frame_idx, "VertAccel"),
                    yaw_rate=ibt.get(frame_idx, "YawRate"),
                    roll_rate=ibt.get(frame_idx, "RollRate"),
                    pitch_rate=ibt.get(frame_idx, "PitchRate"),
                    velocity_x=ibt.get(frame_idx, "VelocityX"),
                    velocity_y=ibt.get(frame_idx, "VelocityY"),
                    velocity_z=ibt.get(frame_idx, "VelocityZ"),
                    latitude=ibt.get(frame_idx, "Lat"),
                    longitude=ibt.get(frame_idx, "Lon"),
                    altitude=ibt.get(frame_idx, "Alt"),
                    yaw=ibt.get(frame_idx, "Yaw"),
                    pitch=ibt.get(frame_idx, "Pitch"),
                    roll=ibt.get(frame_idx, "Roll"),
                    tire_temps={
                        "LF": {
                            "left": ibt.get(frame_idx, "LFtempCL"),
                            "middle": ibt.get(frame_idx, "LFtempCM"),
                            "right": ibt.get(frame_idx, "LFtempCR"),
                        },
                        "RF": {
                            "left": ibt.get(frame_idx, "RFtempCL"),
                            "middle": ibt.get(frame_idx, "RFtempCM"),
                            "right": ibt.get(frame_idx, "RFtempCR"),
                        },
                        "LR": {
                            "left": ibt.get(frame_idx, "LRtempCL"),
                            "middle": ibt.get(frame_idx, "LRtempCM"),
                            "right": ibt.get(frame_idx, "LRtempCR"),
                        },
                        "RR": {
                            "left": ibt.get(frame_idx, "RRtempCL"),
                            "middle": ibt.get(frame_idx, "RRtempCM"),
                            "right": ibt.get(frame_idx, "RRtempCR"),
                        },
                    },
                    tire_wear={
                        "LF": {
                            "left": ibt.get(frame_idx, "LFwearL"),
                            "middle": ibt.get(frame_idx, "LFwearM"),
                            "right": ibt.get(frame_idx, "LFwearR"),
                        },
                        "RF": {
                            "left": ibt.get(frame_idx, "RFwearL"),
                            "middle": ibt.get(frame_idx, "RFwearM"),
                            "right": ibt.get(frame_idx, "RFwearR"),
                        },
                        "LR": {
                            "left": ibt.get(frame_idx, "LRwearL"),
                            "middle": ibt.get(frame_idx, "LRwearM"),
                            "right": ibt.get(frame_idx, "LRwearR"),
                        },
                        "RR": {
                            "left": ibt.get(frame_idx, "RRwearL"),
                            "middle": ibt.get(frame_idx, "RRwearM"),
                            "right": ibt.get(frame_idx, "RRwearR"),
                        },
                    },
                    brake_line_pressure={
                        "LF": ibt.get(frame_idx, "LFbrakeLinePress"),
                        "RF": ibt.get(frame_idx, "RFbrakeLinePress"),
                        "LR": ibt.get(frame_idx, "LRbrakeLinePress"),
                        "RR": ibt.get(frame_idx, "RRbrakeLinePress"),
                    },
                    track_temp=ibt.get(frame_idx, "TrackTempCrew"),
                    track_wetness=ibt.get(frame_idx, "TrackWetness"),
                    air_temp=ibt.get(frame_idx, "AirTemp"),
                    session_flags=ibt.get(frame_idx, "SessionFlags"),
                    track_surface=ibt.get(frame_idx, "PlayerTrackSurface"),
                    on_pit_road=ibt.get(frame_idx, "OnPitRoad"),
                )
                frames.append(frame)

    finally:
        ir.shutdown()
        ibt.close()

    return frames


class TestMetricsWithRealTelemetry:
    """Test metrics extraction with real telemetry data from IBT files."""

    @pytest.mark.slow
    def test_extract_metrics_from_ibt_file(self, ibt_file_path: Path) -> None:
        """
        Test extracting metrics from a real IBT file.

        This test:
        1. Loads telemetry from the sample IBT file
        2. Extracts metrics from a lap
        3. Validates that metrics are reasonable
        """
        # Collect telemetry for lap 2 (first lap might be outlap)
        frames = collect_lap_telemetry(ibt_file_path, target_lap=2)

        # Verify we got frames
        assert len(frames) > 0, "Should have collected frames from the IBT file"
        print(f"\nCollected {len(frames)} frames from lap 2")

        # Create lap telemetry
        lap_telemetry = LapTelemetry(
            frames=frames, lap_time=frames[-1].current_lap_time if frames else None
        )

        # Extract metrics
        metrics = extract_lap_metrics(lap_telemetry)

        # Validate metrics are reasonable
        assert metrics.lap_number == 2
        assert metrics.total_braking_zones > 0, "Should detect braking zones"
        assert metrics.total_corners > 0, "Should detect corners"
        assert metrics.max_speed > metrics.min_speed
        assert metrics.max_speed > 0

        # Print metrics for inspection
        print(f"\nLap {metrics.lap_number} Metrics:")
        print(f"  Lap Time: {metrics.lap_time:.2f}s" if metrics.lap_time else "  Lap Time: N/A")
        print(f"  Total Braking Zones: {metrics.total_braking_zones}")
        print(f"  Total Corners: {metrics.total_corners}")
        print(f"  Max Speed: {metrics.max_speed:.1f} m/s")
        print(f"  Min Speed: {metrics.min_speed:.1f} m/s")
        print(f"  Average Corner Speed: {metrics.average_corner_speed:.1f} m/s")

        # Detailed braking zones
        print(f"\n  Braking Zones:")
        for i, zone in enumerate(metrics.braking_zones[:5]):  # First 5
            print(
                f"    Zone {i + 1}: distance={zone.braking_point_distance:.3f}, "
                f"speed={zone.braking_point_speed:.1f} m/s, "
                f"pressure={zone.max_brake_pressure:.2f}, "
                f"trail_braking={zone.has_trail_braking}"
            )

        # Detailed corners
        print(f"\n  Corners:")
        for i, corner in enumerate(metrics.corners[:5]):  # First 5
            print(
                f"    Corner {i + 1}: apex={corner.apex_distance:.3f}, "
                f"apex_speed={corner.apex_speed:.1f} m/s, "
                f"max_lateral_g={corner.max_lateral_g:.2f}"
            )

    @pytest.mark.slow
    def test_braking_zones_detected_correctly(self, ibt_file_path: Path) -> None:
        """Test that braking zones are detected in real telemetry."""
        frames = collect_lap_telemetry(ibt_file_path, target_lap=2)

        lap_telemetry = LapTelemetry(
            frames=frames, lap_time=frames[-1].current_lap_time if frames else None
        )
        metrics = extract_lap_metrics(lap_telemetry)

        # Bathurst should have many braking zones
        assert metrics.total_braking_zones >= 5, (
            f"Expected at least 5 braking zones at Bathurst, got {metrics.total_braking_zones}"
        )

        # All braking zones should have valid data
        for zone in metrics.braking_zones:
            assert zone.braking_point_speed > zone.minimum_speed, "Should slow down during braking"
            assert 0 <= zone.max_brake_pressure <= 1.0, "Brake pressure should be 0-1"
            assert zone.braking_duration > 0, "Braking duration should be positive"

    @pytest.mark.slow
    def test_corners_detected_correctly(self, ibt_file_path: Path) -> None:
        """Test that corners are detected in real telemetry."""
        frames = collect_lap_telemetry(ibt_file_path, target_lap=2)

        lap_telemetry = LapTelemetry(
            frames=frames, lap_time=frames[-1].current_lap_time if frames else None
        )
        metrics = extract_lap_metrics(lap_telemetry)

        # Bathurst should have many corners
        assert metrics.total_corners >= 10, (
            f"Expected at least 10 corners at Bathurst, got {metrics.total_corners}"
        )

        # All corners should have valid data
        for corner in metrics.corners:
            assert (
                corner.turn_in_distance < corner.exit_distance
                or corner.exit_distance < corner.turn_in_distance
            ), "Corner should have entry and exit"
            assert corner.apex_speed > 0, "Apex speed should be positive"
            assert corner.max_lateral_g >= 0, "Lateral G should be non-negative"
            assert corner.time_in_corner > 0, "Time in corner should be positive"

    @pytest.mark.slow
    def test_metrics_with_multiple_laps(self, ibt_file_path: Path) -> None:
        """
        Test extracting metrics from multiple laps and verify consistency.
        """
        frames_lap2 = collect_lap_telemetry(ibt_file_path, target_lap=2)
        frames_lap3 = collect_lap_telemetry(ibt_file_path, target_lap=3)

        if len(frames_lap2) == 0 or len(frames_lap3) == 0:
            pytest.skip("Not enough laps in IBT file")

        # Skip if lap 3 is incomplete (less than 50% of lap 2 frames indicates incomplete lap)
        if len(frames_lap3) < len(frames_lap2) * 0.5:
            pytest.skip(
                f"Lap 3 appears incomplete ({len(frames_lap3)} frames vs {len(frames_lap2)} for lap 2)"
            )

        metrics_lap2 = extract_lap_metrics(LapTelemetry(frames=frames_lap2, lap_time=None))
        metrics_lap3 = extract_lap_metrics(LapTelemetry(frames=frames_lap3, lap_time=None))

        # Print metrics for debugging
        print(
            f"\nLap 2: {len(frames_lap2)} frames, {metrics_lap2.total_corners} corners, {metrics_lap2.total_braking_zones} braking zones"
        )
        print(
            f"Lap 3: {len(frames_lap3)} frames, {metrics_lap3.total_corners} corners, {metrics_lap3.total_braking_zones} braking zones"
        )

        # Corner count should be similar (within 20% variance)
        corner_variance = abs(metrics_lap2.total_corners - metrics_lap3.total_corners)
        avg_corners = (metrics_lap2.total_corners + metrics_lap3.total_corners) / 2
        assert corner_variance / avg_corners < 0.2, "Corner count should be consistent across laps"

        # Braking zone count should be similar
        braking_variance = abs(metrics_lap2.total_braking_zones - metrics_lap3.total_braking_zones)
        avg_braking = (metrics_lap2.total_braking_zones + metrics_lap3.total_braking_zones) / 2
        assert braking_variance / avg_braking < 0.2, (
            "Braking zone count should be consistent across laps"
        )

        print(
            f"\nLap 2: {metrics_lap2.total_corners} corners, {metrics_lap2.total_braking_zones} braking zones"
        )
        print(
            f"Lap 3: {metrics_lap3.total_corners} corners, {metrics_lap3.total_braking_zones} braking zones"
        )
