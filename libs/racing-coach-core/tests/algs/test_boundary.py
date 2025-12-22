"""Tests for track boundary extraction and lateral position calculation."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from racing_coach_core.algs.boundary import (
    compute_lateral_positions,
    compute_lateral_positions_vectorized,
    get_lateral_position,
)
from racing_coach_core.schemas.telemetry import TelemetryFrame, TelemetrySequence
from racing_coach_core.schemas.track import (
    AugmentedTelemetryFrame,
    AugmentedTelemetrySequence,
    TrackBoundary,
)


@pytest.fixture
def simple_track_boundary() -> TrackBoundary:
    """Create a simple straight track boundary for testing.

    Track runs from (0, 0) to (0, 1) with width of 0.001 degrees.
    Left boundary: longitude = 0.0
    Right boundary: longitude = 0.001
    """
    grid_size = 100
    grid = np.linspace(0.0, 1.0, grid_size, endpoint=False)

    # Straight track along latitude axis
    left_lat = np.linspace(0.0, 1.0, grid_size)
    left_lon = np.zeros(grid_size)
    right_lat = np.linspace(0.0, 1.0, grid_size)
    right_lon = np.ones(grid_size) * 0.001

    return TrackBoundary(
        track_id=999,
        track_name="Test Track",
        track_config_name=None,
        grid_distance_pct=grid.tolist(),
        left_latitude=left_lat.tolist(),
        left_longitude=left_lon.tolist(),
        right_latitude=right_lat.tolist(),
        right_longitude=right_lon.tolist(),
        grid_size=grid_size,
        source_left_frames=100,
        source_right_frames=100,
    )


class TestTrackBoundary:
    """Tests for TrackBoundary model."""

    def test_from_boundary_laps(self) -> None:
        """Test creating TrackBoundary from boundary lap data."""
        # Create synthetic boundary lap data
        n_frames = 1000
        lap_dist = np.linspace(0.0, 1.0, n_frames, endpoint=False)

        left_data = pd.DataFrame(
            {
                "lap_distance_pct": lap_dist,
                "latitude": np.sin(lap_dist * 2 * np.pi),
                "longitude": np.cos(lap_dist * 2 * np.pi),
            }
        )

        right_data = pd.DataFrame(
            {
                "lap_distance_pct": lap_dist,
                "latitude": np.sin(lap_dist * 2 * np.pi) + 0.01,
                "longitude": np.cos(lap_dist * 2 * np.pi) + 0.01,
            }
        )

        boundary = TrackBoundary.from_boundary_laps(
            track_id=123,
            track_name="Test Circuit",
            left_lap_data=left_data,
            right_lap_data=right_data,
            grid_size=500,
        )

        assert boundary.track_id == 123
        assert boundary.track_name == "Test Circuit"
        assert boundary.grid_size == 500
        assert len(boundary.left_latitude) == 500
        assert len(boundary.grid_distance_pct) == 500

    def test_parquet_roundtrip(self, simple_track_boundary: TrackBoundary) -> None:
        """Test saving and loading TrackBoundary to/from Parquet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "boundary.parquet"

            # Save
            simple_track_boundary.to_parquet(path)
            assert path.exists()

            # Load
            loaded = TrackBoundary.from_parquet(path)

            # Verify
            assert loaded.track_id == simple_track_boundary.track_id
            assert loaded.track_name == simple_track_boundary.track_name
            assert loaded.grid_size == simple_track_boundary.grid_size
            assert np.allclose(loaded.left_latitude, simple_track_boundary.left_latitude)
            assert np.allclose(loaded.left_longitude, simple_track_boundary.left_longitude)


