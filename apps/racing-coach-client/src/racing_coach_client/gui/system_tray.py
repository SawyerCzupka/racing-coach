"""System tray icon and menu for Racing Coach."""

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTrayManager(QSystemTrayIcon):
    """System tray icon with context menu and notifications."""

    def __init__(self, parent: QSystemTrayIcon | None = None) -> None:
        super().__init__(parent)

        # Set icon - use a built-in icon as fallback
        # On Windows, we could load a custom icon from resources
        icon = QIcon.fromTheme("applications-games")
        if icon.isNull():
            # Fallback to another common icon
            icon = QIcon.fromTheme("preferences-system")
        self.setIcon(icon)
        self.setToolTip("Racing Coach")

        # Create context menu
        menu = QMenu()

        self.show_action = QAction("Show Window", menu)
        menu.addAction(self.show_action)

        menu.addSeparator()

        self.quit_action = QAction("Quit", menu)
        menu.addAction(self.quit_action)

        self.setContextMenu(menu)

        # Double-click to show window
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_action.trigger()

    def notify(
        self,
        title: str,
        message: str,
        icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration_ms: int = 3000,
    ) -> None:
        """Show a system tray notification.

        Args:
            title: Notification title
            message: Notification message body
            icon_type: Icon to display (Information, Warning, Critical)
            duration_ms: How long to show the notification (milliseconds)
        """
        self.showMessage(title, message, icon_type, duration_ms)
