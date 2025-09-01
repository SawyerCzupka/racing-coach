import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, TypeAlias, TypeVar

from ..models.events import LapAndSession, TelemetryAndSession

logger = logging.getLogger(__name__)


# class EventType(Enum):
#     LAP_TELEMETRY_SEQUENCE = auto()
#     BRAKE_ZONE_ENTERED = auto()
#     BRAKE_ZONE_EXITED = auto()
#     CORNER_ENTERED = auto()
#     CORNER_EXITED = auto()
#     TELEMETRY_FRAME = auto()
#     SESSION_FRAME = auto()
#     SESSION_ENDED = auto()

#     # System
#     SHUTDOWN = auto()


T = TypeVar("T")


@dataclass(frozen=True)
class EventType(Generic[T]):
    name: str

    def __repr__(self) -> str:
        return f"EventType<{self.name}>"


class SystemEvents:
    LAP_TELEMETRY_SEQUENCE: EventType[LapAndSession] = EventType(
        "LAP_TELEMETRY_SEQUENCE"
    )
    TELEMETRY_FRAME: EventType[TelemetryAndSession] = EventType("TELEMETRY_FRAME")


@dataclass
class Event(Generic[T]):
    type: EventType[T]
    data: T
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HandlerContext(Generic[T]):
    event_bus: "EventBus"
    event: Event[T]
    # timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class Handler(Generic[T]):
    type: EventType[T]
    fn: Callable[[HandlerContext[T]], Any]


HandlerType: TypeAlias = Callable[[HandlerContext[T]], Any]

# _SUBSCRIPTION_REGISTRY: list[tuple[EventType, Callable]] = []
# _INSTANCE_SUBSCRIPTION_MARKERS: dict[type, list[tuple[EventType, str]]] = {}


# def subscribe(event_type: EventType):
#     def decorator(fn: Callable):
#         qualname = fn.__qualname__
#         if "." in qualname:
#             # Get the class name, e.g. "MyClass"
#             cls_name = qualname.split(".")[0]
#             # Get the class object from globals.
#             cls = fn.__globals__.get(cls_name)
#             # This will almost always be true with the current code structure but is technically not guaranteed (method inside class inside function)
#             if cls:
#                 _INSTANCE_SUBSCRIPTION_MARKERS.setdefault(cls, []).append(
#                     (event_type, fn.__name__)
#                 )
#         else:
#             _SUBSCRIPTION_REGISTRY.append((event_type, fn))
#         return fn

#     return decorator


class EventBus:
    """Event bus for broadcasting events."""

    def __init__(
        self,
        max_queue_size: int = 1000,  # 0 = no limit
        max_workers: int | None = None,  # None = use all available cores
        thread_name_prefix: str = "EventHandler",
    ) -> None:
        """Initialize the event bus."""

        self._handlers: dict[EventType[Any], list[HandlerType[Any]]] = {}
        self._queue: asyncio.Queue[Event[Any]] = asyncio.Queue(maxsize=max_queue_size)
        self._thread_pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        self._running: bool = False
        # self._process_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, event_type: EventType[T], handler: HandlerType[T]) -> None:
        """Add a handler for a specific event type.

        Whenever the event bus receives an event of the specified type, the handler will be called with the event context.
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

    def unsubscribe(self, event_type: EventType[T], handler: HandlerType[T]) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Removed handler {handler} for event {event_type}")

    async def publish(self, event: Event[Any]) -> None:
        """Publish an event to the bus."""
        assert self._running, "Event bus not running"
        assert self._loop is not None, "Event loop not set"

        try:
            await self._queue.put(event)
            logger.debug(f"Published event {event.type}")
        except Exception as e:
            logger.error(f"Error publishing event {event.type}: {e}")
            raise

    def thread_safe_publish(self, event: Event[Any]) -> None:
        """Called from collector thread or handlers to publish events"""
        if not self._running or self._loop is None:
            raise RuntimeError("Event bus not running")

        # asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)
        asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)

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
            self._loop.run_until_complete(self._process_events())

        import threading

        self._thread = threading.Thread(target=run_event_loop, daemon=True)
        self._thread.start()
        logger.info("Event bus started")

    def stop(self) -> None:
        """Stop processing events and clean up."""
        if not self._running:
            logger.warning("Event bus stop requested but not running")
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

                # for handler in handlers:
                #     self._loop.run_in_executor(self._thread_pool, handler, context)

                if handlers:
                    # Run all handlers at the same time in their own threads
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

    # @property
    def is_running(self) -> bool:
        return self._running


# class HandlerMeta(type):
#     def __call__(cls, *args, **kwargs):
#         instance = super().__call__(*args, **kwargs)

#         if not hasattr(instance, "event_bus") or not isinstance(
#             instance.event_bus, EventBus
#         ):
#             raise AttributeError(
#                 f"Handler Class '{cls.__name__}' must have an 'event_bus' attribute of type EventBus. "
#                 "Did you forget to call super().__init__(event_bus)?"
#             )

#         markers = _INSTANCE_SUBSCRIPTION_MARKERS.get(cls, [])
#         for event_type, method_name in markers:
#             method = getattr(instance, method_name)
#             instance.event_bus.subscribe(event_type, method)
#         return instance


# class EventHandler(metaclass=HandlerMeta):
#     """Base class for all event handler classes."""

#     def __init__(self, event_bus: "EventBus"):
#         self.event_bus = event_bus
