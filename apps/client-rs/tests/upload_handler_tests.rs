//! Integration tests for lap upload and metrics upload handlers.

use async_trait::async_trait;
use chrono::Utc;
use racing_coach_client::api::RacingCoachClient;
use racing_coach_client::events::{
    BrakingMetrics, CornerMetrics, Event, EventBus, EventHandler, HandlerContext, HandlerError,
    LapMetricsExtractedPayload, LapMetricsPayload, LapTelemetryPayload, LapTelemetrySequencePayload,
    SessionInfo, TelemetryFrame,
};
use racing_coach_client::handlers::{LapUploadHandler, MetricsUploadHandler};
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use tokio::time::{timeout, Duration};
use uuid::Uuid;
use wiremock::matchers::{method, path_regex};
use wiremock::{Mock, MockServer, ResponseTemplate};

// ============================================================================
// Test Helpers
// ============================================================================

fn create_test_session() -> SessionInfo {
    SessionInfo {
        session_id: Uuid::new_v4(),
        timestamp: Utc::now(),
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

fn create_test_frame(lap: i32, distance_pct: f32) -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time: 100.0 + distance_pct as f64 * 90.0,
        lap_number: lap,
        lap_distance_pct: distance_pct,
        lap_distance: distance_pct * 5000.0,
        current_lap_time: distance_pct * 90.0,
        last_lap_time: 90.0,
        best_lap_time: 88.0,
        speed: 50.0 + distance_pct * 30.0,
        rpm: 7500.0,
        gear: 4,
        throttle: 0.8,
        brake: 0.0,
        clutch: 0.0,
        steering_angle: 0.0,
        lateral_acceleration: distance_pct * 10.0,
        longitudinal_acceleration: 2.0,
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

fn create_lap_telemetry_payload(lap_number: i32, frame_count: usize) -> LapTelemetrySequencePayload {
    let frames: Vec<TelemetryFrame> = (0..frame_count)
        .map(|i| create_test_frame(lap_number, i as f32 / frame_count as f32))
        .collect();

    LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames: Arc::new(frames),
            lap_time: Some(90.5),
        },
        session: create_test_session(),
        lap_id: Uuid::new_v4(),
    }
}

fn create_lap_metrics_payload(lap_number: i32) -> LapMetricsExtractedPayload {
    LapMetricsExtractedPayload {
        metrics: LapMetricsPayload {
            lap_number,
            lap_time: Some(90.5),
            max_speed: 85.0,
            min_speed: 25.0,
            average_corner_speed: 50.0,
            total_corners: 10,
            total_braking_zones: 8,
            braking_zones: vec![BrakingMetrics {
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
            }],
            corners: vec![CornerMetrics {
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
            }],
        },
        session: create_test_session(),
        lap_id: Uuid::new_v4(),
    }
}

/// Handler that counts processed events
struct EventCountingHandler {
    lap_sequences: AtomicU32,
    metrics_extracted: AtomicU32,
}

impl EventCountingHandler {
    fn new() -> Self {
        Self {
            lap_sequences: AtomicU32::new(0),
            metrics_extracted: AtomicU32::new(0),
        }
    }

    fn lap_sequence_count(&self) -> u32 {
        self.lap_sequences.load(Ordering::SeqCst)
    }

    fn metrics_extracted_count(&self) -> u32 {
        self.metrics_extracted.load(Ordering::SeqCst)
    }
}

#[async_trait]
impl EventHandler for EventCountingHandler {
    fn name(&self) -> &'static str {
        "EventCountingHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::LapTelemetrySequence(_) => {
                self.lap_sequences.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            }
            Event::LapMetricsExtracted(_) => {
                self.metrics_extracted.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            }
            _ => Ok(false),
        }
    }
}

// ============================================================================
// LapUploadHandler Tests
// ============================================================================

