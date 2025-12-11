//! Integration tests for the API client using wiremock.

use chrono::Utc;
use racing_coach_client::api::{
    ApiError, BrakingMetricsApi, CornerMetricsApi, HealthResponse, LapMetricsApi, LapTelemetryApi,
    RacingCoachClient, SessionFrameApi, TelemetryFrameApi,
};
use serde_json::json;
use uuid::Uuid;
use wiremock::matchers::{method, path, query_param};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn create_test_session_api() -> SessionFrameApi {
    SessionFrameApi {
        timestamp: Utc::now(),
        session_id: Uuid::new_v4(),
        track_id: 142,
        track_name: "Mount Panorama".to_string(),
        track_config_name: Some("Full Circuit".to_string()),
        track_type: "road course".to_string(),
        car_id: 123,
        car_name: "Ligier JSP320".to_string(),
        car_class_id: 456,
        series_id: 789,
    }
}

fn create_test_telemetry_frame() -> TelemetryFrameApi {
    TelemetryFrameApi {
        timestamp: Utc::now(),
        session_time: 100.0,
        lap_number: 1,
        lap_distance_pct: 0.5,
        lap_distance: 2500.0,
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
        latitude: 0.0,
        longitude: 0.0,
        altitude: 0.0,
        tire_temps: Default::default(),
        tire_wear: Default::default(),
        brake_line_pressure: Default::default(),
        track_temp: 30.0,
        track_wetness: 0,
        air_temp: 25.0,
        session_flags: 0,
        track_surface: 3,
        on_pit_road: false,
    }
}

fn create_test_lap_telemetry() -> LapTelemetryApi {
    LapTelemetryApi {
        frames: vec![create_test_telemetry_frame(); 10],
        lap_time: Some(90.5),
    }
}

fn create_test_braking_metrics() -> BrakingMetricsApi {
    BrakingMetricsApi {
        braking_point_distance: 0.75,
        braking_point_speed: 80.0,
        end_distance: 0.82,
        max_brake_pressure: 0.95,
        braking_duration: 2.5,
        minimum_speed: 40.0,
        initial_deceleration: 15.0,
        average_deceleration: 12.0,
        braking_efficiency: 0.85,
        has_trail_braking: true,
        trail_brake_distance: 0.02,
        trail_brake_percentage: 0.3,
    }
}

fn create_test_corner_metrics() -> CornerMetricsApi {
    CornerMetricsApi {
        turn_in_distance: 0.80,
        apex_distance: 0.85,
        exit_distance: 0.90,
        throttle_application_distance: 0.87,
        turn_in_speed: 45.0,
        apex_speed: 40.0,
        exit_speed: 55.0,
        throttle_application_speed: 42.0,
        max_lateral_g: 1.5,
        time_in_corner: 3.5,
        corner_distance: 0.10,
        max_steering_angle: 0.3,
        speed_loss: 5.0,
        speed_gain: 15.0,
    }
}

fn create_test_lap_metrics() -> LapMetricsApi {
    LapMetricsApi {
        lap_number: 1,
        lap_time: Some(90.5),
        max_speed: 85.0,
        min_speed: 35.0,
        average_corner_speed: 45.0,
        total_corners: 1,
        total_braking_zones: 1,
        braking_zones: vec![create_test_braking_metrics()],
        corners: vec![create_test_corner_metrics()],
    }
}

#[tokio::test]
async fn test_health_check_success() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/health"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "healthy",
            "version": "1.0.0"
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.health_check().await;

    assert!(result.is_ok());
    let health = result.unwrap();
    assert_eq!(health.status, "healthy");
    assert_eq!(health.version, Some("1.0.0".to_string()));
}

#[tokio::test]
async fn test_health_check_server_error() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/health"))
        .respond_with(ResponseTemplate::new(500).set_body_string("Internal Server Error"))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.health_check().await;

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(matches!(err, ApiError::ServerError { status: 500, .. }));
}

#[tokio::test]
async fn test_upload_lap_success() {
    let mock_server = MockServer::start().await;
    let lap_id = Uuid::new_v4();

    Mock::given(method("POST"))
        .and(path("/api/v1/telemetry/lap"))
        .and(query_param("lap_id", lap_id.to_string()))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "success",
            "lap_id": lap_id.to_string(),
            "message": "Lap uploaded successfully"
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let lap = create_test_lap_telemetry();
    let session = create_test_session_api();

    let result = client.upload_lap(&lap, &session, lap_id).await;

    assert!(result.is_ok());
    let response = result.unwrap();
    assert_eq!(response.lap_id, lap_id.to_string());
}

#[tokio::test]
async fn test_upload_lap_server_error() {
    let mock_server = MockServer::start().await;
    let lap_id = Uuid::new_v4();

    Mock::given(method("POST"))
        .and(path("/api/v1/telemetry/lap"))
        .respond_with(ResponseTemplate::new(400).set_body_string("Invalid request body"))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let lap = create_test_lap_telemetry();
    let session = create_test_session_api();

    let result = client.upload_lap(&lap, &session, lap_id).await;

    assert!(result.is_err());
}

