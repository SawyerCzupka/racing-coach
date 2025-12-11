//! Tests for API models serialization and deserialization.

use chrono::Utc;
use racing_coach_client::api::{
    BrakingMetricsApi, CornerMetricsApi, HealthResponse, LapMetricsApi, LapMetricsResponse,
    LapSummary, LapTelemetryApi, LapUploadRequest, LapUploadResponse, MetricsUploadRequest,
    MetricsUploadResponse, SessionDetailResponse, SessionFrameApi, SessionListResponse,
    SessionSummary, TelemetryFrameApi,
};
use std::collections::HashMap;
use uuid::Uuid;

// ============================================================================
// TelemetryFrameApi Tests
// ============================================================================

fn create_test_telemetry_frame() -> TelemetryFrameApi {
    TelemetryFrameApi {
        timestamp: Utc::now(),
        session_time: 100.5,
        lap_number: 5,
        lap_distance_pct: 0.5,
        lap_distance: 2500.0,
        current_lap_time: 45.5,
        last_lap_time: 90.0,
        best_lap_time: 88.5,
        speed: 50.0,
        rpm: 7500.0,
        gear: 4,
        throttle: 0.8,
        brake: 0.0,
        clutch: 0.0,
        steering_angle: 0.1,
        lateral_acceleration: 15.0,
        longitudinal_acceleration: 2.0,
        vertical_acceleration: 0.0,
        yaw_rate: 0.05,
        roll_rate: 0.01,
        pitch_rate: 0.0,
        velocity_x: 49.0,
        velocity_y: 5.0,
        velocity_z: 0.0,
        yaw: 1.5,
        pitch: 0.0,
        roll: 0.02,
        latitude: 0.0,
        longitude: 0.0,
        altitude: 0.0,
        tire_temps: HashMap::new(),
        tire_wear: HashMap::new(),
        brake_line_pressure: HashMap::new(),
        track_temp: 30.0,
        track_wetness: 0,
        air_temp: 25.0,
        session_flags: 0,
        track_surface: 3,
        on_pit_road: false,
    }
}

#[test]
fn test_telemetry_frame_api_serialize() {
    let frame = create_test_telemetry_frame();
    let json = serde_json::to_string(&frame).unwrap();

    assert!(json.contains("lap_number"));
    assert!(json.contains("speed"));
    assert!(json.contains("throttle"));
    assert!(json.contains("brake"));
}

#[test]
fn test_telemetry_frame_api_deserialize() {
    let frame = create_test_telemetry_frame();
    let json = serde_json::to_string(&frame).unwrap();
    let deserialized: TelemetryFrameApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.lap_number, frame.lap_number);
    assert_eq!(deserialized.speed, frame.speed);
    assert_eq!(deserialized.throttle, frame.throttle);
}

#[test]
fn test_telemetry_frame_api_clone() {
    let frame = create_test_telemetry_frame();
    let cloned = frame.clone();

    assert_eq!(frame.lap_number, cloned.lap_number);
    assert_eq!(frame.speed, cloned.speed);
}

#[test]
fn test_telemetry_frame_api_debug() {
    let frame = create_test_telemetry_frame();
    let debug_str = format!("{:?}", frame);

    assert!(debug_str.contains("TelemetryFrameApi"));
}

#[test]
fn test_telemetry_frame_api_default_values() {
    // Test deserialization with missing optional fields
    let json = r#"{
        "timestamp": "2024-01-01T00:00:00Z",
        "session_time": 100.0,
        "lap_number": 1,
        "lap_distance_pct": 0.5,
        "lap_distance": 1000.0,
        "current_lap_time": 30.0,
        "last_lap_time": 60.0,
        "best_lap_time": 58.0,
        "speed": 40.0,
        "rpm": 6000.0,
        "gear": 3,
        "throttle": 0.5,
        "brake": 0.0,
        "clutch": 0.0,
        "steering_angle": 0.0,
        "lateral_acceleration": 0.0,
        "longitudinal_acceleration": 0.0,
        "vertical_acceleration": 0.0,
        "yaw_rate": 0.0,
        "roll_rate": 0.0,
        "pitch_rate": 0.0,
        "velocity_x": 40.0,
        "velocity_y": 0.0,
        "velocity_z": 0.0,
        "yaw": 0.0,
        "pitch": 0.0,
        "roll": 0.0,
        "track_temp": 25.0,
        "air_temp": 20.0,
        "on_pit_road": false
    }"#;

    let frame: TelemetryFrameApi = serde_json::from_str(json).unwrap();
    assert_eq!(frame.latitude, 0.0); // Default value
    assert_eq!(frame.track_wetness, 0); // Default value
}

