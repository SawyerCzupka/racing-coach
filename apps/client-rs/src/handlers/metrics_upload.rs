//! Metrics upload handler for sending lap metrics to the server.

use async_trait::async_trait;
use std::sync::Arc;
use tracing::{error, info, warn};

use crate::api::{
    BrakingMetricsApi, CornerMetricsApi, LapMetricsApi, RacingCoachClient,
};
use crate::events::{
    BrakingMetrics, CornerMetrics, Event, EventHandler, HandlerContext, HandlerError,
    LapMetricsExtractedPayload, LapMetricsPayload,
};

/// Handler that uploads extracted lap metrics to the server
pub struct MetricsUploadHandler {
    api_client: Arc<RacingCoachClient>,
    enabled: bool,
}

impl MetricsUploadHandler {
    /// Create a new metrics upload handler
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

    /// Convert braking metrics to API format
    fn convert_braking(metrics: &BrakingMetrics) -> BrakingMetricsApi {
        BrakingMetricsApi {
            braking_point_distance: metrics.braking_point_distance,
            braking_point_speed: metrics.braking_point_speed,
            end_distance: metrics.end_distance,
            max_brake_pressure: metrics.max_brake_pressure,
            braking_duration: metrics.braking_duration,
            minimum_speed: metrics.minimum_speed,
            initial_deceleration: metrics.initial_deceleration,
            average_deceleration: metrics.average_deceleration,
            braking_efficiency: metrics.braking_efficiency,
            has_trail_braking: metrics.has_trail_braking,
            trail_brake_distance: metrics.trail_brake_distance,
            trail_brake_percentage: metrics.trail_brake_percentage,
        }
    }

    /// Convert corner metrics to API format
    fn convert_corner(metrics: &CornerMetrics) -> CornerMetricsApi {
        CornerMetricsApi {
            turn_in_distance: metrics.turn_in_distance,
            apex_distance: metrics.apex_distance,
            exit_distance: metrics.exit_distance,
            throttle_application_distance: metrics.throttle_application_distance,
            turn_in_speed: metrics.turn_in_speed,
            apex_speed: metrics.apex_speed,
            exit_speed: metrics.exit_speed,
            throttle_application_speed: metrics.throttle_application_speed,
            max_lateral_g: metrics.max_lateral_g,
            time_in_corner: metrics.time_in_corner,
            corner_distance: metrics.corner_distance,
            max_steering_angle: metrics.max_steering_angle,
            speed_loss: metrics.speed_loss,
            speed_gain: metrics.speed_gain,
        }
    }

    /// Convert lap metrics to API format
    fn convert_metrics(metrics: &LapMetricsPayload) -> LapMetricsApi {
        LapMetricsApi {
            lap_number: metrics.lap_number,
            lap_time: metrics.lap_time,
            braking_zones: metrics.braking_zones.iter().map(Self::convert_braking).collect(),
            corners: metrics.corners.iter().map(Self::convert_corner).collect(),
            total_corners: metrics.total_corners,
            total_braking_zones: metrics.total_braking_zones,
            average_corner_speed: metrics.average_corner_speed,
            max_speed: metrics.max_speed,
            min_speed: metrics.min_speed,
        }
    }

    /// Upload metrics to server
    async fn upload_metrics(&self, payload: &LapMetricsExtractedPayload) -> Result<(), String> {
        if !self.enabled {
            info!("Metrics upload disabled, skipping");
            return Ok(());
        }

        let metrics = &payload.metrics;
        let lap_id = payload.lap_id;

        info!(
            "Uploading metrics for lap {} (lap_id: {}): {} braking zones, {} corners",
            metrics.lap_number,
            lap_id,
            metrics.total_braking_zones,
            metrics.total_corners
        );

        // Convert to API format
        let api_metrics = Self::convert_metrics(metrics);

        // Upload
        match self.api_client.upload_metrics(&api_metrics, lap_id).await {
            Ok(response) => {
                info!(
                    "✓ Lap {} metrics uploaded successfully (id: {})",
                    metrics.lap_number, response.lap_metrics_id
                );
                Ok(())
            }
            Err(e) => {
                error!("✗ Failed to upload metrics for lap {}: {}", metrics.lap_number, e);
                Err(e.to_string())
            }
        }
    }
}

#[async_trait]
impl EventHandler for MetricsUploadHandler {
    fn name(&self) -> &'static str {
        "MetricsUploadHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::LapMetricsExtracted(payload) => {
                if let Err(e) = self.upload_metrics(payload).await {
                    // Log error but don't fail the handler
                    warn!("Metrics upload failed: {}", e);
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

    #[test]
    fn test_handler_creation() {
        let client = Arc::new(RacingCoachClient::new("http://localhost:8000"));
        let handler = MetricsUploadHandler::new(client);
        assert_eq!(handler.name(), "MetricsUploadHandler");
        assert!(handler.enabled);
    }

    #[test]
    fn test_disabled_handler() {
        let handler = MetricsUploadHandler::disabled();
        assert!(!handler.enabled);
    }

    #[test]
    fn test_braking_conversion() {
        let braking = BrakingMetrics {
            braking_point_distance: 0.5,
            braking_point_speed: 80.0,
            end_distance: 0.55,
            max_brake_pressure: 0.95,
            braking_duration: 1.5,
            minimum_speed: 40.0,
            initial_deceleration: 15.0,
            average_deceleration: 12.0,
            braking_efficiency: 0.85,
            has_trail_braking: true,
            trail_brake_distance: 0.02,
            trail_brake_percentage: 0.3,
        };

        let api = MetricsUploadHandler::convert_braking(&braking);
        assert_eq!(api.braking_point_distance, 0.5);
        assert_eq!(api.max_brake_pressure, 0.95);
        assert!(api.has_trail_braking);
    }

    #[test]
    fn test_corner_conversion() {
        let corner = CornerMetrics {
            turn_in_distance: 0.4,
            apex_distance: 0.45,
            exit_distance: 0.5,
            throttle_application_distance: 0.47,
            turn_in_speed: 60.0,
            apex_speed: 45.0,
            exit_speed: 55.0,
            throttle_application_speed: 48.0,
            max_lateral_g: 2.5,
            time_in_corner: 3.0,
            corner_distance: 0.1,
            max_steering_angle: 0.8,
            speed_loss: 15.0,
            speed_gain: 10.0,
        };

        let api = MetricsUploadHandler::convert_corner(&corner);
        assert_eq!(api.apex_distance, 0.45);
        assert_eq!(api.max_lateral_g, 2.5);
    }
}
