//! Lap handler for detecting lap completion and publishing lap telemetry.
//!
//! Buffers telemetry frames and detects when a lap is completed, then publishes
//! the complete lap telemetry sequence.

use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{debug, info, warn};
use uuid::Uuid;

use crate::events::{
    Event, EventHandler, HandlerContext, HandlerError, LapTelemetryPayload,
    LapTelemetrySequencePayload, SessionInfo, TelemetryEventPayload, TelemetryFrame,
};

/// Configuration for lap detection
#[derive(Debug, Clone)]
pub struct LapHandlerConfig {
    /// Minimum lap completion percentage to consider a lap valid (0.0-1.0)
    pub lap_completion_threshold: f32,
}

impl Default for LapHandlerConfig {
    fn default() -> Self {
        Self {
            lap_completion_threshold: 0.05,
        }
    }
}

/// Internal state for lap tracking
struct LapState {
    /// Current lap number being tracked
    current_lap: i32,
    /// Buffer of telemetry frames for the current lap
    telemetry_buffer: Vec<TelemetryFrame>,
    /// Current session info (if available)
    current_session: Option<SessionInfo>,
    /// Total telemetry events processed
    num_telemetry_events: u64,
}

impl Default for LapState {
    fn default() -> Self {
        Self {
            current_lap: -1,
            telemetry_buffer: Vec::with_capacity(10000), // Pre-allocate for ~2.5 min lap at 60Hz
            current_session: None,
            num_telemetry_events: 0,
        }
    }
}

/// Handler that buffers telemetry frames and publishes complete laps
pub struct LapHandler {
    config: LapHandlerConfig,
    state: RwLock<LapState>,
}

impl LapHandler {
    /// Create a new lap handler with default configuration
    pub fn new() -> Self {
        Self::with_config(LapHandlerConfig::default())
    }

    /// Create a new lap handler with custom configuration
    pub fn with_config(config: LapHandlerConfig) -> Self {
        Self {
            config,
            state: RwLock::new(LapState::default()),
        }
    }

    /// Handle session start event
    async fn handle_session_start(&self, session: &SessionInfo) {
        let mut state = self.state.write().await;

        // If we had a previous session with buffered data, discard it
        if !state.telemetry_buffer.is_empty() {
            info!(
                "New session detected, discarding {} buffered frames",
                state.telemetry_buffer.len()
            );
            state.telemetry_buffer.clear();
        }

        state.current_session = Some(session.clone());
        state.current_lap = -1;
        state.num_telemetry_events = 0;

        info!(
            "Session started: {} - {}",
            session.track_name, session.car_name
        );
    }

    /// Handle session end event
    async fn handle_session_end(&self, session_id: &Uuid) {
        let state = self.state.read().await;
        info!(
            "Session {} complete. Collected {} telemetry events.",
            session_id, state.num_telemetry_events
        );
    }

    /// Handle telemetry frame event
    async fn handle_telemetry_frame(
        &self,
        payload: &TelemetryEventPayload,
        ctx: &HandlerContext<'_>,
    ) -> Result<Option<Event>, HandlerError> {
        let frame = &payload.frame;
        let mut state = self.state.write().await;

        state.num_telemetry_events += 1;

        // Check for lap change
        if frame.lap_number != state.current_lap {
            debug!(
                "Lap change detected: {} -> {}",
                state.current_lap, frame.lap_number
            );

            // Ignore incomplete laps (e.g., returning to pits)
            if frame.lap_distance_pct < self.config.lap_completion_threshold
                && frame.lap_number == 0
            {
                state.current_lap = frame.lap_number;
                state.telemetry_buffer.clear();
                debug!(
                    "Ignoring lap change to {} due to low distance percentage",
                    frame.lap_number
                );
                return Ok(None);
            }

            // Starting first lap or leaving pits
            if state.current_lap == 0 || state.current_lap == -1 {
                debug!(
                    "Starting first lap or leaving pits. Setting current lap to {}",
                    frame.lap_number
                );
                state.current_lap = frame.lap_number;
                state.telemetry_buffer.clear();
                state.telemetry_buffer.push(frame.clone());
                return Ok(None);
            }

            // Publish completed lap
            if !state.telemetry_buffer.is_empty() {
                let event = self.create_lap_event(&state, ctx)?;
                info!(
                    "Lap {} finished with {} frames",
                    state.current_lap,
                    state.telemetry_buffer.len()
                );

                // Clear buffer and update lap number
                state.telemetry_buffer.clear();
                state.current_lap = frame.lap_number;
                state.telemetry_buffer.push(frame.clone());

                return Ok(Some(event));
            }

            state.current_lap = frame.lap_number;
        }

        // Add frame to buffer
        state.telemetry_buffer.push(frame.clone());

        Ok(None)
    }

