import logging
from collections.abc import Callable
from functools import wraps
from typing import TypeVar, overload

from racing_coach_core.events.base import (
    EventType,
    HandlerFunc,
    HandlerMethod,
    HandlerType,
)

logger = logging.getLogger(__name__)


def handler_for[X](
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


def handler_for_method[X](
    event_type: EventType[X],
) -> Callable[[HandlerMethod[X]], HandlerMethod[X]]:
    """
    Ultra-minimal version that only adds the event type metadata.
    No wrapper function at all - zero runtime overhead.
    """

    def decorator(func: HandlerMethod[X]) -> HandlerMethod[X]:
        return func

    return decorator