class TestGetLateralPosition:
    """Tests for get_lateral_position function."""

    def test_left_boundary_returns_minus_one(self, simple_track_boundary: TrackBoundary) -> None:
        """Position at left boundary should return -1.0."""
        # At lap distance 0.5, left boundary is at (0.5, 0.0)
        result = get_lateral_position(simple_track_boundary, 0.5, 0.5, 0.0)
        assert abs(result - (-1.0)) < 0.01

    def test_right_boundary_returns_plus_one(self, simple_track_boundary: TrackBoundary) -> None:
        """Position at right boundary should return 1.0."""
        # At lap distance 0.5, right boundary is at (0.5, 0.001)
        result = get_lateral_position(simple_track_boundary, 0.5, 0.5, 0.001)
        assert abs(result - 1.0) < 0.01

    def test_center_returns_zero(self, simple_track_boundary: TrackBoundary) -> None:
        """Position at track center should return 0.0."""
        # At lap distance 0.5, center is at (0.5, 0.0005)
        result = get_lateral_position(simple_track_boundary, 0.5, 0.5, 0.0005)
        assert abs(result) < 0.01

    def test_extrapolation_beyond_left(self, simple_track_boundary: TrackBoundary) -> None:
        """Position beyond left boundary should return < -1.0."""
        # 50% beyond left boundary
        result = get_lateral_position(simple_track_boundary, 0.5, 0.5, -0.0005)
        assert result < -1.0
        assert abs(result - (-2.0)) < 0.01

    def test_extrapolation_beyond_right(self, simple_track_boundary: TrackBoundary) -> None:
        """Position beyond right boundary should return > 1.0."""
        # 50% beyond right boundary
        result = get_lateral_position(simple_track_boundary, 0.5, 0.5, 0.0015)
        assert result > 1.0
        assert abs(result - 2.0) < 0.01

    def test_lap_distance_wraparound(self, simple_track_boundary: TrackBoundary) -> None:
        """Lap distance > 1.0 should wrap around."""
        # 1.5 should be same as 0.5
        result_wrapped = get_lateral_position(simple_track_boundary, 1.5, 0.5, 0.0005)
        result_normal = get_lateral_position(simple_track_boundary, 0.5, 0.5, 0.0005)
        assert abs(result_wrapped - result_normal) < 0.01


class TestVectorizedComputation:
    """Tests for compute_lateral_positions_vectorized function."""

    def test_batch_computation_matches_single(self, simple_track_boundary: TrackBoundary) -> None:
        """Vectorized computation should match single-point computation."""
        n_points = 100
        lap_distances = np.linspace(0.1, 0.9, n_points)

        # Use center positions
        latitudes = lap_distances  # Our test track has lat = lap_dist
        longitudes = np.ones(n_points) * 0.0005  # Center

        # Vectorized
        vectorized_results = compute_lateral_positions_vectorized(
            simple_track_boundary, lap_distances, latitudes, longitudes
        )

        # Single-point
        single_results = np.array(
            [
                get_lateral_position(simple_track_boundary, ld, lat, lon)
                for ld, lat, lon in zip(lap_distances, latitudes, longitudes, strict=False)
            ]
        )

        assert np.allclose(vectorized_results, single_results, atol=0.01)

    def test_vectorized_boundaries(self, simple_track_boundary: TrackBoundary) -> None:
        """Test vectorized computation at exact boundary positions."""
        grid = np.array(simple_track_boundary.grid_distance_pct)
        left_lats = np.array(simple_track_boundary.left_latitude)
        left_lons = np.array(simple_track_boundary.left_longitude)
        right_lats = np.array(simple_track_boundary.right_latitude)
        right_lons = np.array(simple_track_boundary.right_longitude)

        # Left boundary should be -1
        left_results = compute_lateral_positions_vectorized(
            simple_track_boundary, grid, left_lats, left_lons
        )
        assert np.allclose(left_results, -1.0, atol=0.001)

        # Right boundary should be +1
        right_results = compute_lateral_positions_vectorized(
            simple_track_boundary, grid, right_lats, right_lons
        )
        assert np.allclose(right_results, 1.0, atol=0.001)


