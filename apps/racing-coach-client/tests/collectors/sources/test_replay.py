"""Tests for ReplayTelemetrySource."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource


@pytest.mark.unit
class TestReplayTelemetrySourceUnit:
    """Unit tests for ReplayTelemetrySource with mocked IBT file."""

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_startup(self, mock_ibt_class):
        """Test startup opens IBT file and determines frame count."""
        # Setup mock
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM", "Throttle"]
        mock_ibt_class.return_value = mock_ibt

        # Configure get_all to return different length arrays
        def get_all_side_effect(var_name):
            if var_name == "Speed":
                return [1.0] * 100
            return []

        mock_ibt.get_all.side_effect = get_all_side_effect

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.startup()

        # Verify
        mock_ibt.open.assert_called_once_with("/fake/path.ibt")
        assert source.frame_count == 100
        assert source.current_frame == 0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_shutdown(self, mock_ibt_class):
        """Test shutdown closes IBT file."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt

        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.startup()

        # Test
        source.shutdown()

        # Verify
        mock_ibt.close.assert_called_once()

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_freeze_var_buffer_latest(self, mock_ibt_class):
        """Test freeze_var_buffer_latest advances to next frame."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt

        def get_side_effect(frame, var_name):
            return frame * 10.0  # Return different value per frame

        mock_ibt.get.side_effect = get_side_effect

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"), playback_speed=1.0)
        source.startup()

        initial_frame = source.current_frame
        source.freeze_var_buffer_latest()

        # Verify
        assert source.current_frame == initial_frame + 1
        mock_ibt.get.assert_called()

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_getitem_returns_cached_value(self, mock_ibt_class):
        """Test __getitem__ returns cached telemetry values."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed", "RPM"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt

        def get_side_effect(frame, var_name):
            if var_name == "Speed":
                return 50.0
            elif var_name == "RPM":
                return 5000.0
            return 0.0

        mock_ibt.get.side_effect = get_side_effect

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.startup()
        source.freeze_var_buffer_latest()

        speed = source["Speed"]
        rpm = source["RPM"]

        # Verify
        assert speed == 50.0
        assert rpm == 5000.0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_playback_speed_affects_frame_advance(self, mock_ibt_class):
        """Test that playback_speed affects how many frames are advanced."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Test with 2x speed
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"), playback_speed=2.0)
        source.startup()

        initial_frame = source.current_frame
        source.freeze_var_buffer_latest()

        # Verify - should advance by 2 frames
        assert source.current_frame == initial_frame + 2

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_loop_enabled_wraps_to_beginning(self, mock_ibt_class):
        """Test that loop=True wraps playback to beginning."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"), loop=True)
        source.startup()

        # Advance to near the end
        source.current_frame = 9

        # Advance one more time
        source.freeze_var_buffer_latest()

        # Verify - should wrap to beginning
        assert source.current_frame == 0

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_loop_disabled_stops_at_end(self, mock_ibt_class):
        """Test that loop=False stops at the end."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 10
        mock_ibt_class.return_value = mock_ibt
        mock_ibt.get.return_value = 1.0

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"), loop=False)
        source.startup()

        # Advance to the end
        source.current_frame = 9

        # Try to advance beyond end
        source.freeze_var_buffer_latest()

        # Verify - should stay at last frame
        assert source.current_frame == 9

    @patch("racing_coach_client.collectors.sources.replay.irsdk.IBT")
    def test_get_playback_progress(self, mock_ibt_class):
        """Test playback progress calculation."""
        # Setup
        mock_ibt = MagicMock()
        mock_ibt.var_headers_names = ["Speed"]
        mock_ibt.get_all.return_value = [1.0] * 100
        mock_ibt_class.return_value = mock_ibt

        # Test
        source = ReplayTelemetrySource(file_path=Path("/fake/path.ibt"))
        source.startup()

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

    def test_open_and_read_ibt_file(self, ibt_file_path: Path):
        """Test opening and reading a real IBT file."""
        source = ReplayTelemetrySource(file_path=ibt_file_path)

        # Test startup
        source.startup()
        assert source.frame_count > 0
        assert source.current_frame == 0

        # Test reading a frame
        source.freeze_var_buffer_latest()
        assert source.current_frame == 1

        # Verify we can read telemetry values
        speed = source["Speed"]
        assert speed is not None
        assert isinstance(speed, (int, float))

        # Test shutdown
        source.shutdown()

    def test_playback_progression(self, ibt_file_path: Path):
        """Test that playback progresses through frames correctly."""
        source = ReplayTelemetrySource(file_path=ibt_file_path, playback_speed=1.0)
        source.startup()

        initial_frame = source.current_frame
        for i in range(5):
            source.freeze_var_buffer_latest()
            assert source.current_frame == initial_frame + i + 1

        source.shutdown()

    def test_read_multiple_telemetry_fields(self, ibt_file_path: Path):
        """Test reading various telemetry fields from a real IBT file."""
        source = ReplayTelemetrySource(file_path=ibt_file_path)
        source.startup()
        source.freeze_var_buffer_latest()

        # Test reading common telemetry fields
        fields_to_test = [
            "Speed",
            "RPM",
            "Throttle",
            "Brake",
            "Gear",
            "Lap",
            "LapDistPct",
        ]

        for field in fields_to_test:
            try:
                value = source[field]
                assert value is not None
            except KeyError:
                pytest.skip(f"Field {field} not available in this IBT file")

        source.shutdown()

    def test_playback_speed_double(self, ibt_file_path: Path):
        """Test that 2x playback speed advances twice as fast."""
        source = ReplayTelemetrySource(file_path=ibt_file_path, playback_speed=2.0)
        source.startup()

        initial_frame = source.current_frame
        source.freeze_var_buffer_latest()

        # Should advance by 2 frames
        assert source.current_frame == initial_frame + 2

        source.shutdown()

    def test_loop_wraps_playback(self, ibt_file_path: Path):
        """Test that loop=True wraps playback to the beginning."""
        source = ReplayTelemetrySource(file_path=ibt_file_path, loop=True)
        source.startup()

        # Jump to near the end
        source.current_frame = source.frame_count - 1

        # Advance past the end
        source.freeze_var_buffer_latest()

        # Should wrap to beginning
        assert source.current_frame == 0

        source.shutdown()
