"""Upload status panel widget with statistics and activity log."""

from datetime import datetime

from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QVBoxLayout


class UploadPanel(QGroupBox):
    """Panel displaying upload statistics and recent activity."""

    MAX_LOG_ENTRIES = 50

    def __init__(self) -> None:
        super().__init__("Upload Status")
        layout = QVBoxLayout(self)

        # Statistics row
        self.stats_label = QLabel("Laps: 0 uploaded, 0 failed | Metrics: 0 uploaded, 0 failed")
        self.stats_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.stats_label)

        # Recent activity log
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(200)
        layout.addWidget(self.log_list)

        # Counters
        self.laps_uploaded = 0
        self.laps_failed = 0
        self.metrics_uploaded = 0
        self.metrics_failed = 0

    def add_lap_success(self, lap_number: int) -> None:
        """Record a successful lap upload.

        Args:
            lap_number: The lap number that was uploaded
        """
        self.laps_uploaded += 1
        self._add_log_entry(f"Lap {lap_number} telemetry uploaded", success=True)
        self._update_stats()

    def add_lap_failure(self, lap_number: int, error: str | None = None) -> None:
        """Record a failed lap upload.

        Args:
            lap_number: The lap number that failed to upload
            error: Optional error message
        """
        self.laps_failed += 1
        message = f"Lap {lap_number} telemetry failed"
        if error:
            message += f": {error[:50]}"  # Truncate long errors
        self._add_log_entry(message, success=False)
        self._update_stats()

    def add_metrics_success(self, lap_number: int) -> None:
        """Record a successful metrics upload.

        Args:
            lap_number: The lap number whose metrics were uploaded
        """
        self.metrics_uploaded += 1
        self._add_log_entry(f"Lap {lap_number} metrics uploaded", success=True)
        self._update_stats()

    def add_metrics_failure(self, lap_number: int, error: str | None = None) -> None:
        """Record a failed metrics upload.

        Args:
            lap_number: The lap number whose metrics failed to upload
            error: Optional error message
        """
        self.metrics_failed += 1
        message = f"Lap {lap_number} metrics failed"
        if error:
            message += f": {error[:50]}"  # Truncate long errors
        self._add_log_entry(message, success=False)
        self._update_stats()

    def _add_log_entry(self, message: str, *, success: bool) -> None:
        """Add an entry to the activity log.

        Args:
            message: The log message
            success: Whether this was a success or failure
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "[OK]" if success else "[FAIL]"
        self.log_list.insertItem(0, f"{timestamp} {icon} {message}")

        # Trim old entries
        while self.log_list.count() > self.MAX_LOG_ENTRIES:
            self.log_list.takeItem(self.log_list.count() - 1)

    def _update_stats(self) -> None:
        """Update the statistics label."""
        self.stats_label.setText(
            f"Laps: {self.laps_uploaded} uploaded, {self.laps_failed} failed | "
            f"Metrics: {self.metrics_uploaded} uploaded, {self.metrics_failed} failed"
        )

    def reset_stats(self) -> None:
        """Reset all statistics and clear the log."""
        self.laps_uploaded = 0
        self.laps_failed = 0
        self.metrics_uploaded = 0
        self.metrics_failed = 0
        self.log_list.clear()
        self._update_stats()
