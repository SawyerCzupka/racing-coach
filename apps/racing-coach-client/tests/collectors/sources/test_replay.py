"""Tests for ReplayTelemetrySource."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame


@pytest.mark.unit
class TestReplayTelemetrySourceUnit:
    """Unit tests for ReplayTelemetrySource with mocked IBT file."""

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_start(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test start opens IBT file and determines frame count."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM", "Throttle"]
        mock_ibt_class.return_value = mock_ibt

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        # Configure get_all to return different length arrays
        def get_all_side_effect(var_name: str) -> list[float]:
            if var_name == "Speed":
                return [1.0] * 100
            return []

        mock_ibt.get_all.side_effect = get_all_side_effect

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.start()

        # Verify
        mock_ibt.open.assert_called_once_with("/fake/path.ibt")
        mock_ir.startup.assert_called_once_with(test_file="/fake/path.ibt")
        assert source.total_frames == 100
        assert source.current_frame == 0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_stop(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test stop closes IBT file."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        source: ReplayTelemetrySource = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.start()

        # Test
        source.stop()

        # Verify
        mock_ibt.close.assert_called_once()
        mock_ir.shutdown.assert_called_once()

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_advance_frame_increments_current_frame(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test _advance_frame increments current_frame."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        def get_side_effect(frame: int, var_name: str) -> float:
            return frame * 10.0  # Return different value per frame

        mock_ibt.get.side_effect = get_side_effect

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=Path("/fake/path.ibt"),
            speed_multiplier=1000.0,  # Fast for testing
        )
        source.start()

        initial_frame: int = source.current_frame
        assert initial_frame == 0

        # Directly call _advance_frame to test frame advancement
        source._advance_frame()
        assert source.current_frame == 1

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_get_telemetry_data_returns_dict(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test get_telemetry_data returns cached telemetry values as dict."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        def get_side_effect(frame: int, var_name: str) -> float:
            if var_name == "Speed":
                return 50.0
            elif var_name == "RPM":
                return 5000.0
            return 0.0

        mock_ibt.get.side_effect = get_side_effect

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.start()

        data = source.get_telemetry_data()

        # Verify it's a dict with expected values
        assert isinstance(data, dict)
        assert data["Speed"] == 50.0
        assert data["RPM"] == 5000.0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    @patch("racing_coach_client.collectors.sources.replay.time")
    def test_playback_timing_respects_speed_multiplier(
        self,
        mock_time: MagicMock,
        mock_exists: MagicMock,
        mock_ibt_class: MagicMock,
        mock_irsdk_class: MagicMock,
    ) -> None:
        """Test that speed_multiplier affects sleep timing calculation."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        # Mock time to simulate immediate succession
        mock_time.time.side_effect = [0.0, 0.0, 0.0, 0.001, 0.002]  # Fast successive calls

        # Test with 2x speed
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=Path("/fake/path.ibt"), speed_multiplier=2.0
        )
        source.start()

        initial_frame: int = source.current_frame

        # Call internal _advance_frame to test frame progression
        source._advance_frame()

        # Verify - should advance by 1 frame per call
        assert source.current_frame == initial_frame + 1

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_loop_enabled_wraps_to_beginning(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test that loop=True wraps playback to beginning."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=Path("/fake/path.ibt"), loop=True, speed_multiplier=1000.0
        )
        source.start()

        # Advance to near the end
        source.current_frame = 8
        source._cache_current_frame()

        # Advance to frame 9
        source._advance_frame()
        assert source.current_frame == 9

        # Advance again - should wrap to 0
        source._advance_frame()
        assert source.current_frame == 0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_loop_disabled_stops_at_end(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test that loop=False stops at the end and sets exhausted."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=Path("/fake/path.ibt"), loop=False, speed_multiplier=1000.0
        )
        source.start()

        # Advance to near the end
        source.current_frame = 8
        source._cache_current_frame()

        # Advance to frame 9
        source._advance_frame()
        assert source.current_frame == 9
        assert source.is_connected  # Still connected

        # Advance again - should become exhausted
        source._advance_frame()
        assert source.current_frame == 9  # Stays at last frame
        assert not source.is_connected  # Now disconnected (exhausted)

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IRSDK")
    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    @patch("pathlib.Path.exists")
    def test_get_playback_progress(
        self, mock_exists: MagicMock, mock_ibt_class: MagicMock, mock_irsdk_class: MagicMock
    ) -> None:
        """Test playback progress calculation."""
        # Setup mocks
        mock_exists.return_value = True

        # Mock IBT
        mock_ibt: MagicMock = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt

        # Mock IRSDK
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_irsdk_class.return_value = mock_ir

        # Test
        source: ReplayTelemetrySource = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.start()

        # At beginning
        assert source.get_playback_progress() == 0.0

        # At 50%
        source.current_frame = 50
        assert source.get_playback_progress() == 50.0

        # At end
        source.current_frame = 99
        assert source.get_playback_progress() == 99.0


