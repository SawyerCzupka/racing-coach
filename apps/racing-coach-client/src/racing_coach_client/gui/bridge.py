"""EventBus-to-Qt signal bridge for thread-safe GUI updates.

This module provides the EventBridge class that subscribes to EventBus events
and emits Qt signals, enabling safe cross-thread communication between the
telemetry collection thread and the GUI thread.
"""

import logging

from PySide6.QtCore import QObject, Signal

from racing_coach_core.events import EventBus, Handler, HandlerContext, SystemEvents
from racing_coach_core.schemas.events import (
    LapUploadResult,
    MetricsUploadResult,
    SessionEnd,
    SessionStart,
)

logger = logging.getLogger(__name__)


class EventBridge(QObject):
    """Bridge between EventBus events and Qt signals.

    This class registers handlers with the EventBus and emits Qt signals
    when events are received. Qt signals are thread-safe and can be
    connected to slots in the GUI thread.
    """

    # Qt Signals - emitted from handler threads, received in GUI thread
    session_started = Signal(object)  # SessionStart data
    session_ended = Signal(object)  # SessionEnd data
    lap_uploaded = Signal(object)  # LapUploadResult data
    lap_upload_failed = Signal(object)  # LapUploadResult data
    metrics_uploaded = Signal(object)  # MetricsUploadResult data
    metrics_upload_failed = Signal(object)  # MetricsUploadResult data

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers with the EventBus."""
        handlers = [
            Handler(SystemEvents.SESSION_START, self._on_session_start),
            Handler(SystemEvents.SESSION_END, self._on_session_end),
            Handler(SystemEvents.LAP_UPLOAD_SUCCESS, self._on_lap_upload_success),
            Handler(SystemEvents.LAP_UPLOAD_FAILED, self._on_lap_upload_failed),
            Handler(SystemEvents.METRICS_UPLOAD_SUCCESS, self._on_metrics_upload_success),
            Handler(SystemEvents.METRICS_UPLOAD_FAILED, self._on_metrics_upload_failed),
        ]
        self.event_bus.register_handlers(handlers)
        logger.info("EventBridge handlers registered")

    def _on_session_start(self, context: HandlerContext[SessionStart]) -> None:
        """Handle session start event."""
        self.session_started.emit(context.event.data)

    def _on_session_end(self, context: HandlerContext[SessionEnd]) -> None:
        """Handle session end event."""
        self.session_ended.emit(context.event.data)

    def _on_lap_upload_success(self, context: HandlerContext[LapUploadResult]) -> None:
        """Handle lap upload success event."""
        self.lap_uploaded.emit(context.event.data)

    def _on_lap_upload_failed(self, context: HandlerContext[LapUploadResult]) -> None:
        """Handle lap upload failure event."""
        self.lap_upload_failed.emit(context.event.data)

    def _on_metrics_upload_success(self, context: HandlerContext[MetricsUploadResult]) -> None:
        """Handle metrics upload success event."""
        self.metrics_uploaded.emit(context.event.data)

    def _on_metrics_upload_failed(self, context: HandlerContext[MetricsUploadResult]) -> None:
        """Handle metrics upload failure event."""
        self.metrics_upload_failed.emit(context.event.data)
