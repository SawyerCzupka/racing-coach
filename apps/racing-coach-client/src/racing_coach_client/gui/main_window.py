"""Main application window for Racing Coach GUI."""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QStatusBar, QVBoxLayout, QWidget
from racing_coach_core.schemas.events import (
    LapUploadResult,
    MetricsUploadResult,
    SessionEnd,
    SessionStart,
)

from .bridge import EventBridge
from .widgets import SessionPanel, UploadPanel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, bridge: EventBridge) -> None:
        super().__init__()
        self.bridge = bridge

        self.setWindowTitle("Racing Coach")
        self.setMinimumSize(500, 400)

        # Central widget with panels
        central = QWidget()
        layout = QVBoxLayout(central)

        self.session_panel = SessionPanel()
        self.upload_panel = UploadPanel()

        layout.addWidget(self.session_panel)
        layout.addWidget(self.upload_panel)
        layout.addStretch()  # Push panels to top

        self.setCentralWidget(central)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)

        # Connect bridge signals to slots
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect EventBridge signals to handler slots."""
        self.bridge.session_started.connect(self._on_session_started)
        self.bridge.session_ended.connect(self._on_session_ended)
        self.bridge.lap_uploaded.connect(self._on_lap_uploaded)
        self.bridge.lap_upload_failed.connect(self._on_lap_upload_failed)
        self.bridge.metrics_uploaded.connect(self._on_metrics_uploaded)
        self.bridge.metrics_upload_failed.connect(self._on_metrics_upload_failed)

    @Slot(object)
    def _on_session_started(self, data: SessionStart) -> None:
        """Handle session start event."""
        self.session_panel.update_session(data.SessionFrame)
        self.status_bar.showMessage(
            f"Connected: {data.SessionFrame.track_name} - {data.SessionFrame.car_name}"
        )

    @Slot(object)
    def _on_session_ended(self, data: SessionEnd) -> None:
        """Handle session end event."""
        self.session_panel.clear_session()
        self.status_bar.showMessage("Session ended")

    @Slot(object)
    def _on_lap_uploaded(self, data: LapUploadResult) -> None:
        """Handle lap upload success."""
        self.upload_panel.add_lap_success(data.lap_number)

    @Slot(object)
    def _on_lap_upload_failed(self, data: LapUploadResult) -> None:
        """Handle lap upload failure."""
        self.upload_panel.add_lap_failure(data.lap_number, data.error_message)

    @Slot(object)
    def _on_metrics_uploaded(self, data: MetricsUploadResult) -> None:
        """Handle metrics upload success."""
        self.upload_panel.add_metrics_success(data.lap_number)

    @Slot(object)
    def _on_metrics_upload_failed(self, data: MetricsUploadResult) -> None:
        """Handle metrics upload failure."""
        self.upload_panel.add_metrics_failure(data.lap_number, data.error_message)
