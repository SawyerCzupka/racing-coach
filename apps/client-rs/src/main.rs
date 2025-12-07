mod api;
mod events;

use async_trait::async_trait;
use chrono::Utc;
use futures::StreamExt;
use pitwall::{PitwallFrame, UpdateRate};
use std::sync::Arc;
use uuid::Uuid;

use events::{
    Event, EventBus, EventHandler, HandlerContext, HandlerError, SessionInfo, TelemetryEventPayload,
    TelemetryFrame,
};

#[derive(PitwallFrame, Debug)]
struct CarData {
    #[field_name = "Speed"]
    #[calculated = "Speed * 3.6"]
    speed: f32,

    #[field_name = "Brake"]
    brake: f32,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    println!("Hello, world!");

    let my_client = api::client::MyClient {
        client: reqwest::Client::new(),
    };
    println!("{}", my_client.healthcheck().await);

    let ibt_path =
        std::path::Path::new("../../sample_data/ligierjsp320_bathurst 2025-11-17 18-15-16.ibt");

    let connection = pitwall::Pitwall::open(ibt_path, 10.0).await.unwrap();

    let mut stream = connection.subscribe::<CarData>(UpdateRate::Native);

    let mut max_speed: f32 = -1.0;

    while let Some(frame) = stream.next().await {
        println!("Speed: {} | Brake: {}", frame.speed, frame.brake);
        if frame.speed > max_speed {
            max_speed = frame.speed;
        }
    }

    println!("Max Speed: {}", max_speed);

    // --- Event Bus Demonstration ---
    println!("\n=== Event Bus Demonstration ===\n");

    // Create event bus
    let event_bus = Arc::new(EventBus::new());

    // Create and register handlers
    let logger_handler: Arc<dyn EventHandler> = Arc::new(LoggerHandler);

    let handlers = vec![logger_handler];

    // Spawn the event loop
    let bus = event_bus.clone();
    let event_loop_handle = tokio::spawn(async move {
        bus.run(handlers).await;
    });

    // Get a publisher for sending events
    let publisher = event_bus.publisher();

    // Publish some example events
    println!("Publishing SessionStart event...");
    publisher
        .publish(Event::SessionStart(SessionInfo {
            session_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            track_id: 142,
            track_name: "Bathurst".to_string(),
            track_config_name: None,
            track_type: "road course".to_string(),
            car_id: 123,
            car_name: "Ligier JSP320".to_string(),
            car_class_id: 456,
            series_id: 789,
        }))
        .await
        .unwrap();

    // Wait a bit for processing
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    println!("Publishing TelemetryEvent...");
    let session_id = Uuid::new_v4();
    publisher
        .publish(Event::TelemetryEvent(TelemetryEventPayload {
            frame: TelemetryFrame {
                timestamp: Utc::now(),
                session_time: 10.5,
                lap_number: 1,
                lap_distance_pct: 0.25,
                lap_distance: 1500.0,
                current_lap_time: 45.2,
                last_lap_time: 0.0,
                best_lap_time: 0.0,
                speed: 220.0,
                rpm: 8500.0,
                gear: 5,
                throttle: 0.85,
                brake: 0.0,
                clutch: 0.0,
                steering_angle: 0.15,
                lateral_acceleration: 2.5,
                longitudinal_acceleration: 0.5,
                vertical_acceleration: -0.2,
                yaw_rate: 0.1,
                roll_rate: 0.05,
                pitch_rate: 0.02,
                velocity_x: 60.0,
                velocity_y: 0.5,
                velocity_z: -0.2,
                yaw: 1.2,
                pitch: 0.05,
                roll: 0.03,
                track_temp: 28.5,
                air_temp: 24.0,
                on_pit_road: false,
            },
            session_id,
        }))
        .await
        .unwrap();

    // Wait a bit for processing
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    println!("Publishing SessionEnd event...");
    publisher
        .publish(Event::SessionEnd { session_id })
        .await
        .unwrap();

    // Wait a bit for final processing
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    // Shutdown the event bus
    println!("\nShutting down event bus...");
    event_bus.shutdown();

    // Wait for event loop to complete
    event_loop_handle.await.unwrap();

    println!("Event bus demonstration complete!");
}

/// Simple handler that logs all events
struct LoggerHandler;

#[async_trait]
impl EventHandler for LoggerHandler {
    fn name(&self) -> &'static str {
        "LoggerHandler"
    }

    async fn handle(&self, event: &Event, ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::SessionStart(session) => {
                println!(
                    "[{}] SessionStart: {} at {}",
                    ctx.timestamp.format("%H:%M:%S"),
                    session.track_name,
                    session.car_name
                );
                Ok(true)
            }
            Event::TelemetryEvent(payload) => {
                println!(
                    "[{}] TelemetryEvent: Lap {} - Speed: {:.1} km/h, Throttle: {:.0}%",
                    ctx.timestamp.format("%H:%M:%S"),
                    payload.frame.lap_number,
                    payload.frame.speed,
                    payload.frame.throttle * 100.0
                );
                Ok(true)
            }
            Event::SessionEnd { session_id } => {
                println!(
                    "[{}] SessionEnd: session_id = {}",
                    ctx.timestamp.format("%H:%M:%S"),
                    session_id
                );
                Ok(true)
            }
            Event::TelemetryFrame(_) => {
                println!("[{}] TelemetryFrame (raw)", ctx.timestamp.format("%H:%M:%S"));
                Ok(true)
            }
            Event::LapTelemetrySequence(payload) => {
                println!(
                    "[{}] LapTelemetrySequence: {} frames",
                    ctx.timestamp.format("%H:%M:%S"),
                    payload.lap_telemetry.frames.len()
                );
                Ok(true)
            }
            Event::LapMetricsExtracted(payload) => {
                println!(
                    "[{}] LapMetricsExtracted: Lap {} - {} corners, {} braking zones",
                    ctx.timestamp.format("%H:%M:%S"),
                    payload.metrics.lap_number,
                    payload.metrics.total_corners,
                    payload.metrics.total_braking_zones
                );
                Ok(true)
            }
        }
    }
}
