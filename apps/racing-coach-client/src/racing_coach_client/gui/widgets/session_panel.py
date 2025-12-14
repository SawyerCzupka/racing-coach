"""Session information panel widget."""

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel

from racing_coach_core.schemas.telemetry import SessionFrame


class SessionPanel(QGroupBox):
    """Panel displaying current session information."""

    def __init__(self) -> None:
        super().__init__("Session Info")
        layout = QFormLayout(self)

        self.track_label = QLabel("--")
        self.car_label = QLabel("--")
        self.session_type_label = QLabel("--")
        self.status_label = QLabel("Disconnected")

        # Style the status label
        self.status_label.setStyleSheet("color: gray;")

        layout.addRow("Track:", self.track_label)
        layout.addRow("Car:", self.car_label)
        layout.addRow("Session:", self.session_type_label)
        layout.addRow("Status:", self.status_label)

    def update_session(self, session: SessionFrame) -> None:
        """Update the panel with session information.

        Args:
            session: The session frame containing track, car, and session info
        """
        # Build track display with config if available
        track_display = session.track_name
        if session.track_config_name:
            track_display += f" ({session.track_config_name})"

        self.track_label.setText(track_display)
        self.car_label.setText(session.car_name)
        self.session_type_label.setText(session.session_type)
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")

    def clear_session(self) -> None:
        """Clear the session display when disconnected."""
        self.track_label.setText("--")
        self.car_label.setText("--")
        self.session_type_label.setText("--")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
