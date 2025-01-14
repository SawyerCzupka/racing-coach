from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol, Callable, TypeAlias
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging


logger = logging.getLogger(__name__)


class EventType(Enum):
    LAP_COMPLETED = auto()
    BRAKE_ZONE_ENTERED = auto()
    BRAKE_ZONE_EXITED = auto()
    CORNER_ENTERED = auto()
    CORNER_EXITED = auto()
    TELEMETRY_FRAME = auto()
    SESSION_STARTED = auto()
    SESSION_ENDED = auto()

    # System
    SHUTDOWN = auto()


@dataclass
class Event:
    type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HandlerContext:
    event_bus: "EventBus"
    event: Event
    # timestamp: datetime = field(default_factory=datetime.now)


HandlerType: TypeAlias = Callable[[HandlerContext], Any]


def test(test: HandlerType):
    print("foo")


def fuck(context: HandlerContext) -> int:
    return 5


test(fuck)


class EventBus:
    """Event bus for broadcasting events."""

    def __init__(
        self,
        max_queue_size: int = 1000,  # 0 = no limit
        max_workers: int = 0,  # None = use all available cores
        thread_name_prefix: str = "EventHandler",
    ) -> None:
        """Initialize the event bus."""

        self._handlers: dict[EventType, list[Callable]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
        self._thread_pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        self._running: bool = False
        # self._process_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.info(f"Added handler {handler} for event {event_type}")

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Removed handler {handler} for event {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        try:
            await self._queue.put(event)
            logger.debug(f"Published event {event.type}")
        except Exception as e:
            logger.error(f"Error publishing event {event.type}: {e}")
            raise

    def thread_safe_publish(self, event: Event) -> None:
        """Called from collector thread or handlers to publish events"""
        if self._loop is None:
            raise RuntimeError("Event bus not running")
        asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)

    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_event_loop()
        asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop processing events and clean up."""
        if not self._running:
            return

        self._running = False
        self._thread_pool.shutdown(wait=True)

    async def _process_events(self) -> None:
        if self._loop is None:
            raise RuntimeError("Event bus not running")

        while self._running:
            try:
                event = await self._queue.get()
                handlers = self._handlers.get(event.type, [])

                context = HandlerContext(event_bus=self, event=event)

                for handler in handlers:
                    self._loop.run_in_executor(self._thread_pool, handler, context)

                if handlers:
                    await asyncio.gather(
                        *(
                            self._loop.run_in_executor(
                                self._thread_pool, handler, context
                            )
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

    @property
    def is_running(self) -> bool:
        return self._running
