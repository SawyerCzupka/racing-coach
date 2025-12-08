//! Integration tests for the lap handler.

use async_trait::async_trait;
use chrono::Utc;
use racing_coach_client::events::{
    Event, EventBus, EventHandler, HandlerContext, HandlerError, LapTelemetrySequencePayload,
    SessionInfo, TelemetryEventPayload, TelemetryFrame,
};
use racing_coach_client::handlers::LapHandler;
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{timeout, Duration};
use uuid::Uuid;

/// Test handler that captures lap events
struct LapCapturingHandler {
    lap_events: RwLock<Vec<LapTelemetrySequencePayload>>,
    event_count: AtomicU32,
}

impl LapCapturingHandler {
    fn new() -> Self {
        Self {
            lap_events: RwLock::new(Vec::new()),
            event_count: AtomicU32::new(0),
        }
    }

    async fn captured_laps(&self) -> Vec<LapTelemetrySequencePayload> {
        self.lap_events.read().await.clone()
    }
}

#[async_trait]
impl EventHandler for LapCapturingHandler {
    fn name(&self) -> &'static str {
        "LapCapturingHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        self.event_count.fetch_add(1, Ordering::SeqCst);
        match event {
            Event::LapTelemetrySequence(payload) => {
                let mut laps = self.lap_events.write().await;
                laps.push(payload.clone());
                Ok(true)
            }
            _ => Ok(false),
        }
    }
}

fn create_test_session() -> SessionInfo {
    SessionInfo {
        session_id: Uuid::new_v4(),
        timestamp: Utc::now(),
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

fn create_test_frame(
    lap_number: i32,
    lap_distance_pct: f32,
    session_time: f64,
) -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time,
        lap_number,
        lap_distance_pct,
        lap_distance: lap_distance_pct * 5000.0,
        current_lap_time: session_time as f32,
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

#[tokio::test]
async fn test_lap_handler_detects_completed_lap() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    let session_id = session.session_id;

    // Start session
    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Simulate lap 1: frames from 0% to ~99% track distance
    for i in 0..100 {
        let frame = create_test_frame(1, i as f32 * 0.01, i as f64 * 0.9);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id,
            }))
            .await
            .unwrap();
    }

    // Simulate crossing start/finish line - new lap 2
    for i in 0..10 {
        let frame = create_test_frame(2, i as f32 * 0.01, 90.0 + i as f64 * 0.9);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id,
            }))
            .await
            .unwrap();
    }

    // Wait for event processing
    tokio::time::sleep(Duration::from_millis(200)).await;

    // Shutdown
    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // Verify lap was captured
    let captured = capturing_handler.captured_laps().await;
    assert_eq!(captured.len(), 1, "Expected 1 completed lap");

    let lap = &captured[0];
    assert_eq!(lap.lap_telemetry.frames.len(), 100);
}

#[tokio::test]
async fn test_lap_handler_multiple_laps() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    let session_id = session.session_id;

    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    let mut session_time = 0.0;

    // Simulate 3 complete laps
    for lap in 1..=4 {
        for i in 0..50 {
            let frame = create_test_frame(lap, i as f32 * 0.02, session_time);
            publisher
                .publish(Event::TelemetryEvent(TelemetryEventPayload {
                    frame,
                    session_id,
                }))
                .await
                .unwrap();
            session_time += 1.8;
        }
    }

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // Should have captured 3 complete laps (laps 1, 2, 3 - lap 4 is incomplete)
    let captured = capturing_handler.captured_laps().await;
    assert_eq!(captured.len(), 3, "Expected 3 completed laps");

    // Each lap should have 50 frames
    for (i, lap) in captured.iter().enumerate() {
        assert_eq!(
            lap.lap_telemetry.frames.len(),
            50,
            "Lap {} should have 50 frames",
            i + 1
        );
    }
}

