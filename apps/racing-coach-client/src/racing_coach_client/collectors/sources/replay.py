"""
Replay telemetry source implementation for IBT files.

This module provides a telemetry source that plays back recorded iRacing
telemetry from IBT files, with configurable playback speed and looping.
"""

import contextlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import irsdk  # pyright: ignore[reportMissingTypeStubs]
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame

from .base import TelemetryConnectionError

logger = logging.getLogger(__name__)

# iRacing records telemetry at 60Hz
DEFAULT_TELEMETRY_RATE_HZ = 60
DEFAULT_FRAME_TIME_SECONDS = 1.0 / DEFAULT_TELEMETRY_RATE_HZ

# Session metadata keys
SESSION_DATA_KEYS = ["WeekendInfo", "DriverInfo", "SessionInfo", "QualifyResultsInfo", "CarSetup"]


class ReplayTelemetrySource:
    """
    Replay telemetry source that plays back IBT files.

    This class reads telemetry data from iRacing's .ibt telemetry files
    and plays them back at a configurable speed, simulating real-time
    telemetry collection for testing and development.

    Attributes:
        file_path: Path to the IBT telemetry file.
        speed_multiplier: Playback speed (1.0 = real-time, 2.0 = 2x speed).
        loop: Whether to loop playback when reaching the end.
        ibt: The IBT file reader instance.
        current_frame: Current frame index being read.
        total_frames: Total number of frames in the file.
    """

    def __init__(
        self,
        file_path: str | Path,
        speed_multiplier: float = 1.0,
        loop: bool = False,
    ) -> None:
        """
        Initialize the replay telemetry source.

        Args:
            file_path: Path to the IBT telemetry file to replay.
            speed_multiplier: Playback speed multiplier (1.0 = real-time).
            loop: If True, loop playback when reaching the end of the file.

        Raises:
            ValueError: If speed_multiplier is <= 0.
        """
        if speed_multiplier <= 0:
            raise ValueError("speed_multiplier must be greater than 0")

        self.file_path = Path(file_path)
        self.speed_multiplier = speed_multiplier
        self.loop = loop

        self.ibt: irsdk.IBT | None = None
        self.ir: irsdk.IRSDK | None = None  # For accessing session metadata
        self.current_frame: int = 0
        self.total_frames: int = 0
        self._started: bool = False
        self._exhausted: bool = False
        self._last_frame_time: float = 0.0
        self._current_buffer: dict[str, Any] = {}
        self._var_names: list[str] = []

    @property
    def is_connected(self) -> bool:
        """
        Check if the IBT file is open and ready.

        Returns False when file is exhausted (unless looping).

        Returns:
            bool: True if file is open and playback is active, False otherwise.
        """
        return (
            self._started and not self._exhausted and self.ibt is not None and self.ir is not None
        )

    def start(self) -> bool:
        """
        Open and initialize the IBT file for playback.

        Returns:
            bool: True if file opened successfully, False otherwise.

        Raises:
            TelemetryConnectionError: If file cannot be opened or is invalid.
        """
        if self._started:
            logger.warning("ReplayTelemetrySource already started")
            return self.is_connected

        if not self.file_path.exists():
            error_msg = f"IBT file not found: {self.file_path}"
            logger.error(error_msg)
            raise TelemetryConnectionError(error_msg)

        try:
            # Initialize IBT for frame-by-frame telemetry access
            self.ibt = irsdk.IBT()
            self.ibt.open(str(self.file_path))  # pyright: ignore[reportUnknownMemberType]

            # Initialize IRSDK for session metadata access
            self.ir = irsdk.IRSDK()
            if not self.ir.startup(test_file=str(self.file_path)):  # pyright: ignore[reportUnknownMemberType]
                raise TelemetryConnectionError(
                    f"Failed to load session data from IBT file: {self.file_path}"
                )

            # Get available variable names
            self._var_names = self.ibt.var_headers_names  # type: ignore

            # Determine total frames
            self.total_frames = self._determine_frame_count()

            if self.total_frames == 0:
                raise TelemetryConnectionError(f"IBT file appears to be empty: {self.file_path}")

            self.current_frame = 0
            self._started = True
            self._exhausted = False
            self._last_frame_time = time.time()

            # Cache the first frame so first collect_telemetry_frame() returns frame 0
            self._cache_current_frame()

            logger.info(
                f"Opened IBT file: {self.file_path} "
                f"({self.total_frames} frames, {len(self._var_names)} variables)"
            )
            return True

        except TelemetryConnectionError:
            self._cleanup()
            raise
        except Exception as e:
            logger.error(f"Failed to open IBT file {self.file_path}: {e}")
            self._cleanup()
            raise TelemetryConnectionError(f"Failed to open IBT file: {e}") from e

    def stop(self) -> None:
        """
        Close the IBT file and clean up resources.
        """
        self._cleanup()
        logger.info(f"Closed IBT file: {self.file_path}")

    def collect_session_frame(self) -> SessionFrame:
        """
        Collect session metadata from the IBT file.

        Returns:
            SessionFrame containing track, car, and series information.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Cannot collect session frame: replay source not ready")

        data = self.get_session_data()
        return SessionFrame.from_irsdk(data, datetime.now())

    def collect_telemetry_frame(self) -> TelemetryFrame:
        """
        Collect the next telemetry frame, respecting playback timing.

        This method handles:
        - Timing/pacing based on speed_multiplier
        - Frame advancement
        - Loop handling
        - EOF detection

        Returns:
            TelemetryFrame containing current telemetry data.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Cannot collect telemetry frame: replay source not ready")

        # Apply timing delay based on playback speed
        self._apply_playback_timing()

        # Create frame from current cached data
        data = self.get_telemetry_data()
        frame = TelemetryFrame.from_irsdk(data, datetime.now())

        # Advance to next frame for next call
        self._advance_frame()

        return frame

    def get_telemetry_data(self) -> dict[str, Any]:
        """
        Return the current cached telemetry data.

        Returns:
            dict[str, Any]: Dictionary of telemetry variable names to values.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected:
            raise RuntimeError("get_telemetry_data() called while not connected")

        return self._current_buffer

    def get_session_data(self) -> dict[str, Any]:
        """
        Return session metadata from the IBT file.

        Returns:
            dict[str, Any]: Dictionary with session metadata (WeekendInfo, DriverInfo, etc.).

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected or not self.ir:
            raise RuntimeError("get_session_data() called while not connected")

        # Return a wrapper that provides dict-like access to session data
        return _IRSDKSessionDataWrapper(self.ir)

    def _apply_playback_timing(self) -> None:
        """Apply timing delay to maintain playback speed."""
        current_time = time.time()
        elapsed = current_time - self._last_frame_time
        target_frame_time = DEFAULT_FRAME_TIME_SECONDS / self.speed_multiplier
        sleep_time = target_frame_time - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        self._last_frame_time = time.time()

    def _advance_frame(self) -> None:
        """Advance to the next frame, handling EOF and looping."""
        self.current_frame += 1

        if self.current_frame >= self.total_frames:
            if self.loop:
                self.current_frame = 0
                logger.debug("Replay looped back to beginning")
            else:
                self.current_frame = self.total_frames - 1
                self._exhausted = True
                logger.info("Reached end of IBT file")
                return

        self._cache_current_frame()

    def _cache_current_frame(self) -> None:
        """Cache all telemetry variables for current frame."""
        if not self.ibt:
            return

        self._current_buffer.clear()
        for var_name in self._var_names:
            try:
                self._current_buffer[var_name] = self.ibt.get(self.current_frame, var_name)  # pyright: ignore[reportUnknownMemberType]
            except Exception as e:
                logger.warning(f"Failed to cache '{var_name}' at frame {self.current_frame}: {e}")

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.ibt:
            with contextlib.suppress(ValueError):
                self.ibt.close()

            self.ibt = None
        if self.ir:
            with contextlib.suppress(ValueError):
                self.ir.shutdown()
            self.ir = None
        self._started = False
        self._exhausted = True
        self._current_buffer.clear()

    def _determine_frame_count(self) -> int:
        """
        Determine the total number of frames in the IBT file.

        This is done by reading a sample variable using get_all() and
        counting the number of values returned.

        Returns:
            int: The total number of frames in the file.

        Raises:
            TelemetryConnectionError: If frame count cannot be determined.
        """
        if not self.ibt or not self._var_names:
            raise TelemetryConnectionError("Cannot determine frame count: IBT not initialized")

        try:
            # Use a common variable that should exist in all files
            test_var = "SessionTime" if "SessionTime" in self._var_names else self._var_names[0]
            all_values = self.ibt.get_all(test_var)  # pyright: ignore[reportUnknownMemberType]

            if all_values is None:
                return 0

            return len(all_values)

        except Exception as e:
            logger.error(f"Failed to determine frame count: {e}")
            raise TelemetryConnectionError(f"Could not determine frame count: {e}") from e

    # Utility methods for introspection
    def get_current_frame_index(self) -> int:
        """Get the current frame index being played."""
        return self.current_frame

    def get_total_frames(self) -> int:
        """Get the total number of frames in the file."""
        return self.total_frames

    def get_playback_progress(self) -> float:
        """Get the current playback progress as a percentage (0.0 to 100.0)."""
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100.0


class _IRSDKSessionDataWrapper:
    """
    Wrapper that provides dict-like access to iRacing SDK session data.

    This allows the SDK instance to be used with SessionFrame.from_irsdk()
    which expects __getitem__ access.
    """

    def __init__(self, ir: irsdk.IRSDK) -> None:
        self._ir = ir

    def __getitem__(self, key: str) -> Any:
        return self._ir[key]  # pyright: ignore[reportUnknownVariableType]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self._ir[key]  # pyright: ignore[reportUnknownVariableType]
        except (KeyError, TypeError):
            return default
