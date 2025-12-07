use chrono::{DateTime, Utc};
use std::sync::Arc;
use uuid::Uuid;

/// Session information (shared building block)
#[derive(Debug, Clone)]
pub struct SessionInfo {
    pub session_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub track_id: i32,
    pub track_name: String,
    pub track_config_name: Option<String>,
    pub track_type: String,
    pub car_id: i32,
    pub car_name: String,
    pub car_class_id: i32,
    pub series_id: i32,
}

/// Single frame of telemetry data
#[derive(Debug, Clone)]
pub struct TelemetryFrame {
    // Time
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

    // Track Conditions
    pub track_temp: f32,
    pub air_temp: f32,

    // Session State
    pub on_pit_road: bool,
}

/// Telemetry frame with session context
#[derive(Debug, Clone)]
pub struct TelemetryEventPayload {
    pub frame: TelemetryFrame,
    pub session_id: Uuid,
}

/// Complete lap telemetry sequence
#[derive(Debug, Clone)]
pub struct LapTelemetryPayload {
    pub frames: Arc<Vec<TelemetryFrame>>,
    pub lap_time: Option<f64>,
}

/// Lap telemetry with session context
#[derive(Debug, Clone)]
pub struct LapTelemetrySequencePayload {
    pub lap_telemetry: LapTelemetryPayload,
    pub session: SessionInfo,
    pub lap_id: Uuid,
}

/// Metrics for a single braking zone
#[derive(Debug, Clone)]
pub struct BrakingMetrics {
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

/// Metrics for a single corner
#[derive(Debug, Clone)]
pub struct CornerMetrics {
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

/// Computed lap metrics
#[derive(Debug, Clone)]
pub struct LapMetricsPayload {
    pub lap_number: i32,
    pub lap_time: Option<f64>,
    pub max_speed: f32,
    pub min_speed: f32,
    pub average_corner_speed: f32,
    pub total_corners: i32,
    pub total_braking_zones: i32,
    pub braking_zones: Vec<BrakingMetrics>,
    pub corners: Vec<CornerMetrics>,
}

/// Lap metrics with session context
#[derive(Debug, Clone)]
pub struct LapMetricsExtractedPayload {
    pub metrics: LapMetricsPayload,
    pub session: SessionInfo,
    pub lap_id: Uuid,
}