#[tokio::test]
async fn test_lap_handler_ignores_incomplete_laps() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    let session_id = session.session_id;

    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Simulate returning to pits at lap 0 (low distance percentage)
    for i in 0..10 {
        let frame = create_test_frame(0, i as f32 * 0.01, i as f64);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id,
            }))
            .await
            .unwrap();
    }

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // No laps should be captured
    let captured = capturing_handler.captured_laps().await;
    assert_eq!(captured.len(), 0, "Expected no completed laps");
}

#[tokio::test]
async fn test_lap_handler_calculates_lap_time() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    let session_id = session.session_id;

    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Simulate lap 1: 90 seconds worth of frames
    let lap_start_time = 10.0;
    let lap_duration = 90.0;
    let num_frames = 100;

    for i in 0..num_frames {
        let session_time = lap_start_time + (i as f64 / num_frames as f64) * lap_duration;
        let frame = create_test_frame(1, i as f32 / num_frames as f32, session_time);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id,
            }))
            .await
            .unwrap();
    }

    // Start lap 2 to trigger lap 1 completion
    let frame = create_test_frame(2, 0.01, lap_start_time + lap_duration + 1.0);
    publisher
        .publish(Event::TelemetryEvent(TelemetryEventPayload {
            frame,
            session_id,
        }))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_laps().await;
    assert_eq!(captured.len(), 1);

    let lap = &captured[0];
    let lap_time = lap.lap_telemetry.lap_time.unwrap();

    // Lap time should be approximately 90 seconds (with some tolerance for frame boundaries)
    assert!(
        (lap_time - lap_duration).abs() < 2.0,
        "Lap time {} should be approximately {}",
        lap_time,
        lap_duration
    );
}

#[tokio::test]
async fn test_lap_handler_generates_unique_lap_ids() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    let session_id = session.session_id;

    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    let mut session_time = 0.0;

    // Simulate 3 complete laps
    for lap in 1..=4 {
        for i in 0..50 {
            let frame = create_test_frame(lap, i as f32 * 0.02, session_time);
            publisher
                .publish(Event::TelemetryEvent(TelemetryEventPayload {
                    frame,
                    session_id,
                }))
                .await
                .unwrap();
            session_time += 1.8;
        }
    }

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_laps().await;

    // All lap IDs should be unique
    let lap_ids: Vec<Uuid> = captured.iter().map(|l| l.lap_id).collect();
    let unique_ids: std::collections::HashSet<Uuid> = lap_ids.iter().cloned().collect();
    assert_eq!(lap_ids.len(), unique_ids.len(), "All lap IDs should be unique");
}

#[tokio::test]
async fn test_lap_handler_session_change_clears_buffer() {
    let event_bus = Arc::new(EventBus::new());
    let lap_handler = Arc::new(LapHandler::new());
    let capturing_handler = Arc::new(LapCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![lap_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    // First session
    let session1 = create_test_session();
    let session_id1 = session1.session_id;

    publisher
        .publish(Event::SessionStart(session1))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Partial lap in session 1
    for i in 0..50 {
        let frame = create_test_frame(1, i as f32 * 0.01, i as f64);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id: session_id1,
            }))
            .await
            .unwrap();
    }

    // New session starts (buffer should be cleared)
    let session2 = create_test_session();
    let session_id2 = session2.session_id;

    publisher
        .publish(Event::SessionStart(session2))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(50)).await;

    // Complete lap in session 2
    for i in 0..100 {
        let frame = create_test_frame(1, i as f32 * 0.01, 100.0 + i as f64);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id: session_id2,
            }))
            .await
            .unwrap();
    }

    // Trigger lap completion
    let frame = create_test_frame(2, 0.01, 300.0);
    publisher
        .publish(Event::TelemetryEvent(TelemetryEventPayload {
            frame,
            session_id: session_id2,
        }))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_laps().await;
    assert_eq!(captured.len(), 1, "Only session 2 lap should be captured");

    // Verify it's from session 2
    assert_eq!(captured[0].session.session_id, session_id2);
}
