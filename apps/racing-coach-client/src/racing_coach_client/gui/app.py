"""Main GUI application entry point for Racing Coach."""

import logging
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from racing_coach_client.app import RacingCoachClient
from racing_coach_client.config import settings
from racing_coach_client.logging_config import setup_logging

from .bridge import EventBridge
from .main_window import MainWindow
from .system_tray import SystemTrayManager

logger = logging.getLogger(__name__)


class RacingCoachGUIApp:
    """Main GUI application coordinator.

    This class integrates the core RacingCoachClient with a PySide6 GUI,
    using Qt signals to bridge EventBus events to the GUI thread safely.
    """

    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Racing Coach")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

        # Initialize the core client (event bus, collector, handlers)
        self.client = RacingCoachClient()

        # Create the event bridge for thread-safe GUI updates
        self.bridge = EventBridge(self.client.event_bus)

        # Create GUI components
        self.main_window = MainWindow(self.bridge)
        self.tray = SystemTrayManager()

        # Connect tray signals
        self.tray.show_action.triggered.connect(self._show_window)
        self.tray.quit_action.triggered.connect(self._quit)

        # Connect bridge signals to tray notifications
        self._setup_notifications()

        # Override main window close to minimize to tray
        self.main_window.closeEvent = self._on_close_event  # type: ignore[method-assign]

        # Handle system signals gracefully
        self._setup_signal_handlers()

        logger.info("Racing Coach GUI initialized")

    def _setup_notifications(self) -> None:
        """Configure which events trigger system notifications."""
        self.bridge.session_started.connect(
            lambda data: self.tray.notify(
                "Session Started",
                f"{data.SessionFrame.track_name} - {data.SessionFrame.car_name}",
            )
        )
        self.bridge.session_ended.connect(
            lambda data: self.tray.notify("Session Ended", "iRacing session has ended")
        )
        self.bridge.lap_upload_failed.connect(
            lambda data: self.tray.notify(
                "Upload Failed",
                f"Lap {data.lap_number}: {data.error_message or 'Unknown error'}",
                QSystemTrayIcon.MessageIcon.Warning,
            )
        )
        self.bridge.metrics_upload_failed.connect(
            lambda data: self.tray.notify(
                "Metrics Upload Failed",
                f"Lap {data.lap_number}: {data.error_message or 'Unknown error'}",
                QSystemTrayIcon.MessageIcon.Warning,
            )
        )

    def _show_window(self) -> None:
        """Show and raise the main window."""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _quit(self) -> None:
        """Shutdown the application."""
        logger.info("Quit requested, shutting down...")
        self.client.shutdown()
        self.app.quit()

    def _on_close_event(self, event) -> None:  # type: ignore[no-untyped-def]
        """Handle window close - minimize to tray instead of quitting."""
        event.ignore()
        self.main_window.hide()
        self.tray.notify(
            "Racing Coach",
            "Running in background. Right-click tray icon to quit.",
            QSystemTrayIcon.MessageIcon.Information,
        )

    def _setup_signal_handlers(self) -> None:
        """Handle Ctrl+C and other signals gracefully in Qt.

        Qt doesn't process Python signals unless the event loop is active.
        We use a timer to periodically check for signals.
        """
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(lambda: None)  # Just wake up the event loop
        self.signal_timer.start(500)

        def signal_handler(signum: int, frame) -> None:  # type: ignore[no-untyped-def]
            logger.info(f"Signal {signum} received, initiating shutdown...")
            self._quit()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self) -> int:
        """Start the application.

        Returns:
            Exit code from Qt event loop
        """
        logger.info("Starting Racing Coach GUI...")

        # Start telemetry collection
        self.client.collector.start()

        # Show window and tray
        self.main_window.show()
        self.tray.show()

        # Enter Qt event loop (blocks until quit)
        return self.app.exec()


def main() -> None:
    """Entry point for the GUI application."""
    # Configure logging based on settings
    setup_logging(
        level=settings.LOG_LEVEL,
        use_color=settings.LOG_COLOR,
        show_module=settings.LOG_SHOW_MODULE,
    )

    app = RacingCoachGUIApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
