use std::sync::atomic::{AtomicUsize, Ordering};

use async_trait::async_trait;
use tracing::info;

use crate::events::handler::{EventHandler, HandlerContext};
use crate::events::types::{Event, EventKind};

/// Logs telemetry frames at configurable frequency
pub struct LogHandler {
    log_frequency: usize,
    frame_count: AtomicUsize,
}

impl LogHandler {
    pub fn new(log_frequency: usize) -> Self {
        Self {
            log_frequency,
            frame_count: AtomicUsize::new(0),
        }
    }
}

impl Default for LogHandler {
    fn default() -> Self {
        Self::new(60) // Log every 60 frames (~1 second at 60Hz)
    }
}

#[async_trait]
impl EventHandler for LogHandler {
    fn handles(&self) -> EventKind {
        EventKind::TelemetryFrame
    }

    fn name(&self) -> &'static str {
        "LogHandler"
    }

    async fn handle(&self, event: Event, _ctx: &HandlerContext) {
        let Event::TelemetryFrame(frame) = event else {
            return;
        };

        let count = self.frame_count.fetch_add(1, Ordering::Relaxed);

        if count.is_multiple_of(self.log_frequency) {
            info!(
                "Frame {}: Speed={:.1}, RPM={:.0}, Gear={}, Lap={}, DistPct={}",
                count, frame.speed, frame.rpm, frame.gear, frame.lap_number, frame.lap_distance_pct
            );
        }
    }
}
