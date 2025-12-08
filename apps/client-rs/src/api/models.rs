//! API data models for Racing Coach server communication.
//!
//! These models match the FastAPI server's request/response schemas.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

// ============================================================================
// Telemetry Models
// ============================================================================

/// Single frame of telemetry data for API communication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryFrameApi {
    pub timestamp: DateTime<Utc>,
    pub session_time: f64,

    // Lap Information
    pub lap_number: i32,
    pub lap_distance_pct: f32,
    pub lap_distance: f32,
    pub current_lap_time: f32,
    pub last_lap_time: f32,
    pub best_lap_time: f32,

    // Vehicle State
    pub speed: f32,
    pub rpm: f32,
    pub gear: i32,

    // Driver Inputs
    pub throttle: f32,
    pub brake: f32,
    pub clutch: f32,
    pub steering_angle: f32,

    // Vehicle Dynamics
    pub lateral_acceleration: f32,
    pub longitudinal_acceleration: f32,
    pub vertical_acceleration: f32,
    pub yaw_rate: f32,
    pub roll_rate: f32,
    pub pitch_rate: f32,

    // Vehicle Velocity
    pub velocity_x: f32,
    pub velocity_y: f32,
    pub velocity_z: f32,

    // Vehicle Orientation
    pub yaw: f32,
    pub pitch: f32,
    pub roll: f32,

    // GPS Position
    #[serde(default)]
    pub latitude: f32,
    #[serde(default)]
    pub longitude: f32,
    #[serde(default)]
    pub altitude: f32,

    // Tire Data
    #[serde(default)]
    pub tire_temps: HashMap<String, HashMap<String, f32>>,
    #[serde(default)]
    pub tire_wear: HashMap<String, HashMap<String, f32>>,
    #[serde(default)]
    pub brake_line_pressure: HashMap<String, f32>,

    // Track Conditions
    pub track_temp: f32,
    #[serde(default)]
    pub track_wetness: i32,
    pub air_temp: f32,

    // Session State
    #[serde(default)]
    pub session_flags: i32,
    #[serde(default)]
    pub track_surface: i32,
    pub on_pit_road: bool,
}

/// Lap telemetry for API upload
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapTelemetryApi {
    pub frames: Vec<TelemetryFrameApi>,
    pub lap_time: Option<f64>,
}

/// Session information for API communication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionFrameApi {
    pub timestamp: DateTime<Utc>,
    pub session_id: Uuid,
    pub track_id: i32,
    pub track_name: String,
    pub track_config_name: Option<String>,
    pub track_type: String,
    pub car_id: i32,
    pub car_name: String,
    pub car_class_id: i32,
    pub series_id: i32,
}

// ============================================================================
// Metrics Models
// ============================================================================

/// Braking zone metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrakingMetricsApi {
    pub braking_point_distance: f32,
    pub braking_point_speed: f32,
    pub end_distance: f32,
    pub max_brake_pressure: f32,
    pub braking_duration: f32,
    pub minimum_speed: f32,
    pub initial_deceleration: f32,
    pub average_deceleration: f32,
    pub braking_efficiency: f32,
    pub has_trail_braking: bool,
    pub trail_brake_distance: f32,
    pub trail_brake_percentage: f32,
}

/// Corner metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CornerMetricsApi {
    pub turn_in_distance: f32,
    pub apex_distance: f32,
    pub exit_distance: f32,
    pub throttle_application_distance: f32,
    pub turn_in_speed: f32,
    pub apex_speed: f32,
    pub exit_speed: f32,
    pub throttle_application_speed: f32,
    pub max_lateral_g: f32,
    pub time_in_corner: f32,
    pub corner_distance: f32,
    pub max_steering_angle: f32,
    pub speed_loss: f32,
    pub speed_gain: f32,
}

