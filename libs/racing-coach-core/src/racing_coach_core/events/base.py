import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..models.events import LapAndSession, MetricsAndSession, SessionEnd, SessionStart
from ..models.telemetry import TelemetryFrame

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventType[T]:
    name: str
    # data_type: type = field(default=type[T])
    data_type: type = type[T]

    def __repr__(self) -> str:
        return f"EventType<{self.name}>"


class SystemEvents:
    LAP_TELEMETRY_SEQUENCE: EventType[LapAndSession] = EventType("LAP_TELEMETRY_SEQUENCE")
    TELEMETRY_FRAME: EventType[TelemetryFrame] = EventType("TELEMETRY_FRAME")
    LAP_METRICS_EXTRACTED: EventType[MetricsAndSession] = EventType("LAP_METRICS_EXTRACTED")
    SESSION_START: EventType[SessionStart] = EventType("SESSION_START")
    SESSION_END: EventType[SessionEnd] = EventType("SESSION_END")


@dataclass(frozen=True)
class Event[T]:
    type: EventType[T]
    data: T
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class HandlerContext[T]:
    event_bus: "EventBus"
    event: Event[T]
    # timestamp: datetime = field(default_factory=datetime.now)


type HandlerFunc[T] = Callable[[HandlerContext[T]], Any]
type HandlerMethod[T] = Callable[[Any, HandlerContext[T]], Any]
type HandlerType[T] = HandlerFunc[T] | HandlerMethod[T]


@dataclass(frozen=True)
class Handler[T]:
    type: EventType[T]
    # fn: Callable[[HandlerContext[T]], Any]
    fn: HandlerFunc[T]