// ============================================================================
// SessionFrameApi Tests
// ============================================================================

fn create_test_session_frame() -> SessionFrameApi {
    SessionFrameApi {
        timestamp: Utc::now(),
        session_id: Uuid::new_v4(),
        track_id: 142,
        track_name: "Mount Panorama".to_string(),
        track_config_name: Some("Full Circuit".to_string()),
        track_type: "road course".to_string(),
        car_id: 123,
        car_name: "Mazda MX-5".to_string(),
        car_class_id: 456,
        series_id: 789,
    }
}

#[test]
fn test_session_frame_api_serialize() {
    let session = create_test_session_frame();
    let json = serde_json::to_string(&session).unwrap();

    assert!(json.contains("track_name"));
    assert!(json.contains("Mount Panorama"));
    assert!(json.contains("car_name"));
}

#[test]
fn test_session_frame_api_deserialize() {
    let session = create_test_session_frame();
    let json = serde_json::to_string(&session).unwrap();
    let deserialized: SessionFrameApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.track_id, session.track_id);
    assert_eq!(deserialized.track_name, session.track_name);
}

#[test]
fn test_session_frame_api_optional_config() {
    let session = SessionFrameApi {
        timestamp: Utc::now(),
        session_id: Uuid::new_v4(),
        track_id: 100,
        track_name: "Spa".to_string(),
        track_config_name: None,
        track_type: "road course".to_string(),
        car_id: 50,
        car_name: "Test Car".to_string(),
        car_class_id: 1,
        series_id: 2,
    };

    let json = serde_json::to_string(&session).unwrap();
    let deserialized: SessionFrameApi = serde_json::from_str(&json).unwrap();

    assert!(deserialized.track_config_name.is_none());
}

// ============================================================================
// LapTelemetryApi Tests
// ============================================================================

#[test]
fn test_lap_telemetry_api_serialize() {
    let lap = LapTelemetryApi {
        frames: vec![create_test_telemetry_frame()],
        lap_time: Some(90.5),
    };

    let json = serde_json::to_string(&lap).unwrap();
    assert!(json.contains("frames"));
    assert!(json.contains("lap_time"));
}

#[test]
fn test_lap_telemetry_api_deserialize() {
    let lap = LapTelemetryApi {
        frames: vec![create_test_telemetry_frame(), create_test_telemetry_frame()],
        lap_time: Some(88.0),
    };

    let json = serde_json::to_string(&lap).unwrap();
    let deserialized: LapTelemetryApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.frames.len(), 2);
    assert_eq!(deserialized.lap_time, Some(88.0));
}

#[test]
fn test_lap_telemetry_api_no_lap_time() {
    let lap = LapTelemetryApi {
        frames: vec![],
        lap_time: None,
    };

    let json = serde_json::to_string(&lap).unwrap();
    let deserialized: LapTelemetryApi = serde_json::from_str(&json).unwrap();

    assert!(deserialized.lap_time.is_none());
}

// ============================================================================
// BrakingMetricsApi Tests
// ============================================================================

fn create_test_braking_metrics() -> BrakingMetricsApi {
    BrakingMetricsApi {
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
    }
}

#[test]
fn test_braking_metrics_api_serialize() {
    let metrics = create_test_braking_metrics();
    let json = serde_json::to_string(&metrics).unwrap();

    assert!(json.contains("braking_point_distance"));
    assert!(json.contains("has_trail_braking"));
}

#[test]
fn test_braking_metrics_api_deserialize() {
    let metrics = create_test_braking_metrics();
    let json = serde_json::to_string(&metrics).unwrap();
    let deserialized: BrakingMetricsApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.braking_point_distance, 0.5);
    assert!(deserialized.has_trail_braking);
}

#[test]
fn test_braking_metrics_api_negative_deceleration() {
    let metrics = BrakingMetricsApi {
        braking_point_distance: 0.5,
        braking_point_speed: 80.0,
        end_distance: 0.55,
        max_brake_pressure: 0.95,
        braking_duration: 1.5,
        minimum_speed: 40.0,
        initial_deceleration: -20.0,
        average_deceleration: -15.0,
        braking_efficiency: 0.9,
        has_trail_braking: false,
        trail_brake_distance: 0.0,
        trail_brake_percentage: 0.0,
    };

    let json = serde_json::to_string(&metrics).unwrap();
    let deserialized: BrakingMetricsApi = serde_json::from_str(&json).unwrap();

    assert!(deserialized.initial_deceleration < 0.0);
    assert!(deserialized.average_deceleration < 0.0);
}

