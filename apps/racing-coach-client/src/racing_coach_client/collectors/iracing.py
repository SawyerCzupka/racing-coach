"""
Telemetry collector class for iRacing.

This module provides the main telemetry collection loop that works with
any TelemetrySource implementation (live or replay).
"""

import logging
import threading

from racing_coach_core.events import Event, EventBus, SessionRegistry, SystemEvents
from racing_coach_core.schemas.events import SessionEnd, SessionStart, TelemetryAndSessionId
from racing_coach_core.schemas.telemetry import SessionFrame

from .sources import TelemetrySource

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """
    Collects telemetry data from a source and publishes events.

    This class manages the collection loop that reads telemetry data from
    any TelemetrySource implementation and publishes it to the event bus
    for processing by handlers.

    The collector runs in a separate thread. Frame construction, timing,
    and reconnection logic are handled by the source implementations.

    Attributes:
        source: The telemetry data source (live or replay).
        event_bus: Event bus for publishing telemetry events.
        current_session: Current session metadata.
    """

    def __init__(
        self, event_bus: EventBus, source: TelemetrySource, session_registry: SessionRegistry
    ) -> None:
        """
        Initialize the telemetry collector.

        Args:
            event_bus: Event bus for publishing telemetry events.
            source: Telemetry source to collect data from.
            session_registry: Registry for tracking current session state.
        """
        self.source = source
        self.event_bus = event_bus
        self.session_registry = session_registry

        self._running: bool = False
        self._collection_thread: threading.Thread | None = None

        # Current session metadata with unique UUID
        self.current_session: SessionFrame | None = None

        self._num_published_events: int = 0

    def start(self) -> None:
        """
        Start the telemetry collector thread.

        Spawns a new daemon thread that runs the collection loop.
        """
        if self._running:
            logger.warning("Telemetry collector is already running")
            return

        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            name="TelemetryCollectorThread",
            daemon=True,
        )
        self._collection_thread.start()
        logger.info("Telemetry collector thread started")

    def stop(self) -> None:
        """
        Stop the telemetry collector.

        Signals the collection thread to stop and shuts down the telemetry source.
        """
        logger.info("Stopping telemetry collector")
        self._running = False
        self.source.stop()

    def _collection_loop(self) -> None:
        """
        Main loop for collecting telemetry data.

        This method runs in a separate thread and continuously collects telemetry
        data from the source until stopped or the source disconnects.
        """
        # Initialize the telemetry source
        if not self.source.start():
            logger.error("Failed to start telemetry source")
            self._running = False
            return

        # Collect the initial session frame
        try:
            self.current_session = self.source.collect_session_frame()
            self.session_registry.start_session(self.current_session)
            self.event_bus.thread_safe_publish(
                Event(
                    type=SystemEvents.SESSION_START,
                    data=SessionStart(SessionFrame=self.current_session),
                )
            )
        except Exception as e:
            logger.error(f"Failed to collect initial session frame: {e}")
            self._running = False
            self.source.stop()
            return

        logger.info("Telemetry collection loop started")

        try:
            while self._running:
                # Check if the source is still connected
                if not self.source.is_connected:
                    logger.warning("Telemetry source disconnected")
                    logger.info(f"Published {self._num_published_events} events before disconnect.")
                    break

                # Collect and publish the next frame
                try:
                    frame = self.source.collect_telemetry_frame()
                    event = Event[TelemetryAndSessionId](
                        type=SystemEvents.TELEMETRY_EVENT,
                        data=TelemetryAndSessionId(
                            telemetry=frame, session_id=self.current_session.session_id
                        ),
                    )

                    self.event_bus.thread_safe_publish(event)
                    self._num_published_events += 1

                except RuntimeError as e:
                    # Source became disconnected during collection
                    logger.warning(f"Collection failed: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error collecting telemetry frame: {e}", exc_info=True)
                    # time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Telemetry collection interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in collection loop: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up after collection loop ends."""
        self._running = False

        if self.current_session is not None:
            self.event_bus.thread_safe_publish(
                Event(
                    type=SystemEvents.SESSION_END,
                    data=SessionEnd(session_id=self.current_session.session_id),
                )
            )
            self.session_registry.end_session(self.current_session.session_id)

        self.source.stop()
        logger.info("Telemetry collection loop stopped")
