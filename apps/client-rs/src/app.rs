//! Main application orchestrator for Racing Coach Client.
//!
//! Coordinates telemetry collection, event handling, and server communication.

use std::sync::Arc;
use tokio::signal;
use tokio::sync::watch;
use tokio_util::sync::CancellationToken;
use tracing::{error, info, warn};

use crate::api::RacingCoachClient;
use crate::config::Config;
use crate::events::{EventBus, EventBusConfig, EventHandler};
use crate::handlers::{LapHandler, LapUploadHandler, MetricsHandler, MetricsUploadHandler};
use crate::telemetry::{TelemetryCollector, TelemetrySourceConfig};

/// Racing Coach Client application
pub struct RacingCoachApp {
    config: Config,
    event_bus: Arc<EventBus>,
    api_client: Arc<RacingCoachClient>,
    cancel: CancellationToken,
    shutdown_tx: watch::Sender<bool>,
}

impl RacingCoachApp {
    /// Create a new application instance
    pub fn new(config: Config) -> Self {
        let event_bus = Arc::new(EventBus::with_config(EventBusConfig {
            channel_capacity: 100_000,
        }));

        let api_client = Arc::new(RacingCoachClient::new(&config.server_url));

        let (shutdown_tx, _) = watch::channel(false);

        Self {
            config,
            event_bus,
            api_client,
            cancel: CancellationToken::new(),
            shutdown_tx,
        }
    }

    /// Run the application
    pub async fn run(self) -> anyhow::Result<()> {
        info!("Starting Racing Coach Client");
        info!("Mode: {:?}", self.config.mode);

        if let Some(ref file) = self.config.ibt_file {
            info!("IBT File: {}", file.display());
        }
        info!("Server: {}", self.config.server_url);
        info!("Upload enabled: {}", self.config.upload_enabled);

        // Check server health
        self.check_server_health().await;

        // Create handlers
        let handlers = self.create_handlers();
        info!("Registered {} handlers", handlers.len());

        // Clone for event loop
        let event_bus = self.event_bus.clone();
        let cancel = self.cancel.clone();

        // Spawn event loop
        let event_loop_handle = tokio::spawn(async move {
            event_bus.run(handlers).await;
        });

        // Create telemetry collector
        let source_config = TelemetrySourceConfig {
            mode: self.config.mode,
            ibt_file: self.config.ibt_file.clone(),
            playback_speed: self.config.playback_speed,
        };

        let collector = TelemetryCollector::new(source_config);
        let collector_cancel = collector.cancel_token();

        // Spawn collector
        let event_bus_for_collector = self.event_bus.clone();
        let collector_handle = tokio::spawn(async move {
            if let Err(e) = collector.run(event_bus_for_collector).await {
                error!("Collector error: {}", e);
            }
        });

        // Wait for shutdown signal or completion
        let shutdown_reason = tokio::select! {
            _ = signal::ctrl_c() => {
                info!("Received Ctrl+C, shutting down...");
                "user interrupt"
            }
            _ = self.cancel.cancelled() => {
                info!("Shutdown requested");
                "shutdown requested"
            }
            result = collector_handle => {
                match result {
                    Ok(()) => {
                        info!("Telemetry collection complete");
                        "collection complete"
                    }
                    Err(e) => {
                        error!("Collector task panicked: {}", e);
                        "collector error"
                    }
                }
            }
        };

        // Graceful shutdown
        info!("Initiating shutdown (reason: {})", shutdown_reason);

        // Cancel collector if still running
        collector_cancel.cancel();

        // Shutdown event bus
        self.event_bus.shutdown();

        // Wait for event loop to finish
        let _ = tokio::time::timeout(
            std::time::Duration::from_secs(5),
            event_loop_handle,
        ).await;

        // Notify shutdown complete
        let _ = self.shutdown_tx.send(true);

        info!("Racing Coach Client shutdown complete");
        Ok(())
    }

    /// Check server health before starting
    async fn check_server_health(&self) {
        info!("Checking server health...");

        match self.api_client.health_check().await {
            Ok(response) => {
                info!("✓ Server is healthy: {}", response.status);
            }
            Err(e) => {
                warn!("✗ Server health check failed: {}", e);
                if self.config.upload_enabled {
                    warn!("Uploads may fail - server might be unavailable");
                }
            }
        }
    }

    /// Create all event handlers
    fn create_handlers(&self) -> Vec<Arc<dyn EventHandler>> {
        let mut handlers: Vec<Arc<dyn EventHandler>> = Vec::new();

        // Lap detection handler (always enabled)
        let lap_handler = LapHandler::with_config(crate::handlers::lap::LapHandlerConfig {
            lap_completion_threshold: self.config.lap_completion_threshold,
        });
        handlers.push(Arc::new(lap_handler));

        // Metrics extraction handler (always enabled)
        let metrics_handler = MetricsHandler::new();
        handlers.push(Arc::new(metrics_handler));

        // Upload handlers (conditional)
        if self.config.upload_enabled {
            let lap_upload = LapUploadHandler::new(self.api_client.clone());
            handlers.push(Arc::new(lap_upload));

            let metrics_upload = MetricsUploadHandler::new(self.api_client.clone());
            handlers.push(Arc::new(metrics_upload));
        } else {
            info!("Upload handlers disabled");
        }

        handlers
    }

    /// Request application shutdown
    pub fn shutdown(&self) {
        self.cancel.cancel();
    }

    /// Get a receiver to watch for shutdown completion
    pub fn shutdown_receiver(&self) -> watch::Receiver<bool> {
        self.shutdown_tx.subscribe()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::TelemetryMode;

    fn test_config() -> Config {
        Config {
            mode: TelemetryMode::Replay,
            ibt_file: Some(std::path::PathBuf::from("test.ibt")),
            playback_speed: 1.0,
            server_url: "http://localhost:8000".to_string(),
            upload_enabled: false,
            log_level: "info".to_string(),
            lap_completion_threshold: 0.05,
        }
    }

    #[test]
    fn test_app_creation() {
        let config = test_config();
        let app = RacingCoachApp::new(config);

        // Should have created event bus and API client
        assert!(!app.config.upload_enabled);
    }

    #[test]
    fn test_handler_creation_with_uploads() {
        let mut config = test_config();
        config.upload_enabled = true;

        let app = RacingCoachApp::new(config);
        let handlers = app.create_handlers();

        // Should have 4 handlers: lap, metrics, lap_upload, metrics_upload
        assert_eq!(handlers.len(), 4);
    }

    #[test]
    fn test_handler_creation_without_uploads() {
        let config = test_config();

        let app = RacingCoachApp::new(config);
        let handlers = app.create_handlers();

        // Should have 2 handlers: lap, metrics
        assert_eq!(handlers.len(), 2);
    }
}
