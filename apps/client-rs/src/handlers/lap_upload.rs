//! Lap upload handler for sending lap telemetry to the server.

use async_trait::async_trait;
use chrono::Utc;
use std::sync::Arc;
use tracing::{error, info, warn};

use crate::api::{
    LapTelemetryApi, RacingCoachClient, SessionFrameApi, TelemetryFrameApi,
};
use crate::events::{
    Event, EventHandler, HandlerContext, HandlerError, LapTelemetrySequencePayload,
    SessionInfo, TelemetryFrame,
};

/// Handler that uploads completed lap telemetry to the server
pub struct LapUploadHandler {
    api_client: Arc<RacingCoachClient>,
    enabled: bool,
}

impl LapUploadHandler {
    /// Create a new lap upload handler
    pub fn new(api_client: Arc<RacingCoachClient>) -> Self {
        Self {
            api_client,
            enabled: true,
        }
    }

    /// Create a disabled handler (for testing or offline mode)
    pub fn disabled() -> Self {
        Self {
            api_client: Arc::new(RacingCoachClient::new("http://localhost:8000")),
            enabled: false,
        }
    }

    /// Enable or disable uploads
    pub fn set_enabled(&mut self, enabled: bool) {
        self.enabled = enabled;
    }

    /// Convert session info to API format
    fn convert_session(session: &SessionInfo) -> SessionFrameApi {
        SessionFrameApi {
            timestamp: session.timestamp,
            session_id: session.session_id,
            track_id: session.track_id,
            track_name: session.track_name.clone(),
            track_config_name: session.track_config_name.clone(),
            track_type: session.track_type.clone(),
            car_id: session.car_id,
            car_name: session.car_name.clone(),
            car_class_id: session.car_class_id,
            series_id: session.series_id,
        }
    }

    /// Convert telemetry frame to API format
    fn convert_frame(frame: &TelemetryFrame) -> TelemetryFrameApi {
        TelemetryFrameApi {
            timestamp: frame.timestamp,
            session_time: frame.session_time,
            lap_number: frame.lap_number,
            lap_distance_pct: frame.lap_distance_pct,
            lap_distance: frame.lap_distance,
            current_lap_time: frame.current_lap_time,
            last_lap_time: frame.last_lap_time,
            best_lap_time: frame.best_lap_time,
            speed: frame.speed,
            rpm: frame.rpm,
            gear: frame.gear,
            throttle: frame.throttle,
            brake: frame.brake,
            clutch: frame.clutch,
            steering_angle: frame.steering_angle,
            lateral_acceleration: frame.lateral_acceleration,
            longitudinal_acceleration: frame.longitudinal_acceleration,
            vertical_acceleration: frame.vertical_acceleration,
            yaw_rate: frame.yaw_rate,
            roll_rate: frame.roll_rate,
            pitch_rate: frame.pitch_rate,
            velocity_x: frame.velocity_x,
            velocity_y: frame.velocity_y,
            velocity_z: frame.velocity_z,
            yaw: frame.yaw,
            pitch: frame.pitch,
            roll: frame.roll,
            latitude: 0.0,
            longitude: 0.0,
            altitude: 0.0,
            tire_temps: Default::default(),
            tire_wear: Default::default(),
            brake_line_pressure: Default::default(),
            track_temp: frame.track_temp,
            track_wetness: 0,
            air_temp: frame.air_temp,
            session_flags: 0,
            track_surface: 3, // On track
            on_pit_road: frame.on_pit_road,
        }
    }

    /// Upload lap telemetry to server
    async fn upload_lap(&self, payload: &LapTelemetrySequencePayload) -> Result<(), String> {
        if !self.enabled {
            info!("Lap upload disabled, skipping");
            return Ok(());
        }

        let lap_telemetry = &payload.lap_telemetry;
        let session = &payload.session;
        let lap_id = payload.lap_id;

        let lap_number = lap_telemetry
            .frames
            .first()
            .map(|f| f.lap_number)
            .unwrap_or(-1);

        info!(
            "Uploading lap {} with {} frames (lap_id: {})",
            lap_number,
            lap_telemetry.frames.len(),
            lap_id
        );

        // Convert to API format
        let api_frames: Vec<TelemetryFrameApi> = lap_telemetry
            .frames
            .iter()
            .map(Self::convert_frame)
            .collect();

        let api_lap = LapTelemetryApi {
            frames: api_frames,
            lap_time: lap_telemetry.lap_time,
        };

        let api_session = Self::convert_session(session);

        // Upload
        match self.api_client.upload_lap(&api_lap, &api_session, lap_id).await {
            Ok(response) => {
                info!(
                    "✓ Lap {} uploaded successfully (lap_id: {})",
                    lap_number, response.lap_id
                );
                Ok(())
            }
            Err(e) => {
                error!("✗ Failed to upload lap {}: {}", lap_number, e);
                Err(e.to_string())
            }
        }
    }
}

#[async_trait]
impl EventHandler for LapUploadHandler {
    fn name(&self) -> &'static str {
        "LapUploadHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::LapTelemetrySequence(payload) => {
                if let Err(e) = self.upload_lap(payload).await {
                    // Log error but don't fail the handler
                    warn!("Lap upload failed: {}", e);
                }
                Ok(true)
            }
            _ => Ok(false),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;
    use uuid::Uuid;

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

    #[test]
    fn test_handler_creation() {
        let client = Arc::new(RacingCoachClient::new("http://localhost:8000"));
        let handler = LapUploadHandler::new(client);
        assert_eq!(handler.name(), "LapUploadHandler");
        assert!(handler.enabled);
    }

    #[test]
    fn test_disabled_handler() {
        let handler = LapUploadHandler::disabled();
        assert!(!handler.enabled);
    }

    #[test]
    fn test_session_conversion() {
        let session = create_test_session();
        let api_session = LapUploadHandler::convert_session(&session);

        assert_eq!(api_session.track_id, session.track_id);
        assert_eq!(api_session.track_name, session.track_name);
        assert_eq!(api_session.car_id, session.car_id);
    }
}
