import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from racing_coach_core.events.base import EventType, HandlerContext

logger = logging.getLogger(__name__)

T = TypeVar("T")
HandlerFunc = Callable[[HandlerContext[T]], Any]
HandlerMethod = Callable[[Any, HandlerContext[T]], Any]
HandlerType = HandlerFunc[T] | HandlerMethod[T]


def handler_for(event_type: EventType[T]) -> Callable[[HandlerType[T]], HandlerType[T]]:
    """
    Decorator that provides type safety for event handlers.

    This decorator:
    1. Stores the event type on the function for auto-registration
    2. Provides static type checking via the return type annotation
    3. Works with both regular functions and class methods

    The main benefit is static typing - your IDE will know the exact type
    of context.event.data based on the EventType you specify.

    Usage:
        # For class methods:
        class MyHandler:
            @handler_for(SystemEvents.TELEMETRY_FRAME)
            def handle_telemetry(self, context: HandlerContext[TelemetryAndSession]) -> None:
                data = context.event.data  # Typed as TelemetryAndSession
                # ...

        # For regular functions:
        @handler_for(SystemEvents.TELEMETRY_FRAME)
        def handle_telemetry(context: HandlerContext[TelemetryAndSession]) -> None:
            data = context.event.data  # Typed as TelemetryAndSession
            # ...

    Args:
        event_type: The EventType this handler should process

    Returns:
        The decorated handler function/method with type information attached
    """

    def decorator(func: HandlerType[T]) -> HandlerType[T]:
        # Store the event type on the function for auto-registration
        func.__event_type__ = event_type  # type: ignore

        # Optional: Add minimal runtime logging (can be removed entirely)
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # Preserve the event type on the wrapper
        wrapper.__event_type__ = event_type  # type: ignore
        # wrapper.__annotations__["context"] = HandlerContext[get_args(event_type.__orig_bases__[0])[0]]  # type: ignore
        wrapper.__annotations__["context"] = int
        func.__annotations__["context"] = int

        return wrapper  # type: ignore

    return decorator


# Utility function to extract event type from decorated handlers
def get_event_type(handler_func: Callable[..., Any]) -> EventType[Any] | None:
    """Extract the event type from a decorated handler function."""
    return getattr(handler_func, "__event_type__", None)


# Auto-registration helper
def auto_register_handlers(event_bus, handler_instance) -> None:
    """
    Automatically register all decorated handler methods from an instance.

    Usage:
        class MyHandlers:
            def __init__(self, event_bus):
                self.event_bus = event_bus
                auto_register_handlers(event_bus, self)

            @handler_for(SystemEvents.TELEMETRY_FRAME)
            def handle_telemetry(self, context: HandlerContext[TelemetryAndSession]):
                # ...
    """
    for attr_name in dir(handler_instance):
        attr = getattr(handler_instance, attr_name)
        if callable(attr) and hasattr(attr, "__event_type__"):
            event_type = attr.__event_type__
            event_bus.subscribe(event_type, attr)
            logger.info(f"Auto-registered handler {attr_name} for event {event_type}")


# Even simpler version if you want absolutely minimal overhead:
def handler_for_minimal(
    event_type: EventType[T],
) -> Callable[[HandlerType[T]], HandlerType[T]]:
    """
    Ultra-minimal version that only adds the event type metadata.
    No wrapper function at all - zero runtime overhead.
    """

    def decorator(func: HandlerType[T]) -> HandlerType[T]:
        func.__event_type__ = event_type  # type: ignore
        return func

    return decorator


if __name__ == "__main__":
    # Example usage and test
    from typing import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")

    def add_extra(func: Callable[..., R]) -> Callable[[float], R]:
        def wrapper(bar: float) -> R:
            return func(bar)

        return wrapper

    @add_extra
    def example_function(bar: int) -> bool:
        bar + 1

        return True
