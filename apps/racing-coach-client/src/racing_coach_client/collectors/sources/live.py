"""
Live telemetry source implementation for iRacing SDK.

This module provides a telemetry source that connects to a running iRacing
instance and streams real-time telemetry data.
"""

import logging
from typing import Any

import irsdk

from .base import TelemetryConnectionError, TelemetrySource

logger = logging.getLogger(__name__)


class LiveTelemetrySource:
    """
    Live telemetry source that connects to iRacing SDK.

    This class manages the connection to a running iRacing instance and
    provides real-time telemetry data through the TelemetrySource interface.

    Attributes:
        ir: The iRacing SDK instance.
        _connected: Flag indicating current connection status.
    """

    def __init__(self) -> None:
        """Initialize the live telemetry source."""
        self.ir: irsdk.IRSDK | None = None
        self._connected: bool = False

    def startup(self) -> bool:
        """
        Initialize connection to iRacing SDK.

        Returns:
            bool: True if connection established, False otherwise.

        Raises:
            TelemetryConnectionError: If connection fails critically.
        """
        try:
            self.ir = irsdk.IRSDK()
            return self._check_connection()
        except Exception as e:
            logger.error(f"Failed to initialize iRacing SDK: {e}")
            raise TelemetryConnectionError(f"SDK initialization failed: {e}") from e

    def shutdown(self) -> None:
        """
        Disconnect from iRacing SDK and clean up resources.
        """
        if self.ir:
            self.ir.shutdown()
            logger.info("iRacing SDK shutdown")

        self._connected = False
        self.ir = None

    def is_connected(self) -> bool:
        """
        Check if currently connected to iRacing.

        Returns:
            bool: True if connected and ready, False otherwise.
        """
        return self._connected and self.ir is not None

    def ensure_connected(self) -> bool:
        """
        Ensure connection is active, attempt to reconnect if needed.

        This method checks the current connection status and attempts to
        reconnect if the connection has been lost.

        Returns:
            bool: True if connected (or successfully reconnected), False otherwise.
        """
        if not self.is_connected():
            return self.startup()

        return self._check_connection()

    def freeze_var_buffer_latest(self) -> None:
        """
        Freeze the variable buffer to the latest available data.

        This ensures all subsequent variable reads come from the same
        telemetry snapshot, preventing inconsistent data.

        Raises:
            RuntimeError: If called while not connected.
        """
        if not self.is_connected() or not self.ir:
            raise RuntimeError("freeze_var_buffer_latest() called while not connected to iRacing")

        self.ir.freeze_var_buffer_latest()

    def __getitem__(self, key: str) -> Any:
        """
        Get a telemetry variable value.

        Args:
            key: The name of the telemetry variable.

        Returns:
            The value of the requested variable.

        Raises:
            RuntimeError: If called while not connected.
            KeyError: If the variable name is not found.
        """
        if not self.is_connected() or not self.ir:
            raise RuntimeError("__getitem__() called while not connected to iRacing")

        return self.ir[key]

    def _check_connection(self) -> bool:
        """
        Internal method to check and update connection status.

        This method verifies the iRacing SDK connection state and updates
        the internal connection flag accordingly.

        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.ir:
            return False

        # Check if we were connected but lost connection
        if self._connected and not (self.ir.is_initialized and self.ir.is_connected):
            self._connected = False
            self.ir.shutdown()
            logger.info("iRacing SDK disconnected")
            return False

        # Check if we're not connected but iRacing is available
        if (
            not self._connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self._connected = True
            logger.info("iRacing SDK connected")
            return True

        return self._connected
