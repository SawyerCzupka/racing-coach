use async_trait::async_trait;
use tokio::sync::Mutex;
use tracing::{debug, info};

use crate::events::{LapCompletePayload, RacingEvent, RacingEventKind};
use eventbus::{EventHandler, HandlerContext};

/// Detects lap completion by monitoring lap_number changes
pub struct LapHandler {
    state: Mutex<LapHandlerState>,
}

struct LapHandlerState {
    current_lap: i32,
    frame_count: usize,
    valid: bool,
}

impl LapHandler {
    pub fn new() -> Self {
        Self {
            state: Mutex::new(LapHandlerState {
                current_lap: -1,
                frame_count: 0,
                valid: true,
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
impl EventHandler<RacingEvent> for LapHandler {
    fn handles(&self) -> RacingEventKind {
        RacingEventKind::TelemetryFrameCollected
    }

    fn name(&self) -> &'static str {
        "LapHandler"
    }

    async fn handle(&self, event: RacingEvent, ctx: &HandlerContext<RacingEvent>) {
        let RacingEvent::TelemetryFrameCollected(frame) = event else {
            return;
        };

        let mut state = self.state.lock().await;
        state.frame_count += 1;

        if state.valid && frame.track_surface != 3 {
            state.valid = false;
        }

        // Detect lap change
        if frame.lap_number != state.current_lap && state.current_lap >= 0 {
            info!(
                "Lap {} complete after {} frames. Valid: {}",
                state.current_lap, state.frame_count, state.valid
            );

            // Publish LapComplete event (no Arc needed - small payload)
            ctx.publish(RacingEvent::LapComplete(LapCompletePayload {
                lap_number: state.current_lap,
                lap_time_ms: None,
                frame_count: state.frame_count,
            }));

            // Reset for new lap
            state.frame_count = 0;
        }

        state.current_lap = frame.lap_number;
        debug!("Lap {} frame {}", state.current_lap, state.frame_count);
    }
}