#[tokio::test]
async fn test_lap_upload_handler_success() {
    let mock_server = MockServer::start().await;

    // Set up mock response
    Mock::given(method("POST"))
        .and(path_regex("/api/v1/telemetry/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Lap uploaded",
            "lap_id": "550e8400-e29b-41d4-a716-446655440000"
        })))
        .expect(1)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = LapUploadHandler::new(client);

    // Create event bus and run handler
    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Publish lap telemetry event
    let payload = create_lap_telemetry_payload(5, 100);
    event_bus
        .publish(Event::LapTelemetrySequence(payload))
        .await
        .unwrap();

    // Wait for processing
    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_lap_upload_handler_server_error() {
    let mock_server = MockServer::start().await;

    // Set up error response
    Mock::given(method("POST"))
        .and(path_regex("/api/v1/telemetry/lap.*"))
        .respond_with(ResponseTemplate::new(500).set_body_json(serde_json::json!({
            "error": "Internal server error"
        })))
        .expect(1)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = LapUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Handler should not panic on server error
    let payload = create_lap_telemetry_payload(5, 50);
    event_bus
        .publish(Event::LapTelemetrySequence(payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_lap_upload_handler_disabled() {
    let mock_server = MockServer::start().await;

    // Mock should NOT be called
    Mock::given(method("POST"))
        .and(path_regex("/api/v1/telemetry/lap.*"))
        .respond_with(ResponseTemplate::new(200))
        .expect(0)
        .mount(&mock_server)
        .await;

    let handler = LapUploadHandler::disabled();

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let payload = create_lap_telemetry_payload(5, 50);
    event_bus
        .publish(Event::LapTelemetrySequence(payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_lap_upload_handler_multiple_laps() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/telemetry/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Lap uploaded",
            "lap_id": "test-lap-id"
        })))
        .expect(3)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = LapUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Upload 3 laps
    for lap in 1..=3 {
        let payload = create_lap_telemetry_payload(lap, 50);
        event_bus
            .publish(Event::LapTelemetrySequence(payload))
            .await
            .unwrap();
    }

    tokio::time::sleep(Duration::from_millis(300)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_lap_upload_handler_ignores_other_events() {
    let mock_server = MockServer::start().await;

    // No upload should be called
    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(200))
        .expect(0)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = LapUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Publish non-lap events
    event_bus
        .publish(Event::SessionStart(create_test_session()))
        .await
        .unwrap();
    event_bus
        .publish(Event::SessionEnd {
            session_id: Uuid::new_v4(),
        })
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

// ============================================================================
// MetricsUploadHandler Tests
// ============================================================================

#[tokio::test]
async fn test_metrics_upload_handler_success() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/metrics/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Metrics uploaded",
            "lap_metrics_id": "metrics-123"
        })))
        .expect(1)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = MetricsUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let payload = create_lap_metrics_payload(5);
    event_bus
        .publish(Event::LapMetricsExtracted(payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_metrics_upload_handler_server_error() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/metrics/lap.*"))
        .respond_with(ResponseTemplate::new(500))
        .expect(1)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = MetricsUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Handler should not panic on server error
    let payload = create_lap_metrics_payload(5);
    event_bus
        .publish(Event::LapMetricsExtracted(payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_metrics_upload_handler_disabled() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(200))
        .expect(0)
        .mount(&mock_server)
        .await;

    let handler = MetricsUploadHandler::disabled();

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let payload = create_lap_metrics_payload(5);
    event_bus
        .publish(Event::LapMetricsExtracted(payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_metrics_upload_handler_multiple_laps() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/metrics/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Metrics uploaded",
            "lap_metrics_id": "metrics-id"
        })))
        .expect(5)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = MetricsUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Upload metrics for 5 laps
    for lap in 1..=5 {
        let payload = create_lap_metrics_payload(lap);
        event_bus
            .publish(Event::LapMetricsExtracted(payload))
            .await
            .unwrap();
    }

    tokio::time::sleep(Duration::from_millis(500)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_metrics_upload_handler_ignores_other_events() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(200))
        .expect(0)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let handler = MetricsUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> = vec![Arc::new(handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Publish non-metrics events
    event_bus
        .publish(Event::SessionStart(create_test_session()))
        .await
        .unwrap();
    let lap_payload = create_lap_telemetry_payload(1, 10);
    event_bus
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

// ============================================================================
// Combined Handler Tests
// ============================================================================

#[tokio::test]
async fn test_both_handlers_together() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/telemetry/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Lap uploaded",
            "lap_id": "lap-id"
        })))
        .expect(1)
        .mount(&mock_server)
        .await;

    Mock::given(method("POST"))
        .and(path_regex("/api/v1/metrics/lap.*"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "success",
            "message": "Metrics uploaded",
            "lap_metrics_id": "metrics-id"
        })))
        .expect(1)
        .mount(&mock_server)
        .await;

    let client = Arc::new(RacingCoachClient::new(&mock_server.uri()));
    let lap_handler = LapUploadHandler::new(client.clone());
    let metrics_handler = MetricsUploadHandler::new(client);

    let event_bus = Arc::new(EventBus::new());
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![Arc::new(lap_handler), Arc::new(metrics_handler)];

    let bus = event_bus.clone();
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Publish both event types
    let lap_payload = create_lap_telemetry_payload(5, 50);
    event_bus
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    let metrics_payload = create_lap_metrics_payload(5);
    event_bus
        .publish(Event::LapMetricsExtracted(metrics_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(300)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;
}

#[tokio::test]
async fn test_handler_enable_disable_toggle() {
    let client = Arc::new(RacingCoachClient::new("http://localhost:8000"));
    let mut handler = LapUploadHandler::new(client);

    assert!(handler.name() == "LapUploadHandler");

    handler.set_enabled(false);
    // Can't directly test enabled field, but disabled handler shouldn't make requests

    handler.set_enabled(true);
    // Re-enabled
}

#[tokio::test]
async fn test_metrics_handler_enable_disable_toggle() {
    let client = Arc::new(RacingCoachClient::new("http://localhost:8000"));
    let mut handler = MetricsUploadHandler::new(client);

    assert!(handler.name() == "MetricsUploadHandler");

    handler.set_enabled(false);
    handler.set_enabled(true);
}
