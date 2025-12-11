//! Integration tests for the event bus system.

use async_trait::async_trait;
use chrono::Utc;
use racing_coach_client::events::{
    Event, EventBus, EventHandler, HandlerContext, HandlerError, SessionInfo,
    TelemetryEventPayload, TelemetryFrame,
};
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use tokio::time::{timeout, Duration};
use uuid::Uuid;

/// Test handler that counts events
struct CountingHandler {
    session_starts: AtomicU32,
    telemetry_events: AtomicU32,
    session_ends: AtomicU32,
}

impl CountingHandler {
    fn new() -> Self {
        Self {
            session_starts: AtomicU32::new(0),
            telemetry_events: AtomicU32::new(0),
            session_ends: AtomicU32::new(0),
        }
    }

    fn session_start_count(&self) -> u32 {
        self.session_starts.load(Ordering::SeqCst)
    }

    fn telemetry_event_count(&self) -> u32 {
        self.telemetry_events.load(Ordering::SeqCst)
    }

    fn session_end_count(&self) -> u32 {
        self.session_ends.load(Ordering::SeqCst)
    }
}

#[async_trait]
impl EventHandler for CountingHandler {
    fn name(&self) -> &'static str {
        "CountingHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::SessionStart(_) => {
                self.session_starts.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            }
            Event::TelemetryEvent(_) => {
                self.telemetry_events.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            }
            Event::SessionEnd { .. } => {
                self.session_ends.fetch_add(1, Ordering::SeqCst);
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
        track_config_name: None,
        track_type: "road course".to_string(),
        car_id: 123,
        car_name: "Ligier JSP320".to_string(),
        car_class_id: 456,
        series_id: 789,
    }
}

fn create_test_frame(lap: i32, distance_pct: f32) -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time: 100.0,
        lap_number: lap,
        lap_distance_pct: distance_pct,
        lap_distance: distance_pct * 5000.0,
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

#[tokio::test]
async fn test_event_bus_basic_flow() {
    let event_bus = Arc::new(EventBus::new());
    let handler = Arc::new(CountingHandler::new());

    // Start event loop
    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    // Wait for event loop to start
    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    // Publish session start
    let session = create_test_session();
    let session_id = session.session_id;
    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    // Wait for processing
    tokio::time::sleep(Duration::from_millis(50)).await;

    // Publish some telemetry events
    for i in 0..5 {
        let frame = create_test_frame(1, i as f32 * 0.2);
        publisher
            .publish(Event::TelemetryEvent(TelemetryEventPayload {
                frame,
                session_id,
            }))
            .await
            .unwrap();
    }

    // Wait for processing
    tokio::time::sleep(Duration::from_millis(100)).await;

    // Publish session end
    publisher
        .publish(Event::SessionEnd { session_id })
        .await
        .unwrap();

    // Wait for processing
    tokio::time::sleep(Duration::from_millis(50)).await;

    // Shutdown
    event_bus.shutdown();

    // Wait for event loop to finish
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // Verify counts
    assert_eq!(handler.session_start_count(), 1);
    assert_eq!(handler.telemetry_event_count(), 5);
    assert_eq!(handler.session_end_count(), 1);
}

#[tokio::test]
async fn test_event_bus_multiple_handlers() {
    let event_bus = Arc::new(EventBus::new());
    let handler1 = Arc::new(CountingHandler::new());
    let handler2 = Arc::new(CountingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> = vec![handler1.clone(), handler2.clone()];
    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();
    let session = create_test_session();
    publisher
        .publish(Event::SessionStart(session))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(100)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // Both handlers should receive the event
    assert_eq!(handler1.session_start_count(), 1);
    assert_eq!(handler2.session_start_count(), 1);
}
