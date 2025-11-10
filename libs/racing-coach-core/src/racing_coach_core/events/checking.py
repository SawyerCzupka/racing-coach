import logging
from collections.abc import Callable

from racing_coach_core.events.base import EventType, HandlerFunc, HandlerMethod

logger = logging.getLogger(__name__)


def func_handles[X](
    event_type: EventType[X],
) -> Callable[[HandlerFunc[X]], HandlerFunc[X]]:
    """
    Ultra-minimal version that only adds the event type metadata.
    No wrapper function at all - zero runtime overhead.
    """

    def decorator(func: HandlerFunc[X]) -> HandlerFunc[X]:
        # func._event_type = event_type  # type: ignore
        return func

    return decorator


def method_handles[X](
    event_type: EventType[X],
) -> Callable[[HandlerMethod[X]], HandlerMethod[X]]:
    """
    Ultra-minimal version that only adds the event type metadata.
    No wrapper function at all - zero runtime overhead.
    """

    def decorator(func: HandlerMethod[X]) -> HandlerMethod[X]:
        # func._event_type = event_type  # type: ignore
        return func

    return decorator
