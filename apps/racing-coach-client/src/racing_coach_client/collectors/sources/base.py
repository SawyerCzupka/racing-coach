"""
Base abstractions for telemetry data sources.

This module defines the Protocol that all telemetry sources must implement,
allowing the TelemetryCollector to work with both live iRacing connections
and recorded telemetry file playback.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TelemetrySource(Protocol):
    """
    Protocol defining the interface for telemetry data sources.

    This protocol allows the TelemetryCollector to work with different
    telemetry sources (live iRacing SDK, IBT file replay, mock sources, etc.)
    without knowing the implementation details.
    """

    def startup(self) -> bool:
        """
        Initialize and start the telemetry source.

        Returns:
            bool: True if startup successful, False otherwise.
        """
        ...

    def shutdown(self) -> None:
        """
        Cleanly shutdown the telemetry source and release resources.
        """
        ...

    def is_connected(self) -> bool:
        """
        Check if the telemetry source is currently connected and ready.

        Returns:
            bool: True if connected and ready to provide data, False otherwise.
        """
        ...

    def freeze_var_buffer_latest(self) -> None:
        """
        Freeze the variable buffer to ensure consistent reads.

        This method ensures that all subsequent reads of telemetry variables
        come from the same snapshot in time, preventing race conditions.
        """
        ...

    def __getitem__(self, key: str) -> Any:
        """
        Get a telemetry variable value by name.

        Args:
            key: The name of the telemetry variable (e.g., 'Speed', 'RPM').

        Returns:
            The value of the requested telemetry variable.

        Raises:
            KeyError: If the variable name is not found.
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