    /// Create a lap telemetry sequence event from current buffer
    fn create_lap_event(
        &self,
        state: &LapState,
        _ctx: &HandlerContext<'_>,
    ) -> Result<Event, HandlerError> {
        let session = state.current_session.as_ref().ok_or_else(|| {
            HandlerError::ProcessingError("No session info available".to_string())
        })?;

        let frames = Arc::new(state.telemetry_buffer.clone());
        let lap_id = Uuid::new_v4();

        // Calculate lap time from frames
        let lap_time = if frames.len() >= 2 {
            Some(frames.last().unwrap().session_time - frames.first().unwrap().session_time)
        } else {
            None
        };

        let lap_telemetry = LapTelemetryPayload { frames, lap_time };

        let payload = LapTelemetrySequencePayload {
            lap_telemetry,
            session: session.clone(),
            lap_id,
        };

        Ok(Event::LapTelemetrySequence(payload))
    }
}

impl Default for LapHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl EventHandler for LapHandler {
    fn name(&self) -> &'static str {
        "LapHandler"
    }

    async fn handle(&self, event: &Event, ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::SessionStart(session) => {
                self.handle_session_start(session).await;
                Ok(true)
            }
            Event::SessionEnd { session_id } => {
                self.handle_session_end(session_id).await;
                Ok(true)
            }
            Event::TelemetryEvent(payload) => {
                if let Some(lap_event) = self.handle_telemetry_frame(payload, ctx).await? {
                    // Publish the lap event
                    ctx.publisher
                        .publish(lap_event)
                        .await
                        .map_err(|e| HandlerError::PublishError(e))?;
                }
                Ok(true)
            }
            _ => Ok(false), // Don't handle other events
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    fn create_test_frame(lap_number: i32, lap_distance_pct: f32) -> TelemetryFrame {
        TelemetryFrame {
            timestamp: Utc::now(),
            session_time: 100.0,
            lap_number,
            lap_distance_pct,
            lap_distance: lap_distance_pct * 5000.0,
            current_lap_time: 45.0,
            last_lap_time: 90.0,
            best_lap_time: 88.0,
            speed: 50.0,
            rpm: 7500.0,
            gear: 4,
            throttle: 0.8,
            brake: 0.0,
            clutch: 0.0,
            steering_angle: 0.0,
            lateral_acceleration: 0.0,
            longitudinal_acceleration: 0.0,
            vertical_acceleration: 0.0,
            yaw_rate: 0.0,
            roll_rate: 0.0,
            pitch_rate: 0.0,
            velocity_x: 50.0,
            velocity_y: 0.0,
            velocity_z: 0.0,
            yaw: 0.0,
            pitch: 0.0,
            roll: 0.0,
            track_temp: 30.0,
            air_temp: 25.0,
            on_pit_road: false,
        }
    }

    fn create_test_session() -> SessionInfo {
        SessionInfo {
            session_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            track_id: 142,
            track_name: "Test Track".to_string(),
            track_config_name: None,
            track_type: "road course".to_string(),
            car_id: 123,
            car_name: "Test Car".to_string(),
            car_class_id: 456,
            series_id: 789,
        }
    }

    #[tokio::test]
    async fn test_lap_handler_creation() {
        let handler = LapHandler::new();
        assert_eq!(handler.name(), "LapHandler");
    }

    #[tokio::test]
    async fn test_session_start_clears_buffer() {
        let handler = LapHandler::new();

        // Add some frames to buffer
        {
            let mut state = handler.state.write().await;
            state.telemetry_buffer.push(create_test_frame(1, 0.5));
            state.telemetry_buffer.push(create_test_frame(1, 0.6));
        }

        // Start new session
        let session = create_test_session();
        handler.handle_session_start(&session).await;

        // Buffer should be cleared
        let state = handler.state.read().await;
        assert!(state.telemetry_buffer.is_empty());
        assert!(state.current_session.is_some());
    }

    #[tokio::test]
    async fn test_config_defaults() {
        let config = LapHandlerConfig::default();
        assert_eq!(config.lap_completion_threshold, 0.05);
    }
}
