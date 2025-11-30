"""
Live telemetry source implementation for iRacing SDK.

This module provides a telemetry source that connects to a running iRacing
instance and streams real-time telemetry data.
"""

import logging
from datetime import datetime
from typing import Any

import irsdk
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame

from .base import TelemetryConnectionError

logger = logging.getLogger(__name__)

# Session metadata keys that should be included in get_session_data()
SESSION_DATA_KEYS = ["WeekendInfo", "DriverInfo", "SessionInfo", "QualifyResultsInfo", "CarSetup"]


class LiveTelemetrySource:
    """
    Live telemetry source that connects to iRacing SDK.

    This class manages the connection to a running iRacing instance and
    provides real-time telemetry data through the TelemetrySource interface.

    Attributes:
        ir: The iRacing SDK instance.
        _connected: Flag indicating current connection status.
        _started: Flag indicating if start() has been called.
    """

    def __init__(self) -> None:
        """Initialize the live telemetry source."""
        self.ir: irsdk.IRSDK | None = None
        self._connected: bool = False
        self._started: bool = False

    @property
    def is_connected(self) -> bool:
        """
        Check if currently connected to iRacing.

        Returns:
            bool: True if connected and ready, False otherwise.
        """
        return self._connected and self.ir is not None

    def start(self) -> bool:
        """
        Initialize connection to iRacing SDK.

        Returns:
            bool: True if connection established, False otherwise.

        Raises:
            TelemetryConnectionError: If connection fails critically.
        """
        if self._started:
            logger.warning("LiveTelemetrySource already started")
            return self.is_connected

        try:
            self.ir = irsdk.IRSDK()
            self._started = True
            return self._ensure_connected()
        except Exception as e:
            logger.error(f"Failed to initialize iRacing SDK: {e}")
            raise TelemetryConnectionError(f"SDK initialization failed: {e}") from e

    def stop(self) -> None:
        """
        Disconnect from iRacing SDK and clean up resources.
        """
        if self.ir:
            self.ir.shutdown()
            logger.info("iRacing SDK shutdown")

        self._connected = False
        self._started = False
        self.ir = None

    def collect_session_frame(self) -> SessionFrame:
        """
        Collect current session metadata from iRacing.

        Returns:
            SessionFrame containing track, car, and series information.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self._ensure_connected():
            raise RuntimeError("Cannot collect session frame: not connected to iRacing")

        assert self.ir is not None
        self.ir.freeze_var_buffer_latest()
        data = self.get_session_data()
        return SessionFrame.from_irsdk(data, datetime.now())

    def collect_telemetry_frame(self) -> TelemetryFrame:
        """
        Collect the latest telemetry frame from iRacing.

        Returns:
            TelemetryFrame containing current telemetry data.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self._ensure_connected():
            raise RuntimeError("Cannot collect telemetry frame: not connected to iRacing")

        assert self.ir is not None
        self.ir.freeze_var_buffer_latest()
        data = self.get_telemetry_data()
        return TelemetryFrame.from_irsdk(data, datetime.now())

    def get_telemetry_data(self) -> dict[str, Any]:
        """
        Return a frozen snapshot of telemetry variables.

        Note: This returns a wrapper that provides dict-like access to the
        frozen iRacing SDK buffer. Call freeze_var_buffer_latest() on the SDK
        before calling this method for consistent data.

        Returns:
            dict[str, Any]: Dictionary-like access to telemetry variables.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected or not self.ir:
            raise RuntimeError("get_telemetry_data() called while not connected to iRacing")

        # Return a dict-like wrapper around the frozen SDK buffer
        # The SDK already implements __getitem__, so we wrap it
        return _IRSDKDataWrapper(self.ir)

    def get_session_data(self) -> dict[str, Any]:
        """
        Return session metadata from iRacing.

        Returns:
            dict[str, Any]: Dictionary with session metadata (WeekendInfo, DriverInfo, etc.).

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected or not self.ir:
            raise RuntimeError("get_session_data() called while not connected to iRacing")

        # Return a dict-like wrapper for session data
        return _IRSDKDataWrapper(self.ir)

    def _ensure_connected(self) -> bool:
        """
        Internal method to ensure connection, with automatic reconnection.

        This handles the case where iRacing was restarted or connection dropped.

        Returns:
            bool: True if connected (or successfully reconnected), False otherwise.
        """
        if not self._started or not self.ir:
            return False

        # Check if we lost connection
        if self._connected and not (self.ir.is_initialized and self.ir.is_connected):
            self._connected = False
            self.ir.shutdown()
            logger.info("iRacing connection lost, will attempt reconnect")
            # Re-initialize for reconnection attempt
            self.ir = irsdk.IRSDK()

        # Attempt to connect if not connected
        if not self._connected:
            if self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
                self._connected = True
                logger.info("iRacing SDK connected")

        return self._connected


class _IRSDKDataWrapper:
    """
    Wrapper that provides dict-like access to iRacing SDK data.

    This allows the SDK instance to be used with TelemetryFrame.from_irsdk()
    and SessionFrame.from_irsdk() which expect __getitem__ access.
    """

    def __init__(self, ir: irsdk.IRSDK) -> None:
        self._ir = ir

    def __getitem__(self, key: str) -> Any:
        return self._ir[key]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self._ir[key]
        except (KeyError, TypeError):
            return default
