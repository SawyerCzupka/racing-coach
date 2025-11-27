"""
Replay telemetry source implementation for IBT files.

This module provides a telemetry source that plays back recorded iRacing
telemetry from IBT files, with configurable playback speed and looping.
"""

import logging
import time
from pathlib import Path
from typing import Any

import irsdk

from .base import TelemetryConnectionError, TelemetryReadError

logger = logging.getLogger(__name__)

# iRacing records telemetry at 60Hz
DEFAULT_TELEMETRY_RATE_HZ = 60
DEFAULT_FRAME_TIME_SECONDS = 1.0 / DEFAULT_TELEMETRY_RATE_HZ


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
        _connected: Flag indicating if the file is open and ready.
        _last_freeze_time: Timestamp of last frame freeze (for timing).
        _current_buffer: Cached telemetry values from current frozen frame.
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
        self._connected: bool = False
        self._last_freeze_time: float = 0.0
        self._current_buffer: dict[str, Any] = {}
        self._var_names: list[str] = []
        self._end_of_file_logged: bool = False  # Flag to prevent log spam

    def startup(self) -> bool:
        """
        Open and initialize the IBT file for playback.

        Returns:
            bool: True if file opened successfully, False otherwise.

        Raises:
            TelemetryConnectionError: If file cannot be opened or is invalid.
        """
        if not self.file_path.exists():
            error_msg = f"IBT file not found: {self.file_path}"
            logger.error(error_msg)
            raise TelemetryConnectionError(error_msg)

        try:
            # Initialize IBT for frame-by-frame telemetry access
            self.ibt = irsdk.IBT()
            self.ibt.open(str(self.file_path))

            # Initialize IRSDK for session metadata access
            self.ir = irsdk.IRSDK()
            if not self.ir.startup(test_file=str(self.file_path)):
                raise TelemetryConnectionError(
                    f"Failed to load session data from IBT file: {self.file_path}"
                )

            # Get available variable names
            self._var_names = self.ibt.var_headers_names  # type: ignore

            # Determine total frames
            # IBT files don't directly expose frame count, so we need to infer it
            # by checking when get() returns None or trying get_all on a variable
            self.total_frames = self._determine_frame_count()

            if self.total_frames == 0:
                raise TelemetryConnectionError(f"IBT file appears to be empty: {self.file_path}")

            self.current_frame = 0
            self._connected = True
            self._last_freeze_time = time.time()
            self._end_of_file_logged = False

            logger.info(
                f"Opened IBT file: {self.file_path} "
                f"({self.total_frames} frames, {len(self._var_names)} variables)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to open IBT file {self.file_path}: {e}")
            # Clean up on failure
            if self.ibt:
                self.ibt.close()
                self.ibt = None
            if self.ir:
                self.ir.shutdown()
                self.ir = None
            raise TelemetryConnectionError(f"Failed to open IBT file: {e}") from e

    def shutdown(self) -> None:
        """
        Close the IBT file and clean up resources.
        """
        if self.ibt:
            self.ibt.close()
            logger.info(f"Closed IBT file: {self.file_path}")

        if self.ir:
            self.ir.shutdown()

        self._connected = False
        self.ibt = None
        self.ir = None
        self.current_frame = 0
        self._current_buffer.clear()

    def is_connected(self) -> bool:
        """
        Check if the IBT file is open and ready.

        Returns:
            bool: True if file is open and playback is active, False otherwise.
        """
        return self._connected and self.ibt is not None and self.ir is not None

    def freeze_var_buffer_latest(self) -> None:
        """
        Advance to the next frame and freeze the buffer.

        This method advances the playback to the next frame, respecting the
        configured playback speed, and caches all telemetry variables for
        consistent reads.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected() or not self.ibt:
            raise RuntimeError("freeze_var_buffer_latest() called while not connected")

        # Calculate sleep time to maintain playback speed
        current_time = time.time()
        elapsed = current_time - self._last_freeze_time
        target_frame_time = DEFAULT_FRAME_TIME_SECONDS / self.speed_multiplier
        sleep_time = target_frame_time - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        # Advance to next frame
        self.current_frame += 1

        # Handle end of file
        if self.current_frame >= self.total_frames:
            if self.loop:
                if not self._end_of_file_logged:
                    logger.debug(
                        f"Reached end of IBT file, looping back to start "
                        f"(frame {self.current_frame}/{self.total_frames})"
                    )
                self.current_frame = 0
                self._end_of_file_logged = False  # Reset for next loop
            else:
                if not self._end_of_file_logged:
                    logger.info(
                        f"Reached end of IBT file, stopping playback "
                        f"(frame {self.current_frame}/{self.total_frames})"
                    )
                    self._end_of_file_logged = True
                    self._connected = False  # Triggers SESSION_END via disconnect handling
                self.current_frame = self.total_frames - 1  # Stay on last frame

        # Cache all variables for this frame
        self._current_buffer.clear()
        for var_name in self._var_names:
            try:
                value = self.ibt.get(self.current_frame, var_name)
                self._current_buffer[var_name] = value
            except Exception as e:
                logger.warning(
                    f"Failed to read variable '{var_name}' at frame {self.current_frame}: {e}"
                )

        self._last_freeze_time = time.time()

    def __getitem__(self, key: str) -> Any:
        """
        Get a telemetry variable value from the current frozen frame.

        For session metadata (WeekendInfo, DriverInfo, etc.), this accesses
        the IRSDK instance. For telemetry variables, it reads from the IBT
        instance at the current frame.

        Args:
            key: The name of the telemetry variable or session metadata key.

        Returns:
            The value of the requested variable.

        Raises:
            RuntimeError: If called while not connected.
            KeyError: If the variable name is not found.
            TelemetryReadError: If reading the variable fails.
        """
        if not self.is_connected():
            raise RuntimeError("__getitem__() called while not connected")

        # Session metadata keys - use IRSDK instance
        if key in ["WeekendInfo", "DriverInfo", "SessionInfo", "QualifyResultsInfo", "CarSetup"]:
            if not self.ir:
                raise RuntimeError("IRSDK reader is not initialized")
            try:
                return self.ir[key]
            except Exception as e:
                raise TelemetryReadError(f"Failed to read session metadata '{key}': {e}") from e

        # Telemetry variables - use IBT instance with caching
        if key not in self._current_buffer:
            # Try to read it directly if not in cache
            if not self.ibt:
                raise RuntimeError("IBT reader is not initialized")

            try:
                value = self.ibt.get(self.current_frame, key)
                self._current_buffer[key] = value
                return value
            except Exception as e:
                raise TelemetryReadError(
                    f"Failed to read variable '{key}' at frame {self.current_frame}: {e}"
                ) from e

        return self._current_buffer[key]

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
            # Try 'SessionTime' first, fall back to first available variable
            test_var = "SessionTime" if "SessionTime" in self._var_names else self._var_names[0]
            all_values = self.ibt.get_all(test_var)

            if all_values is None:
                return 0

            # get_all returns a list/array of all values
            return len(all_values)

        except Exception as e:
            logger.error(f"Failed to determine frame count: {e}")
            raise TelemetryConnectionError(f"Could not determine frame count: {e}") from e

    def get_current_frame_index(self) -> int:
        """
        Get the current frame index being played.

        Returns:
            int: Current frame index (0-based).
        """
        return self.current_frame

    def get_total_frames(self) -> int:
        """
        Get the total number of frames in the file.

        Returns:
            int: Total frame count.
        """
        return self.total_frames

    def get_playback_progress(self) -> float:
        """
        Get the current playback progress as a percentage.

        Returns:
            float: Progress percentage (0.0 to 100.0).
        """
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100.0
