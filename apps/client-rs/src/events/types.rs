use std::sync::Arc;

/// Discriminant enum for channel routing (no payload, just identifies event kind)
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum EventKind {
    TelemetryFrame,
    LapComplete,
}

impl EventKind {
    /// Iterator over all event kinds - used to initialize channels
    pub fn all() -> impl Iterator<Item = EventKind> {
        [EventKind::TelemetryFrame, EventKind::LapComplete].into_iter()
    }
}

/// Main event enum with Arc-wrapped payloads for zero-copy broadcast
#[derive(Clone, Debug)]
pub enum Event {
    // TelemetryFrame(TelemetryFramePayload),
    TelemetryFrame(Arc<TelemetryFramePayload>),
    LapComplete(Arc<LapCompletePayload>),
}

impl Event {
    /// Get the discriminant kind for channel routing
    pub fn kind(&self) -> EventKind {
        match self {
            Event::TelemetryFrame(_) => EventKind::TelemetryFrame,
            Event::LapComplete(_) => EventKind::LapComplete,
        }
    }
}

/// Telemetry data from iRacing - minimal stub
#[derive(Clone, Debug)]
pub struct TelemetryFramePayload {
    pub speed: f32,
    pub rpm: f32,
    pub gear: i32,
    pub lap_number: i32,
    pub lap_distance_pct: f32,
    pub session_time: f64,
}

/// Completed lap data - minimal stub
#[derive(Clone, Debug)]
pub struct LapCompletePayload {
    pub lap_number: i32,
    pub lap_time_ms: Option<u64>,
    pub frame_count: usize,
}
