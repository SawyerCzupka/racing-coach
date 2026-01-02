"""Factories for creating test data using polyfactory."""

from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from racing_coach_core.algs.events import (
    BrakingMetrics,
    CornerMetrics,
    CornerSegmentInput,
    LapMetrics,
)
from racing_coach_core.schemas.events import LapAndSession, TelemetryAndSession
from racing_coach_core.schemas.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)

# ============================================================================
# Pydantic Schema Factories
# ============================================================================


class TelemetryFrameFactory(ModelFactory[TelemetryFrame]): ...


class SessionFrameFactory(ModelFactory[SessionFrame]): ...


class LapTelemetryFactory(ModelFactory[LapTelemetry]): ...


class TelemetryAndSessionFactory(ModelFactory[TelemetryAndSession]): ...


class LapAndSessionFactory(ModelFactory[LapAndSession]): ...


# ============================================================================
# Dataclass Factories
# ============================================================================


class BrakingMetricsFactory(DataclassFactory[BrakingMetrics]): ...


class CornerMetricsFactory(DataclassFactory[CornerMetrics]): ...


class CornerSegmentInputFactory(DataclassFactory[CornerSegmentInput]): ...


class LapMetricsFactory(DataclassFactory[LapMetrics]): ...
