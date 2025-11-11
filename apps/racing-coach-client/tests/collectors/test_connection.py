"""Tests for iRacing connection management."""

from unittest.mock import MagicMock, patch

import pytest
from racing_coach_client.collectors.connection import iRacingConnectionManager


@pytest.mark.unit
class TestIRacingConnectionManager:
    """Unit tests for iRacingConnectionManager."""

    def test_initial_state(self) -> None:
        """Test that connection manager starts in disconnected state."""
        manager: iRacingConnectionManager = iRacingConnectionManager()
        assert manager.ir is None
        assert manager.ir_connected is False
        assert not manager.is_connected()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_connect_success(self, mock_irsdk_class: MagicMock) -> None:
        """Test successful connection to iRacing."""
        # Setup mock
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        # Test
        manager: iRacingConnectionManager = iRacingConnectionManager()
        result: bool = manager.connect()

        # Verify
        assert result is True
        assert manager.ir is mock_ir
        assert manager.ir_connected is True
        assert manager.is_connected()
        mock_ir.startup.assert_called_once()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_connect_failure_startup_fails(self, mock_irsdk_class: MagicMock) -> None:
        """Test connection failure when startup() returns False."""
        # Setup mock
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = False
        mock_irsdk_class.return_value = mock_ir

        # Test
        manager: iRacingConnectionManager = iRacingConnectionManager()
        result: bool = manager.connect()

        # Verify
        assert result is False
        assert not manager.ir_connected
        assert not manager.is_connected()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_connect_failure_not_initialized(self, mock_irsdk_class: MagicMock) -> None:
        """Test connection failure when SDK is not initialized."""
        # Setup mock
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = False
        mock_ir.is_connected = False
        mock_irsdk_class.return_value = mock_ir

        # Test
        manager: iRacingConnectionManager = iRacingConnectionManager()
        result: bool = manager.connect()

        # Verify
        assert result is False
        assert not manager.ir_connected

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_disconnect(self, mock_irsdk_class: MagicMock) -> None:
        """Test disconnecting from iRacing."""
        # Setup - first connect
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.connect()
        assert manager.ir_connected

        # Test disconnect
        manager.disconnect()

        # Verify
        assert manager.ir is None
        assert not manager.ir_connected
        assert not manager.is_connected()
        mock_ir.shutdown.assert_called_once()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_disconnect_when_not_connected(self, mock_irsdk_class: MagicMock) -> None:
        """Test that disconnect handles being called when not connected."""
        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.disconnect()  # Should not raise an error

        assert manager.ir is None
        assert not manager.ir_connected

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_get_ir_when_connected(self, mock_irsdk_class: MagicMock) -> None:
        """Test getting iRacing SDK instance when connected."""
        # Setup
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.connect()

        # Test
        ir = manager.get_ir()

        # Verify
        assert ir is mock_ir

    def test_get_ir_when_not_connected(self) -> None:
        """Test that get_ir raises error when not connected."""
        manager: iRacingConnectionManager = iRacingConnectionManager()

        with pytest.raises(RuntimeError, match="not connected to iRacing"):
            manager.get_ir()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_check_connection_detects_disconnect(self, mock_irsdk_class: MagicMock) -> None:
        """Test that connection manager detects when iRacing disconnects."""
        # Setup - first connect
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.connect()
        assert manager.ir_connected

        # Simulate disconnect
        mock_ir.is_initialized = False
        mock_ir.is_connected = False

        # Test
        result: bool = manager._check_connection()

        # Verify
        assert result is False
        assert not manager.ir_connected
        mock_ir.shutdown.assert_called_once()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_ensure_connected_when_not_connected(self, mock_irsdk_class: MagicMock) -> None:
        """Test ensure_connected connects when not connected."""
        # Setup
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        # Test
        manager: iRacingConnectionManager = iRacingConnectionManager()
        result: bool = manager.ensure_connected()

        # Verify
        assert result is True
        assert manager.ir_connected
        mock_ir.startup.assert_called_once()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_ensure_connected_when_already_connected(self, mock_irsdk_class: MagicMock) -> None:
        """Test ensure_connected checks connection when already connected."""
        # Setup - first connect
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.connect()
        mock_ir.startup.reset_mock()  # Reset the startup call count

        # Test
        result: bool = manager.ensure_connected()

        # Verify
        assert result is True
        assert manager.ir_connected
        # Should not call startup again since already connected
        mock_ir.startup.assert_not_called()

    @patch("racing_coach_client.collectors.connection.irsdk.IRSDK")
    def test_ensure_connected_reconnects_after_disconnect(self, mock_irsdk_class: MagicMock) -> None:
        """Test ensure_connected reconnects after detecting a disconnect."""
        # Setup - first connect
        mock_ir: MagicMock = MagicMock()
        mock_ir.startup.return_value = True
        mock_ir.is_initialized = True
        mock_ir.is_connected = True
        mock_irsdk_class.return_value = mock_ir

        manager: iRacingConnectionManager = iRacingConnectionManager()
        manager.connect()

        # Simulate disconnect
        mock_ir.is_initialized = False
        mock_ir.is_connected = False
        mock_ir.startup.reset_mock()

        # Simulate reconnect working
        mock_ir.startup.return_value = True

        # Test
        result: bool = manager.ensure_connected()

        # Verify - should have tried to startup again
        assert mock_ir.startup.called
