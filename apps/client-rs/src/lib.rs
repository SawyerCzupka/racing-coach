mod config;
mod pos_service;

pub mod events;
pub mod handlers;
pub mod pitwall_ext;
pub mod telem;

pub use config::Config;
// pub use models::{Sample, SampleKind};
pub use pitwall_ext::AcceleratedReplayConnection;

use eventbus::{EventBus, HandlerRegistry};
use handlers::{LapHandler, LogHandler};
use pos_service::PositionService;
use telem::read_telemetry_eventbus;
use tokio::sync::watch;
use tokio::time::sleep;

use crate::pos_service::PositionState;

pub async fn run_events() {
    let bus = EventBus::new(10000);

    let (tx, rx) = watch::channel(PositionState::default());
    let mut pos_service = PositionService::new(rx.clone());

    // Set up handler registry
    let mut registry = HandlerRegistry::new();
    registry.register(LapHandler::new());
    registry.register(LogHandler::new(500));

    // Start all handlers
    let handles = registry.run(bus.clone());

    tokio::spawn(async move {
        let state = pos_service.wait_until_position(0.8).await;

        println!("[POS_SVC_USER] At 80% Lap Percentage!");
        println!("[POS_SVC_USER] State: {state}");
    });

    // Run telemetry collection (publisher)
    tokio::spawn(async move {
        read_telemetry_eventbus(bus, 40f64, tx).await;
    });

    sleep(std::time::Duration::from_secs(15)).await;

    println!("Continuing in run_events()...");

    // Signal shutdown
    registry.shutdown();

    // Wait for handlers to finish
    for handle in handles {
        let _ = handle.await;
    }
}

/// Main entry point for the library logic.
pub fn run(config: &Config) {
    println!("Server: {}", config.server_url);
}