// ============================================================================
// CornerMetricsApi Tests
// ============================================================================

fn create_test_corner_metrics() -> CornerMetricsApi {
    CornerMetricsApi {
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
    }
}

#[test]
fn test_corner_metrics_api_serialize() {
    let metrics = create_test_corner_metrics();
    let json = serde_json::to_string(&metrics).unwrap();

    assert!(json.contains("apex_distance"));
    assert!(json.contains("max_lateral_g"));
}

#[test]
fn test_corner_metrics_api_deserialize() {
    let metrics = create_test_corner_metrics();
    let json = serde_json::to_string(&metrics).unwrap();
    let deserialized: CornerMetricsApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.apex_distance, 0.45);
    assert_eq!(deserialized.max_lateral_g, 2.5);
}

// ============================================================================
// LapMetricsApi Tests
// ============================================================================

#[test]
fn test_lap_metrics_api_serialize() {
    let metrics = LapMetricsApi {
        lap_number: 5,
        lap_time: Some(90.5),
        braking_zones: vec![create_test_braking_metrics()],
        corners: vec![create_test_corner_metrics()],
        total_corners: 10,
        total_braking_zones: 8,
        average_corner_speed: 50.0,
        max_speed: 85.0,
        min_speed: 25.0,
    };

    let json = serde_json::to_string(&metrics).unwrap();
    assert!(json.contains("lap_number"));
    assert!(json.contains("braking_zones"));
    assert!(json.contains("corners"));
}

#[test]
fn test_lap_metrics_api_deserialize() {
    let metrics = LapMetricsApi {
        lap_number: 3,
        lap_time: Some(88.0),
        braking_zones: vec![],
        corners: vec![],
        total_corners: 0,
        total_braking_zones: 0,
        average_corner_speed: 0.0,
        max_speed: 80.0,
        min_speed: 30.0,
    };

    let json = serde_json::to_string(&metrics).unwrap();
    let deserialized: LapMetricsApi = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.lap_number, 3);
    assert!(deserialized.braking_zones.is_empty());
}

// ============================================================================
// Request/Response Models Tests
// ============================================================================

#[test]
fn test_lap_upload_request_serialize() {
    let request = LapUploadRequest {
        lap: LapTelemetryApi {
            frames: vec![create_test_telemetry_frame()],
            lap_time: Some(90.0),
        },
        session: create_test_session_frame(),
    };

    let json = serde_json::to_string(&request).unwrap();
    assert!(json.contains("lap"));
    assert!(json.contains("session"));
}

#[test]
fn test_lap_upload_response_deserialize() {
    let json = r#"{
        "status": "success",
        "message": "Lap uploaded successfully",
        "lap_id": "550e8400-e29b-41d4-a716-446655440000"
    }"#;

    let response: LapUploadResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.status, "success");
    assert_eq!(response.lap_id, "550e8400-e29b-41d4-a716-446655440000");
}

#[test]
fn test_metrics_upload_request_serialize() {
    let request = MetricsUploadRequest {
        lap_metrics: LapMetricsApi {
            lap_number: 1,
            lap_time: Some(90.0),
            braking_zones: vec![],
            corners: vec![],
            total_corners: 0,
            total_braking_zones: 0,
            average_corner_speed: 0.0,
            max_speed: 80.0,
            min_speed: 30.0,
        },
        lap_id: "test-lap-id".to_string(),
    };

    let json = serde_json::to_string(&request).unwrap();
    assert!(json.contains("lap_metrics"));
    assert!(json.contains("lap_id"));
}

#[test]
fn test_metrics_upload_response_deserialize() {
    let json = r#"{
        "status": "success",
        "message": "Metrics uploaded",
        "lap_metrics_id": "metrics-123"
    }"#;

    let response: MetricsUploadResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.status, "success");
    assert_eq!(response.lap_metrics_id, "metrics-123");
}

#[test]
fn test_health_response_deserialize() {
    let json = r#"{
        "status": "healthy",
        "version": "1.0.0"
    }"#;

    let response: HealthResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.status, "healthy");
    assert_eq!(response.version, Some("1.0.0".to_string()));
}

#[test]
fn test_health_response_without_version() {
    let json = r#"{"status": "healthy"}"#;

    let response: HealthResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.status, "healthy");
    assert!(response.version.is_none());
}

