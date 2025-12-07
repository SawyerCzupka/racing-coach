use async_trait::async_trait;
use chrono::{DateTime, Utc};

use super::bus::EventPublisher;
use super::error::HandlerError;
use super::types::Event;

/// Context passed to every handler invocation
pub struct HandlerContext<'a> {
    /// Publisher for emitting new events
    pub publisher: &'a EventPublisher,

    /// Timestamp when the event was created
    pub timestamp: DateTime<Utc>,
}

/// Single handler trait - handlers pattern-match on events they care about
#[async_trait]
pub trait EventHandler: Send + Sync {
    /// Human-readable name for logging/debugging
    fn name(&self) -> &'static str;

    /// Handle an event. Return Ok(true) if handled, Ok(false) if ignored.
    ///
    /// Handlers should pattern-match on the event enum and process
    /// only the variants they care about, returning false for others.
    async fn handle(&self, event: &Event, ctx: &HandlerContext<'_>) -> Result<bool, HandlerError>;
}
