use std::sync::Arc;

use async_trait::async_trait;
use tokio::sync::Mutex;
use tracing::{debug, info};

use crate::events::handler::{EventHandler, HandlerContext};
use crate::events::types::{Event, EventKind, LapCompletePayload};

/// Detects lap completion by monitoring lap_number changes
pub struct LapHandler {
    state: Mutex<LapHandlerState>,
}

struct LapHandlerState {
    current_lap: i32,
    frame_count: usize,
}

impl LapHandler {
    pub fn new() -> Self {
        Self {
            state: Mutex::new(LapHandlerState {
                current_lap: -1,
                frame_count: 0,
            }),
        }
    }
}

impl Default for LapHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl EventHandler for LapHandler {
    fn handles(&self) -> EventKind {
        EventKind::TelemetryFrame
    }

    fn name(&self) -> &'static str {
        "LapHandler"
    }

    async fn handle(&self, event: Event, ctx: &HandlerContext) {
        let Event::TelemetryFrame(frame) = event else {
            return;
        };

        let mut state = self.state.lock().await;
        state.frame_count += 1;

        // Detect lap change
        if frame.lap_number != state.current_lap && state.current_lap >= 0 {
            info!(
                "Lap {} complete after {} frames",
                state.current_lap, state.frame_count
            );

            // Publish LapComplete event
            let lap_complete = LapCompletePayload {
                lap_number: state.current_lap,
                lap_time_ms: None,
                frame_count: state.frame_count,
            };

            ctx.publish(Event::LapComplete(Arc::new(lap_complete)));

            // Reset for new lap
            state.frame_count = 0;
        }

        state.current_lap = frame.lap_number;
        debug!("Lap {} frame {}", state.current_lap, state.frame_count);
    }
}
