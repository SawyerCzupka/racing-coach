use std::sync::atomic::{AtomicUsize, Ordering};

use async_trait::async_trait;
use tracing::info;

use crate::events::handler::{EventHandler, HandlerContext};
use crate::events::types::{Event, EventKind};

/// Counts telemetry frames received - useful for debugging event delivery
pub struct CounterHandler {
    frame_count: AtomicUsize,
}

impl CounterHandler {
    pub fn new() -> Self {
        Self {
            frame_count: AtomicUsize::new(0),
        }
    }

    /// Get the current count (can be called from outside)
    pub fn count(&self) -> usize {
        self.frame_count.load(Ordering::Relaxed)
    }
}

impl Default for CounterHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl EventHandler for CounterHandler {
    fn handles(&self) -> EventKind {
        EventKind::TelemetryFrame
    }

    fn name(&self) -> &'static str {
        "CounterHandler"
    }

    async fn handle(&self, event: Event, _ctx: &HandlerContext) {
        let Event::TelemetryFrame(_) = event else {
            return;
        };

        let count = self.frame_count.fetch_add(1, Ordering::Relaxed) + 1;

        // Log periodically to show progress without flooding
        if count % 5000 == 0 {
            info!("CounterHandler: {} frames received so far", count);
        }
    }
}
