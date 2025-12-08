//! Integration tests for the metrics handler.

use async_trait::async_trait;
use chrono::Utc;
use racing_coach_client::events::{
    Event, EventBus, EventHandler, HandlerContext, HandlerError, LapMetricsExtractedPayload,
    LapTelemetryPayload, LapTelemetrySequencePayload, SessionInfo, TelemetryFrame,
};
use racing_coach_client::handlers::MetricsHandler;
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{timeout, Duration};
use uuid::Uuid;

/// Test handler that captures metrics events
struct MetricsCapturingHandler {
    metrics_events: RwLock<Vec<LapMetricsExtractedPayload>>,
    event_count: AtomicU32,
}

impl MetricsCapturingHandler {
    fn new() -> Self {
        Self {
            metrics_events: RwLock::new(Vec::new()),
            event_count: AtomicU32::new(0),
        }
    }

    async fn captured_metrics(&self) -> Vec<LapMetricsExtractedPayload> {
        self.metrics_events.read().await.clone()
    }
}

#[async_trait]
impl EventHandler for MetricsCapturingHandler {
    fn name(&self) -> &'static str {
        "MetricsCapturingHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        self.event_count.fetch_add(1, Ordering::SeqCst);
        match event {
            Event::LapMetricsExtracted(payload) => {
                let mut metrics = self.metrics_events.write().await;
                metrics.push(payload.clone());
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
    lap_distance_pct: f32,
    speed: f32,
    brake: f32,
    throttle: f32,
    steering: f32,
    lat_accel: f32,
    session_time: f64,
) -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time,
        lap_number: 1,
        lap_distance_pct,
        lap_distance: lap_distance_pct * 5000.0,
        current_lap_time: session_time as f32,
        last_lap_time: 0.0,
        best_lap_time: 0.0,
        speed,
        rpm: 7500.0,
        gear: 4,
        throttle,
        brake,
        clutch: 0.0,
        steering_angle: steering,
        lateral_acceleration: lat_accel,
        longitudinal_acceleration: if brake > 0.0 { -15.0 } else { 5.0 },
        vertical_acceleration: 0.0,
        yaw_rate: steering * 0.1,
        roll_rate: 0.0,
        pitch_rate: 0.0,
        velocity_x: speed,
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

/// Create a lap with realistic braking zones and corners
fn create_realistic_lap_frames() -> Vec<TelemetryFrame> {
    let mut frames = Vec::new();
    let mut session_time = 0.0;
    let time_step = 0.016; // ~60Hz

    // Segment 1: Straight at high speed
    for i in 0..50 {
        let pct = i as f32 * 0.002; // 0% to 10%
        frames.push(create_test_frame(
            pct,
            80.0, // high speed
            0.0,  // no braking
            1.0,  // full throttle
            0.0,  // no steering
            0.0,  // no lateral G
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 2: Heavy braking zone
    for i in 0..25 {
        let pct = 0.10 + i as f32 * 0.002; // 10% to 15%
        let speed = 80.0 - i as f32 * 1.5; // Decelerating
        frames.push(create_test_frame(
            pct,
            speed,
            0.9, // heavy braking
            0.0,
            0.0,
            -15.0, // deceleration G
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 3: Trail braking into corner (braking + steering)
    for i in 0..15 {
        let pct = 0.15 + i as f32 * 0.002;
        let speed = 42.0 - i as f32 * 0.3;
        let brake_pressure = 0.9 - i as f32 * 0.05;
        let steering = 0.1 + i as f32 * 0.02;
        frames.push(create_test_frame(
            pct,
            speed,
            brake_pressure.max(0.1),
            0.0,
            steering,
            8.0 + i as f32 * 0.5, // Building lateral G
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 4: Corner apex (high lateral G, some steering, building throttle)
    for i in 0..30 {
        let pct = 0.18 + i as f32 * 0.002;
        let t = i as f32 / 30.0;
        let lateral_g = 15.0 * (t * std::f32::consts::PI).sin(); // Peak at middle
        let steering = 0.4 * (1.0 - (t - 0.5).abs() * 2.0).max(0.2);
        let speed = 38.0 + i as f32 * 0.3;
        frames.push(create_test_frame(
            pct,
            speed,
            0.0,
            0.2 + t * 0.6, // Gradually applying throttle
            steering,
            lateral_g,
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 5: Corner exit - full throttle acceleration
    for i in 0..25 {
        let pct = 0.24 + i as f32 * 0.002;
        let speed = 47.0 + i as f32 * 1.2;
        let steering = 0.2 * (1.0 - i as f32 / 25.0);
        let lat_g = 8.0 * (1.0 - i as f32 / 25.0);
        frames.push(create_test_frame(
            pct,
            speed,
            0.0,
            1.0,
            steering,
            lat_g,
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 6: Another straight
    for i in 0..100 {
        let pct = 0.29 + i as f32 * 0.003;
        frames.push(create_test_frame(
            pct,
            77.0,
            0.0,
            1.0,
            0.0,
            0.0,
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 7: Second braking zone
    for i in 0..20 {
        let pct = 0.59 + i as f32 * 0.002;
        let speed = 77.0 - i as f32 * 1.8;
        frames.push(create_test_frame(
            pct,
            speed,
            0.85,
            0.0,
            0.0,
            -12.0,
            session_time,
        ));
        session_time += time_step;
    }

    // Segment 8: Second corner
    for i in 0..35 {
        let pct = 0.63 + i as f32 * 0.002;
        let t = i as f32 / 35.0;
        let lateral_g = 12.0 * (t * std::f32::consts::PI).sin();
        let steering = -0.35 * (1.0 - (t - 0.5).abs() * 2.0).max(0.15); // Left turn
        let speed = 41.0 + t * 15.0;
        frames.push(create_test_frame(
            pct,
            speed,
            0.0,
            0.3 + t * 0.7,
            steering,
            lateral_g,
            session_time,
        ));
        session_time += time_step;
    }

    // Fill rest with straight driving
    while frames.len() < 500 {
        let last_pct = frames.last().map(|f| f.lap_distance_pct).unwrap_or(0.7);
        let pct = last_pct + 0.001;
        if pct >= 1.0 {
            break;
        }
        frames.push(create_test_frame(
            pct.min(0.99),
            75.0,
            0.0,
            1.0,
            0.0,
            0.0,
            session_time,
        ));
        session_time += time_step;
    }

    frames
}

#[tokio::test]
async fn test_metrics_handler_detects_braking_zones() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    // Create and publish lap telemetry
    let session = create_test_session();
    let frames = Arc::new(create_realistic_lap_frames());
    let lap_time = frames.last().map(|f| f.session_time).unwrap_or(90.0);

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: Some(lap_time),
        },
        session,
        lap_id: Uuid::new_v4(),
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 1, "Expected 1 metrics extraction");

    let metrics = &captured[0].metrics;

    // Should detect braking zones
    assert!(
        metrics.total_braking_zones >= 1,
        "Expected at least 1 braking zone, got {}",
        metrics.total_braking_zones
    );

    // Verify braking zone properties
    for zone in &metrics.braking_zones {
        assert!(
            zone.max_brake_pressure > 0.5,
            "Braking zone should have significant brake pressure"
        );
        assert!(
            zone.braking_point_speed > zone.minimum_speed,
            "Entry speed should be greater than minimum speed"
        );
    }
}

#[tokio::test]
async fn test_metrics_handler_detects_corners() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();
    let frames = Arc::new(create_realistic_lap_frames());
    let lap_time = frames.last().map(|f| f.session_time).unwrap_or(90.0);

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: Some(lap_time),
        },
        session,
        lap_id: Uuid::new_v4(),
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 1);

    let metrics = &captured[0].metrics;

    // Should detect corners
    assert!(
        metrics.total_corners >= 1,
        "Expected at least 1 corner, got {}",
        metrics.total_corners
    );

    // Verify corner properties
    for corner in &metrics.corners {
        assert!(
            corner.max_lateral_g > 0.5,
            "Corner should have significant lateral G"
        );
        assert!(
            corner.apex_distance >= corner.turn_in_distance,
            "Apex should be after turn-in"
        );
        assert!(
            corner.exit_distance >= corner.apex_distance,
            "Exit should be after apex"
        );
    }
}

#[tokio::test]
async fn test_metrics_handler_detects_trail_braking() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();
    let frames = Arc::new(create_realistic_lap_frames());
    let lap_time = frames.last().map(|f| f.session_time).unwrap_or(90.0);

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: Some(lap_time),
        },
        session,
        lap_id: Uuid::new_v4(),
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 1);

    let metrics = &captured[0].metrics;

    // The first braking zone should have trail braking
    let trail_braking_zones: Vec<_> = metrics
        .braking_zones
        .iter()
        .filter(|z| z.has_trail_braking)
        .collect();

    assert!(
        !trail_braking_zones.is_empty(),
        "Expected at least one braking zone with trail braking"
    );
}

#[tokio::test]
async fn test_metrics_handler_calculates_speed_range() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();
    let frames = Arc::new(create_realistic_lap_frames());
    let lap_time = frames.last().map(|f| f.session_time).unwrap_or(90.0);

    // Calculate expected speed range from frames
    let expected_max: f32 = frames.iter().map(|f| f.speed).fold(0.0, f32::max);
    let expected_min: f32 = frames.iter().map(|f| f.speed).fold(f32::MAX, f32::min);

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: Some(lap_time),
        },
        session,
        lap_id: Uuid::new_v4(),
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 1);

    let metrics = &captured[0].metrics;

    assert!(
        (metrics.max_speed - expected_max).abs() < 0.1,
        "Max speed mismatch: {} vs {}",
        metrics.max_speed,
        expected_max
    );
    assert!(
        (metrics.min_speed - expected_min).abs() < 0.1,
        "Min speed mismatch: {} vs {}",
        metrics.min_speed,
        expected_min
    );
}

#[tokio::test]
async fn test_metrics_handler_preserves_lap_id() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();
    let lap_id = Uuid::new_v4();
    let frames = Arc::new(create_realistic_lap_frames());

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: Some(90.0),
        },
        session: session.clone(),
        lap_id,
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 1);

    // Verify lap_id is preserved
    assert_eq!(captured[0].lap_id, lap_id);
    // Verify session is preserved
    assert_eq!(captured[0].session.session_id, session.session_id);
}

#[tokio::test]
async fn test_metrics_handler_empty_frames() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();
    let frames: Arc<Vec<TelemetryFrame>> = Arc::new(Vec::new()); // Empty frames

    let lap_payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames,
            lap_time: None,
        },
        session,
        lap_id: Uuid::new_v4(),
    };

    publisher
        .publish(Event::LapTelemetrySequence(lap_payload))
        .await
        .unwrap();

    tokio::time::sleep(Duration::from_millis(200)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    // Should not crash, but no metrics should be extracted
    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 0, "Empty frames should not produce metrics");
}

#[tokio::test]
async fn test_metrics_handler_multiple_laps() {
    let event_bus = Arc::new(EventBus::new());
    let metrics_handler = Arc::new(MetricsHandler::new());
    let capturing_handler = Arc::new(MetricsCapturingHandler::new());

    let bus = event_bus.clone();
    let handlers: Vec<Arc<dyn EventHandler>> =
        vec![metrics_handler.clone(), capturing_handler.clone()];

    let event_loop = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    tokio::time::sleep(Duration::from_millis(50)).await;

    let publisher = event_bus.publisher();

    let session = create_test_session();

    // Publish 3 lap telemetry events
    for i in 0..3 {
        let frames = Arc::new(create_realistic_lap_frames());
        let lap_payload = LapTelemetrySequencePayload {
            lap_telemetry: LapTelemetryPayload {
                frames,
                lap_time: Some(90.0 + i as f64),
            },
            session: session.clone(),
            lap_id: Uuid::new_v4(),
        };

        publisher
            .publish(Event::LapTelemetrySequence(lap_payload))
            .await
            .unwrap();
    }

    tokio::time::sleep(Duration::from_millis(300)).await;

    event_bus.shutdown();
    let _ = timeout(Duration::from_secs(2), event_loop).await;

    let captured = capturing_handler.captured_metrics().await;
    assert_eq!(captured.len(), 3, "Expected 3 metrics extractions");
}