#[test]
fn test_lap_metrics_response_deserialize() {
    let json = r#"{
        "lap_id": "test-lap",
        "lap_time": 90.5,
        "total_corners": 10,
        "total_braking_zones": 8,
        "average_corner_speed": 50.0,
        "max_speed": 85.0,
        "min_speed": 25.0,
        "braking_zones": [],
        "corners": []
    }"#;

    let response: LapMetricsResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.lap_id, "test-lap");
    assert_eq!(response.total_corners, 10);
}

// ============================================================================
// Session List Models Tests
// ============================================================================

#[test]
fn test_session_summary_deserialize() {
    let json = r#"{
        "session_id": "test-session-123",
        "track_id": 142,
        "track_name": "Mount Panorama",
        "track_config_name": "Full Circuit",
        "track_type": "road course",
        "car_id": 123,
        "car_name": "Mazda MX-5",
        "car_class_id": 456,
        "series_id": 789,
        "lap_count": 15,
        "created_at": "2024-01-01T12:00:00Z"
    }"#;

    let summary: SessionSummary = serde_json::from_str(json).unwrap();
    assert_eq!(summary.session_id, "test-session-123");
    assert_eq!(summary.track_name, "Mount Panorama");
    assert_eq!(summary.lap_count, 15);
}

#[test]
fn test_session_summary_without_config_name() {
    let json = r#"{
        "session_id": "test",
        "track_id": 100,
        "track_name": "Spa",
        "track_config_name": null,
        "track_type": "road course",
        "car_id": 50,
        "car_name": "Test",
        "car_class_id": 1,
        "series_id": 2,
        "lap_count": 5,
        "created_at": "2024-01-01T00:00:00Z"
    }"#;

    let summary: SessionSummary = serde_json::from_str(json).unwrap();
    assert!(summary.track_config_name.is_none());
}

#[test]
fn test_session_list_response_deserialize() {
    let json = r#"{
        "sessions": [
            {
                "session_id": "session-1",
                "track_id": 100,
                "track_name": "Track 1",
                "track_config_name": null,
                "track_type": "road course",
                "car_id": 1,
                "car_name": "Car 1",
                "car_class_id": 1,
                "series_id": 1,
                "lap_count": 10,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 1
    }"#;

    let response: SessionListResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.sessions.len(), 1);
    assert_eq!(response.total, 1);
}

#[test]
fn test_lap_summary_deserialize() {
    let json = r#"{
        "lap_id": "lap-123",
        "lap_number": 5,
        "lap_time": 90.5,
        "is_valid": true,
        "has_metrics": true,
        "created_at": "2024-01-01T12:00:00Z"
    }"#;

    let summary: LapSummary = serde_json::from_str(json).unwrap();
    assert_eq!(summary.lap_id, "lap-123");
    assert_eq!(summary.lap_number, 5);
    assert!(summary.is_valid);
    assert!(summary.has_metrics);
}

#[test]
fn test_lap_summary_no_lap_time() {
    let json = r#"{
        "lap_id": "lap-456",
        "lap_number": 1,
        "lap_time": null,
        "is_valid": false,
        "has_metrics": false,
        "created_at": "2024-01-01T00:00:00Z"
    }"#;

    let summary: LapSummary = serde_json::from_str(json).unwrap();
    assert!(summary.lap_time.is_none());
    assert!(!summary.is_valid);
}

#[test]
fn test_session_detail_response_deserialize() {
    let json = r#"{
        "session_id": "session-123",
        "track_id": 142,
        "track_name": "Mount Panorama",
        "track_config_name": "Full Circuit",
        "track_type": "road course",
        "car_id": 123,
        "car_name": "Mazda MX-5",
        "car_class_id": 456,
        "series_id": 789,
        "laps": [
            {
                "lap_id": "lap-1",
                "lap_number": 1,
                "lap_time": 95.0,
                "is_valid": true,
                "has_metrics": true,
                "created_at": "2024-01-01T12:00:00Z"
            },
            {
                "lap_id": "lap-2",
                "lap_number": 2,
                "lap_time": 92.0,
                "is_valid": true,
                "has_metrics": true,
                "created_at": "2024-01-01T12:02:00Z"
            }
        ],
        "created_at": "2024-01-01T11:55:00Z"
    }"#;

    let response: SessionDetailResponse = serde_json::from_str(json).unwrap();
    assert_eq!(response.session_id, "session-123");
    assert_eq!(response.laps.len(), 2);
    assert_eq!(response.laps[0].lap_number, 1);
    assert_eq!(response.laps[1].lap_number, 2);
}
