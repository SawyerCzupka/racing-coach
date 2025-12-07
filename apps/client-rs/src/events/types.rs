use chrono::{DateTime, Utc};
use uuid::Uuid;

use super::payloads::{
    LapMetricsExtractedPayload, LapTelemetrySequencePayload, SessionInfo, TelemetryEventPayload,
    TelemetryFrame,
};

/// All events in the system
#[derive(Debug, Clone)]
pub enum Event {
    /// Individual telemetry data point (raw frame from pitwall)
    TelemetryFrame(TelemetryFrame),

    /// Telemetry frame associated with a session ID
    TelemetryEvent(TelemetryEventPayload),

    /// Session has started with session info
    SessionStart(SessionInfo),

    /// Session has ended
    SessionEnd { session_id: Uuid },

    /// Complete lap telemetry sequence
    LapTelemetrySequence(LapTelemetrySequencePayload),

    /// Computed metrics for a lap
    LapMetricsExtracted(LapMetricsExtractedPayload),
}

/// Wrapper for events with timestamp metadata
#[derive(Debug, Clone)]
pub struct TimestampedEvent {
    pub event: Event,
    pub timestamp: DateTime<Utc>,
}

impl TimestampedEvent {
    pub fn new(event: Event) -> Self {
        Self {
            event,
            timestamp: Utc::now(),
        }
    }
}
