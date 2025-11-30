"""
Base abstractions for telemetry data sources.

This module defines the Protocol that all telemetry sources must implement,
allowing the TelemetryCollector to work with both live iRacing connections
and recorded telemetry file playback.
"""

from typing import Any, Protocol, runtime_checkable

from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame


@runtime_checkable
class TelemetrySource(Protocol):
    """
    Protocol defining the interface for telemetry data sources.

    This protocol allows the TelemetryCollector to work with different
    telemetry sources (live iRacing SDK, IBT file replay, mock sources, etc.)
    without knowing the implementation details.

    Sources encapsulate all logic for:
    - Connection management (live) or file handling (replay)
    - Frame construction from raw telemetry data
    - Timing/pacing of frame delivery
    """

    @property
    def is_connected(self) -> bool:
        """
        Check if the telemetry source is currently connected and ready.

        For live sources: True when iRacing SDK is connected.
        For replay sources: True when file is open and not exhausted.

        Returns:
            bool: True if connected and ready to provide data, False otherwise.
        """
        ...

    def start(self) -> bool:
        """
        Initialize and start the telemetry source.

        For live sources: Initialize SDK, attempt initial connection.
        For replay sources: Open file, determine frame count, initialize state.

        Returns:
            bool: True if initialization successful and source is ready.
                  False if initialization failed but source can retry.

        Raises:
            TelemetryConnectionError: For unrecoverable initialization failures.
        """
        ...

    def stop(self) -> None:
        """
        Stop the source and release all resources.

        After calling stop(), the source should not be reused.
        """
        ...

    def collect_session_frame(self) -> SessionFrame:
        """
        Collect current session metadata.

        Returns:
            SessionFrame containing track, car, and series information.

        Raises:
            RuntimeError: If called while not connected.
            TelemetryReadError: If session data cannot be read.
        """
        ...

    def collect_telemetry_frame(self) -> TelemetryFrame:
        """
        Collect the next telemetry frame.

        For live sources: Freezes latest buffer, constructs frame.
        For replay sources: Advances to next frame (respecting timing), constructs frame.

        Returns:
            TelemetryFrame containing current telemetry data.

        Raises:
            RuntimeError: If called while not connected.
            TelemetryReadError: If telemetry data cannot be read.
        """
        ...

    def get_telemetry_data(self) -> dict[str, Any]:
        """
        Return a frozen snapshot of all telemetry variables.

        This method freezes the buffer (if applicable) and returns a dictionary
        containing all telemetry variable values. Safe to read multiple values
        without race conditions.

        Returns:
            dict[str, Any]: Dictionary mapping variable names to values.

        Raises:
            RuntimeError: If called while not connected.
        """
        ...

    def get_session_data(self) -> dict[str, Any]:
        """
        Return session metadata.

        Returns a dictionary containing session info like WeekendInfo,
        DriverInfo, SessionInfo, etc.

        Returns:
            dict[str, Any]: Dictionary with session metadata.

        Raises:
            RuntimeError: If called while not connected.
        """
        ...


class TelemetrySourceError(Exception):
    """Base exception for telemetry source errors."""

    pass


class TelemetryConnectionError(TelemetrySourceError):
    """Exception raised when connection to telemetry source fails."""

    pass


class TelemetryReadError(TelemetrySourceError):
    """Exception raised when reading telemetry data fails."""

    pass