#[tokio::test]
async fn test_get_latest_session_success() {
    let mock_server = MockServer::start().await;
    let session_id = Uuid::new_v4();

    Mock::given(method("GET"))
        .and(path("/api/v1/telemetry/sessions/latest"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "timestamp": "2024-01-15T10:30:00Z",
            "session_id": session_id.to_string(),
            "track_id": 142,
            "track_name": "Mount Panorama",
            "track_config_name": "Full Circuit",
            "track_type": "road course",
            "car_id": 123,
            "car_name": "Ligier JSP320",
            "car_class_id": 456,
            "series_id": 789
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_latest_session().await;

    assert!(result.is_ok());
    let session = result.unwrap();
    assert_eq!(session.track_name, "Mount Panorama");
    assert_eq!(session.car_name, "Ligier JSP320");
}

#[tokio::test]
async fn test_get_latest_session_not_found() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/telemetry/sessions/latest"))
        .respond_with(ResponseTemplate::new(404).set_body_string("No sessions found"))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_latest_session().await;

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(matches!(err, ApiError::NotFound(_)));
}

#[tokio::test]
async fn test_upload_metrics_success() {
    let mock_server = MockServer::start().await;
    let lap_id = Uuid::new_v4();

    Mock::given(method("POST"))
        .and(path("/api/v1/metrics/lap"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "success",
            "lap_metrics_id": "metrics-123",
            "message": "Metrics uploaded successfully"
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let metrics = create_test_lap_metrics();

    let result = client.upload_metrics(&metrics, lap_id).await;

    assert!(result.is_ok());
    let response = result.unwrap();
    assert_eq!(response.lap_metrics_id, "metrics-123");
}

#[tokio::test]
async fn test_get_lap_metrics_success() {
    let mock_server = MockServer::start().await;
    let lap_id = Uuid::new_v4();

    Mock::given(method("GET"))
        .and(path(format!("/api/v1/metrics/lap/{}", lap_id)))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "lap_id": lap_id.to_string(),
            "lap_time": 90.5,
            "max_speed": 85.0,
            "min_speed": 35.0,
            "average_corner_speed": 45.0,
            "total_corners": 1,
            "total_braking_zones": 1,
            "braking_zones": [],
            "corners": []
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_lap_metrics(lap_id).await;

    assert!(result.is_ok());
}

#[tokio::test]
async fn test_get_lap_metrics_not_found() {
    let mock_server = MockServer::start().await;
    let lap_id = Uuid::new_v4();

    Mock::given(method("GET"))
        .and(path(format!("/api/v1/metrics/lap/{}", lap_id)))
        .respond_with(ResponseTemplate::new(404).set_body_string("Metrics not found"))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_lap_metrics(lap_id).await;

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(matches!(err, ApiError::NotFound(_)));
}

#[tokio::test]
async fn test_list_sessions_success() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/sessions"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "sessions": [
                {
                    "session_id": Uuid::new_v4().to_string(),
                    "track_id": 142,
                    "track_name": "Mount Panorama",
                    "track_config_name": "Full Circuit",
                    "track_type": "road course",
                    "car_id": 123,
                    "car_name": "Ligier JSP320",
                    "car_class_id": 456,
                    "series_id": 789,
                    "lap_count": 5,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                {
                    "session_id": Uuid::new_v4().to_string(),
                    "track_id": 200,
                    "track_name": "Spa-Francorchamps",
                    "track_config_name": null,
                    "track_type": "road course",
                    "car_id": 200,
                    "car_name": "Ferrari 488 GT3",
                    "car_class_id": 100,
                    "series_id": 500,
                    "lap_count": 10,
                    "created_at": "2024-01-14T14:00:00Z"
                }
            ],
            "total": 2
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.list_sessions().await;

    assert!(result.is_ok());
    let response = result.unwrap();
    assert_eq!(response.total, 2);
    assert_eq!(response.sessions.len(), 2);
}

#[tokio::test]
async fn test_get_session_success() {
    let mock_server = MockServer::start().await;
    let session_id = Uuid::new_v4();

    Mock::given(method("GET"))
        .and(path(format!("/api/v1/sessions/{}", session_id)))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "session_id": session_id.to_string(),
            "track_id": 142,
            "track_name": "Mount Panorama",
            "track_config_name": "Full Circuit",
            "track_type": "road course",
            "car_id": 123,
            "car_name": "Ligier JSP320",
            "car_class_id": 456,
            "series_id": 789,
            "laps": [
                {
                    "lap_id": Uuid::new_v4().to_string(),
                    "lap_number": 1,
                    "lap_time": 90.5,
                    "is_valid": true,
                    "has_metrics": true,
                    "created_at": "2024-01-15T10:31:00Z"
                }
            ],
            "created_at": "2024-01-15T10:30:00Z"
        })))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_session(session_id).await;

    assert!(result.is_ok());
    let response = result.unwrap();
    assert_eq!(response.session_id, session_id.to_string());
}

#[tokio::test]
async fn test_get_session_not_found() {
    let mock_server = MockServer::start().await;
    let session_id = Uuid::new_v4();

    Mock::given(method("GET"))
        .and(path(format!("/api/v1/sessions/{}", session_id)))
        .respond_with(ResponseTemplate::new(404).set_body_string("Session not found"))
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());
    let result = client.get_session(session_id).await;

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(matches!(err, ApiError::NotFound(_)));
}

#[tokio::test]
async fn test_concurrent_requests() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/health"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "healthy"
        })))
        .expect(3)
        .mount(&mock_server)
        .await;

    let client = RacingCoachClient::new(mock_server.uri());

    // Make concurrent requests
    let (r1, r2, r3): (
        Result<HealthResponse, ApiError>,
        Result<HealthResponse, ApiError>,
        Result<HealthResponse, ApiError>,
    ) = tokio::join!(
        client.health_check(),
        client.health_check(),
        client.health_check()
    );

    assert!(r1.is_ok());
    assert!(r2.is_ok());
    assert!(r3.is_ok());
}

#[tokio::test]
async fn test_client_with_custom_client() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/api/v1/health"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "ok"
        })))
        .mount(&mock_server)
        .await;

    let reqwest_client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .unwrap();

    let client = RacingCoachClient::with_client(reqwest_client, mock_server.uri());
    let result = client.health_check().await;

    assert!(result.is_ok());
}
