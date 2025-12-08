//! Racing Coach Client - High-performance Rust client for iRacing telemetry analysis.
//!
//! This client collects telemetry from iRacing (live or replay), detects lap completion,
//! extracts performance metrics, and uploads data to the Racing Coach server.
//!
//! # Usage
//!
//! ## Live Mode (Windows only)
//! ```bash
//! racing-coach --mode live
//! ```
//!
//! ## Replay Mode
//! ```bash
//! racing-coach --mode replay --file session.ibt --speed 2.0
//! ```
//!
//! ## Environment Variables
//! - `TELEMETRY_MODE`: live or replay
//! - `IBT_FILE`: Path to IBT file for replay mode
//! - `SERVER_URL`: Racing Coach server URL (default: http://localhost:8000)
//! - `UPLOAD_ENABLED`: Enable/disable uploads (default: true)
//! - `LOG_LEVEL`: trace, debug, info, warn, error (default: info)

use racing_coach_client::{Config, RacingCoachApp};
use tracing::info;
use tracing_subscriber::{fmt, EnvFilter};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load configuration
    let config = Config::load()?;

    // Initialize logging
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(&config.log_level));

    fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_thread_ids(false)
        .with_file(false)
        .with_line_number(false)
        .init();

    info!("Racing Coach Client v{}", env!("CARGO_PKG_VERSION"));

    // Create and run application
    let app = RacingCoachApp::new(config);
    app.run().await?;

    Ok(())
}
