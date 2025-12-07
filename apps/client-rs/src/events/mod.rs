mod bus;
mod error;
mod handler;
mod payloads;
mod types;

// Re-export main types
pub use bus::{EventBus, EventBusConfig, EventPublisher};
pub use error::{EventBusError, HandlerError};
pub use handler::{EventHandler, HandlerContext};
pub use payloads::{
    BrakingMetrics, CornerMetrics, LapMetricsExtractedPayload, LapMetricsPayload,
    LapTelemetryPayload, LapTelemetrySequencePayload, SessionInfo, TelemetryEventPayload,
    TelemetryFrame,
};
pub use types::{Event, TimestampedEvent};