class TestAugmentedTelemetry:
    """Tests for AugmentedTelemetryFrame and AugmentedTelemetrySequence."""

    @pytest.fixture
    def sample_frame(self) -> TelemetryFrame:
        """Create a sample TelemetryFrame for testing."""
        from datetime import datetime

        return TelemetryFrame(
            timestamp=datetime.now(),
            session_time=100.0,
            lap_number=1,
            lap_distance_pct=0.5,
            lap_distance=3000.0,
            current_lap_time=60.0,
            last_lap_time=120.0,
            best_lap_time=118.0,
            speed=50.0,
            rpm=5000.0,
            gear=3,
            throttle=0.8,
            brake=0.0,
            clutch=0.0,
            steering_angle=0.1,
            lateral_acceleration=1.0,
            longitudinal_acceleration=0.5,
            vertical_acceleration=0.0,
            yaw_rate=0.0,
            roll_rate=0.0,
            pitch_rate=0.0,
            velocity_x=50.0,
            velocity_y=0.0,
            velocity_z=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            latitude=-33.45,
            longitude=149.55,
            altitude=100.0,
            tire_temps={
                "LF": {"left": 80, "middle": 85, "right": 80},
                "RF": {"left": 80, "middle": 85, "right": 80},
                "LR": {"left": 80, "middle": 85, "right": 80},
                "RR": {"left": 80, "middle": 85, "right": 80},
            },
            tire_wear={
                "LF": {"left": 100, "middle": 100, "right": 100},
                "RF": {"left": 100, "middle": 100, "right": 100},
                "LR": {"left": 100, "middle": 100, "right": 100},
                "RR": {"left": 100, "middle": 100, "right": 100},
            },
            brake_line_pressure={"LF": 0, "RF": 0, "LR": 0, "RR": 0},
            track_temp=30.0,
            track_wetness=0,
            air_temp=25.0,
            session_flags=0,
            track_surface=3,
            on_pit_road=False,
        )

    def test_augmented_frame_from_telemetry_frame(self, sample_frame: TelemetryFrame) -> None:
        """Test creating AugmentedTelemetryFrame from TelemetryFrame."""
        augmented = AugmentedTelemetryFrame.from_telemetry_frame(sample_frame, 0.25)

        assert augmented.lateral_position == 0.25
        assert augmented.speed == sample_frame.speed
        assert augmented.lap_distance_pct == sample_frame.lap_distance_pct

    def test_augmented_sequence_iteration(self, sample_frame: TelemetryFrame) -> None:
        """Test iterating over AugmentedTelemetrySequence."""
        frames = [sample_frame] * 5
        lateral_positions = [0.0, -0.5, 0.5, -1.0, 1.0]

        sequence = AugmentedTelemetrySequence(frames=frames, lateral_positions=lateral_positions)

        assert len(sequence) == 5

        for i, augmented in enumerate(sequence.iter_augmented()):
            assert augmented.lateral_position == lateral_positions[i]

    def test_augmented_sequence_get_frame(self, sample_frame: TelemetryFrame) -> None:
        """Test getting single frame from AugmentedTelemetrySequence."""
        frames = [sample_frame] * 3
        lateral_positions = [-1.0, 0.0, 1.0]

        sequence = AugmentedTelemetrySequence(frames=frames, lateral_positions=lateral_positions)

        frame = sequence.get_augmented_frame(1)
        assert frame.lateral_position == 0.0

    def test_compute_lateral_positions_for_sequence(
        self, simple_track_boundary: TrackBoundary, sample_frame: TelemetryFrame
    ) -> None:
        """Test computing lateral positions for a TelemetrySequence."""
        # Create frames at different positions
        frames: list[TelemetryFrame] = []
        for i in range(5):
            frame = sample_frame.model_copy()
            frame.lap_distance_pct = i * 0.2
            frame.latitude = i * 0.2  # Match test track pattern
            frame.longitude = 0.0005  # Center
            frames.append(frame)

        sequence = TelemetrySequence(frames=frames)
        augmented = compute_lateral_positions(simple_track_boundary, sequence)

        assert len(augmented) == 5
        # All center positions should be ~0
        for lat_pos in augmented.lateral_positions:
            assert abs(lat_pos) < 0.1