/// Complete lap metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapMetricsApi {
    pub lap_number: i32,
    pub lap_time: Option<f64>,
    pub braking_zones: Vec<BrakingMetricsApi>,
    pub corners: Vec<CornerMetricsApi>,
    pub total_corners: i32,
    pub total_braking_zones: i32,
    pub average_corner_speed: f32,
    pub max_speed: f32,
    pub min_speed: f32,
}

// ============================================================================
// API Request/Response Models
// ============================================================================

/// Request body for uploading lap telemetry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapUploadRequest {
    pub lap: LapTelemetryApi,
    pub session: SessionFrameApi,
}

/// Response from lap upload endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapUploadResponse {
    pub status: String,
    pub message: String,
    pub lap_id: String,
}

/// Request body for uploading metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsUploadRequest {
    pub lap_metrics: LapMetricsApi,
    pub lap_id: String,
}

/// Response from metrics upload endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsUploadResponse {
    pub status: String,
    pub message: String,
    pub lap_metrics_id: String,
}

/// Response from get lap metrics endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapMetricsResponse {
    pub lap_id: String,
    pub lap_time: Option<f64>,
    pub total_corners: i32,
    pub total_braking_zones: i32,
    pub average_corner_speed: f32,
    pub max_speed: f32,
    pub min_speed: f32,
    pub braking_zones: Vec<BrakingMetricsApi>,
    pub corners: Vec<CornerMetricsApi>,
}

/// Health check response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    #[serde(default)]
    pub version: Option<String>,
}

// ============================================================================
// Session List Models
// ============================================================================

/// Summary of a session for list view
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionSummary {
    pub session_id: String,
    pub track_id: i32,
    pub track_name: String,
    pub track_config_name: Option<String>,
    pub track_type: String,
    pub car_id: i32,
    pub car_name: String,
    pub car_class_id: i32,
    pub series_id: i32,
    pub lap_count: i32,
    pub created_at: DateTime<Utc>,
}

/// Response from sessions list endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionListResponse {
    pub sessions: Vec<SessionSummary>,
    pub total: i32,
}

/// Summary of a lap for list view
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapSummary {
    pub lap_id: String,
    pub lap_number: i32,
    pub lap_time: Option<f64>,
    pub is_valid: bool,
    pub has_metrics: bool,
    pub created_at: DateTime<Utc>,
}

/// Detailed session response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionDetailResponse {
    pub session_id: String,
    pub track_id: i32,
    pub track_name: String,
    pub track_config_name: Option<String>,
    pub track_type: String,
    pub car_id: i32,
    pub car_name: String,
    pub car_class_id: i32,
    pub series_id: i32,
    pub laps: Vec<LapSummary>,
    pub created_at: DateTime<Utc>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lap_upload_response_deserialize() {
        let json = r#"{"status":"success","message":"Uploaded","lap_id":"550e8400-e29b-41d4-a716-446655440000"}"#;
        let response: LapUploadResponse = serde_json::from_str(json).unwrap();
        assert_eq!(response.status, "success");
        assert_eq!(response.lap_id, "550e8400-e29b-41d4-a716-446655440000");
    }

    #[test]
    fn test_metrics_upload_response_deserialize() {
        let json = r#"{"status":"success","message":"Metrics uploaded","lap_metrics_id":"abc123"}"#;
        let response: MetricsUploadResponse = serde_json::from_str(json).unwrap();
        assert_eq!(response.status, "success");
    }

    #[test]
    fn test_braking_metrics_serialize() {
        let metrics = BrakingMetricsApi {
            braking_point_distance: 0.5,
            braking_point_speed: 80.0,
            end_distance: 0.55,
            max_brake_pressure: 0.95,
            braking_duration: 1.5,
            minimum_speed: 40.0,
            initial_deceleration: -15.0,
            average_deceleration: -12.0,
            braking_efficiency: 0.85,
            has_trail_braking: true,
            trail_brake_distance: 0.02,
            trail_brake_percentage: 0.3,
        };
        let json = serde_json::to_string(&metrics).unwrap();
        assert!(json.contains("braking_point_distance"));
    }
}
