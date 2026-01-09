use crate::telem::TelemetryFrame;
use eventbus::EventLike;
use std::sync::Arc;

/// Discriminant enum for channel routing (no payload, just identifies event kind).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum RacingEventKind {
    TelemetryFrameCollected,
    LapComplete,
}

/// Main event enum for racing telemetry events.
///
/// Large, frequent payloads (like TelemetryFrame) use Arc for zero-copy broadcast.
/// Small, infrequent payloads (like LapCompletePayload) are cloned directly.
#[derive(Clone, Debug)]
pub enum RacingEvent {
    TelemetryFrameCollected(Arc<TelemetryFrame>),
    LapComplete(LapCompletePayload),
}

impl EventLike for RacingEvent {
    type Kind = RacingEventKind;

    fn kind(&self) -> Self::Kind {
        match self {
            RacingEvent::TelemetryFrameCollected(_) => RacingEventKind::TelemetryFrameCollected,
            RacingEvent::LapComplete(_) => RacingEventKind::LapComplete,
        }
    }

    fn all_kinds() -> impl Iterator<Item = Self::Kind> {
        [
            RacingEventKind::TelemetryFrameCollected,
            RacingEventKind::LapComplete,
        ]
        .into_iter()
    }
}

/// Completed lap data.
#[derive(Clone, Debug)]
pub struct LapCompletePayload {
    pub lap_number: i32,
    pub lap_time_ms: Option<u64>,
    pub frame_count: usize,
}
