//! Racing Coach Client Library
//!
//! High-performance Rust client for iRacing telemetry analysis.
//! This library provides modules for:
//!
//! - **api**: HTTP client for Racing Coach server API
//! - **config**: Configuration management (CLI, env, files)
//! - **events**: Event bus system for decoupled communication
//! - **handlers**: Event handlers for lap detection, metrics extraction, and uploads
//! - **telemetry**: Telemetry collection from iRacing (live and replay)

pub mod api;
pub mod app;
pub mod config;
pub mod events;
pub mod handlers;
pub mod telemetry;

// Re-export commonly used types
pub use api::RacingCoachClient;
pub use app::RacingCoachApp;
pub use config::{Config, TelemetryMode};
pub use events::{Event, EventBus, EventHandler};