class EventBus:
    """Event bus for broadcasting events."""

    def __init__(
        self,
        max_queue_size: int = 1000,  # 0 = no limit
        max_workers: int | None = None,  # None = use all available cores
        thread_name_prefix: str = "EventHandler",
    ) -> None:
        """Initialize the event bus."""

        self._handlers: dict[EventType[Any], list[HandlerFunc[Any]]] = {}
        self._max_queue_size = max_queue_size
        self._queue: asyncio.Queue[Event[Any]] | None = None  # Created in start()
        self._thread_pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        self._running: bool = False
        # self._process_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe[T](self, event_type: EventType[T], handler: HandlerFunc[T]) -> None:
        """Add a handler for a specific event type.

        Whenever the event bus receives an event of the specified type, the handler will be called
        with the event context.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.info(f"Added handler {handler} for event {event_type}")

    def register_handler(self, handler: Handler[Any]) -> None:
        """Register a new event handler."""
        self._handlers.setdefault(handler.type, []).append(handler.fn)
        logger.info(f"Registered handler {handler.fn} for event {handler.type}")

    def register_handlers(self, handlers: list[Handler[Any]]) -> None:
        for handler in handlers:
            self.register_handler(handler)

    def unsubscribe[T](self, event_type: EventType[T], handler: HandlerFunc[T]) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Removed handler {handler} for event {event_type}")

    async def publish(self, event: Event[Any]) -> None:
        """Publish an event to the bus.

        This method can be called from any event loop. It will schedule the event
        to be added to the EventBus's queue in the EventBus's own event loop.
        """
        if not self._running or self._loop is None or self._queue is None:
            raise RuntimeError("Event bus not running")

        # Check if we're in the EventBus's event loop
        try:
            current_loop = asyncio.get_running_loop()
            if current_loop is self._loop:
                # We're in the EventBus's event loop, can directly await
                await self._queue.put(event)
                logger.debug(f"Published event {event.type}")
            else:
                # We're in a different event loop, need to use run_coroutine_threadsafe
                async def _put_event():
                    await self._queue.put(event)  # type: ignore[union-attr]
                    logger.debug(f"Published event {event.type}")

                future = asyncio.run_coroutine_threadsafe(_put_event(), self._loop)
                # Wait for completion (this blocks the current coroutine but that's okay)
                future.result(timeout=5.0)
        except RuntimeError:
            # No event loop running, use run_coroutine_threadsafe
            async def _put_event():
                await self._queue.put(event)  # type: ignore[union-attr]
                logger.debug(f"Published event {event.type}")

            future = asyncio.run_coroutine_threadsafe(_put_event(), self._loop)
            future.result(timeout=5.0)

    def thread_safe_publish(self, event: Event[Any]) -> None:
        """Called from non-async code or different threads to publish events."""
        if not self._running or self._loop is None or self._queue is None:
            raise RuntimeError("Event bus not running")

        async def _put_event():
            await self._queue.put(event)  # type: ignore[union-attr]
            logger.debug(f"Published event {event.type}")

        asyncio.run_coroutine_threadsafe(_put_event(), self._loop)

    def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
        self._running = True
        self._loop = asyncio.new_event_loop()

        # Create a new thread to run the event loop
        def run_event_loop():
            if self._loop is None:
                raise RuntimeError("Event bus not running")

            asyncio.set_event_loop(self._loop)
            # Create the queue in the event loop that will use it
            self._queue = asyncio.Queue(maxsize=self._max_queue_size)
            # Schedule the event processing task
            self._loop.create_task(self._process_events())
            # Run the loop forever until stop() is called
            self._loop.run_forever()

        import threading

        self._thread = threading.Thread(target=run_event_loop, daemon=True)
        self._thread.start()

        # Wait for the queue to be initialized
        import time

        timeout = 1.0
        start_time = time.time()
        while self._queue is None and time.time() - start_time < timeout:
            time.sleep(0.01)

        if self._queue is None:
            raise RuntimeError("Failed to initialize event queue")

        logger.info("Event bus started")

    def stop(self) -> None:
        """Stop processing events and clean up.

        This method follows asyncio best practices for clean shutdown:
        1. Stop accepting new events
        2. Cancel all pending tasks
        3. Give the loop a chance to process cancellations
        4. Stop and close the event loop
        """
        if not self._running:
            logger.warning("Event bus stop requested but not running")
            return

        self._running = False

        if self._loop is None or not hasattr(self, "_thread"):
            return

        # Schedule cleanup as an async task in the event loop
        async def async_cleanup():
            """Async cleanup to cancel all pending tasks."""
            # Get all tasks except this cleanup task
            pending = [
                task for task in asyncio.all_tasks(self._loop) if task is not asyncio.current_task()
            ]

            # Cancel all pending tasks
            for task in pending:
                task.cancel()

            # Wait for tasks to handle cancellation
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        # Schedule the async cleanup and then stop the loop
        def cleanup_and_stop():
            """Schedule async cleanup then stop the loop."""
            # Create the cleanup task
            cleanup_task = self._loop.create_task(async_cleanup())

            # When cleanup is done, stop the loop
            def stop_loop(task):
                self._loop.stop()

            cleanup_task.add_done_callback(stop_loop)

        # Schedule the cleanup to run in the event loop thread
        self._loop.call_soon_threadsafe(cleanup_and_stop)

        # Wait for the thread to finish
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)

        # Close the event loop (now that the thread has finished)
        if not self._loop.is_closed():
            self._loop.close()

        # Shutdown the thread pool
        self._thread_pool.shutdown(wait=True)

        # Clear references
        self._queue = None
        self._loop = None

        logger.info("Event bus stopped and cleaned up")

    async def _process_events(self) -> None:
        if self._loop is None or self._queue is None:
            raise RuntimeError("Event bus not properly initialized")

        while self._running:
            try:
                event = await self._queue.get()
                handlers = self._handlers.get(event.type, [])

                context = HandlerContext(event_bus=self, event=event)

                # for handler in handlers:
                #     self._loop.run_in_executor(self._thread_pool, handler, context)

                if handlers:
                    # Run all handlers at the same time in their own threads
                    await asyncio.gather(
                        *(
                            self._loop.run_in_executor(self._thread_pool, handler, context)
                            for handler in handlers
                        ),
                        return_exceptions=True,
                    )

                self._queue.task_done()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error processing event: {e}")
                if not self._running:
                    break

    # @property
    def is_running(self) -> bool:
        return self._running