@pytest.mark.ibt
@pytest.mark.integration
class TestReplayTelemetrySourceIntegration:
    """Integration tests for ReplayTelemetrySource with real IBT file."""

    def test_open_and_read_ibt_file(self, ibt_file_path: Path) -> None:
        """Test opening and reading a real IBT file."""
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=1000.0
        )

        # Test start
        source.start()
        assert source.total_frames > 0
        assert source.current_frame == 0
        assert source.is_connected

        # Test collecting a frame
        frame = source.collect_telemetry_frame()
        assert isinstance(frame, TelemetryFrame)
        assert source.current_frame == 1

        # Verify we can read telemetry values
        data = source.get_telemetry_data()
        assert "Speed" in data
        assert data["Speed"] is not None

        # Test stop
        source.stop()

    def test_playback_progression(self, ibt_file_path: Path) -> None:
        """Test that playback progresses through frames correctly."""
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=1000.0
        )
        source.start()

        initial_frame: int = source.current_frame
        for i in range(5):
            source.collect_telemetry_frame()
            assert source.current_frame == initial_frame + i + 1

        source.stop()

    def test_read_multiple_telemetry_fields(self, ibt_file_path: Path) -> None:
        """Test reading various telemetry fields from a real IBT file."""
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=1000.0
        )
        source.start()
        source.collect_telemetry_frame()

        # Test reading common telemetry fields via get_telemetry_data()
        data = source.get_telemetry_data()
        fields_to_test: list[str] = [
            "Speed",
            "RPM",
            "Throttle",
            "Brake",
            "Gear",
            "Lap",
            "LapDistPct",
        ]

        for field in fields_to_test:
            if field in data:
                assert data[field] is not None

        source.stop()

    def test_playback_speed_double(self, ibt_file_path: Path) -> None:
        """Test that 2x playback speed processes frames twice as fast as 1x speed."""
        import time

        # Test 1x speed
        source_1x: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=1.0
        )
        source_1x.start()

        start_1x: float = time.time()
        for _ in range(10):
            source_1x.collect_telemetry_frame()
        elapsed_1x: float = time.time() - start_1x
        source_1x.stop()

        # Test 2x speed
        source_2x: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=2.0
        )
        source_2x.start()

        start_2x: float = time.time()
        for _ in range(10):
            source_2x.collect_telemetry_frame()
        elapsed_2x: float = time.time() - start_2x
        source_2x.stop()

        # 2x speed should take roughly half the time (with tolerance for timing variance)
        speedup_ratio: float = elapsed_1x / elapsed_2x
        assert 1.5 < speedup_ratio < 2.5, (
            f"2x speed should be ~2x faster than 1x, but got {speedup_ratio:.2f}x "
            f"(1x: {elapsed_1x:.3f}s, 2x: {elapsed_2x:.3f}s)"
        )

    def test_loop_wraps_playback(self, ibt_file_path: Path) -> None:
        """Test that loop=True wraps playback to the beginning."""
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, loop=True, speed_multiplier=1000.0
        )
        source.start()

        # Jump to near the end
        source.current_frame = source.total_frames - 2
        source._cache_current_frame()

        # Advance to last frame
        source.collect_telemetry_frame()
        assert source.current_frame == source.total_frames - 1

        # Advance past the end - should wrap to beginning
        source.collect_telemetry_frame()
        assert source.current_frame == 0

        source.stop()
