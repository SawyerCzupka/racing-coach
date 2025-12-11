//! Configuration module for Racing Coach Client.
//!
//! Provides configuration management via environment variables, config files, and CLI arguments.

use clap::Parser;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Telemetry source mode
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TelemetryMode {
    /// Live connection to iRacing (Windows only)
    #[default]
    Live,
    /// Replay from IBT file
    Replay,
}

impl std::str::FromStr for TelemetryMode {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "live" => Ok(TelemetryMode::Live),
            "replay" => Ok(TelemetryMode::Replay),
            _ => Err(format!("Invalid telemetry mode: {}. Use 'live' or 'replay'", s)),
        }
    }
}

impl std::fmt::Display for TelemetryMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TelemetryMode::Live => write!(f, "live"),
            TelemetryMode::Replay => write!(f, "replay"),
        }
    }
}

/// CLI arguments for Racing Coach Client
#[derive(Parser, Debug, Clone)]
#[command(name = "racing-coach")]
#[command(author = "Racing Coach Team")]
#[command(version = "0.1.0")]
#[command(about = "AI-powered sim racing coach for iRacing")]
pub struct CliArgs {
    /// Telemetry mode: 'live' for iRacing connection, 'replay' for IBT file
    #[arg(short, long, env = "TELEMETRY_MODE", default_value = "live")]
    pub mode: TelemetryMode,

    /// Path to IBT file (required for replay mode)
    #[arg(short, long, env = "IBT_FILE")]
    pub file: Option<PathBuf>,

    /// Playback speed multiplier for replay mode (1.0 = real-time)
    #[arg(short, long, env = "PLAYBACK_SPEED", default_value = "1.0")]
    pub speed: f64,

    /// Server URL for API endpoints
    #[arg(long, env = "SERVER_URL", default_value = "http://localhost:8000")]
    pub server_url: String,

    /// Enable lap telemetry upload to server
    #[arg(long, env = "UPLOAD_ENABLED", default_value = "true")]
    pub upload: bool,

    /// Log level (trace, debug, info, warn, error)
    #[arg(long, env = "LOG_LEVEL", default_value = "info")]
    pub log_level: String,

    /// Minimum lap completion percentage to consider a lap valid (0.0-1.0)
    #[arg(long, env = "LAP_COMPLETION_THRESHOLD", default_value = "0.05")]
    pub lap_completion_threshold: f32,
}

impl CliArgs {
    /// Validate the configuration
    pub fn validate(&self) -> Result<(), ConfigError> {
        // Replay mode requires a file path
        if self.mode == TelemetryMode::Replay && self.file.is_none() {
            return Err(ConfigError::MissingIbtFile);
        }

        // Validate playback speed
        if self.speed <= 0.0 {
            return Err(ConfigError::InvalidPlaybackSpeed(self.speed));
        }

        // Validate lap completion threshold
        if !(0.0..=1.0).contains(&self.lap_completion_threshold) {
            return Err(ConfigError::InvalidThreshold(self.lap_completion_threshold));
        }

        // Check if IBT file exists (for replay mode)
        if let Some(ref path) = self.file {
            if self.mode == TelemetryMode::Replay && !path.exists() {
                return Err(ConfigError::IbtFileNotFound(path.clone()));
            }
        }

        Ok(())
    }
}

/// Application configuration
#[derive(Debug, Clone)]
pub struct Config {
    /// Telemetry mode
    pub mode: TelemetryMode,
    /// Path to IBT file (for replay mode)
    pub ibt_file: Option<PathBuf>,
    /// Playback speed multiplier
    pub playback_speed: f64,
    /// Server base URL
    pub server_url: String,
    /// Whether to upload telemetry to server
    pub upload_enabled: bool,
    /// Log level
    pub log_level: String,
    /// Minimum lap completion percentage
    pub lap_completion_threshold: f32,
}

impl Config {
    /// Create configuration from CLI arguments
    pub fn from_args(args: CliArgs) -> Result<Self, ConfigError> {
        args.validate()?;

        Ok(Self {
            mode: args.mode,
            ibt_file: args.file,
            playback_speed: args.speed,
            server_url: args.server_url,
            upload_enabled: args.upload,
            log_level: args.log_level,
            lap_completion_threshold: args.lap_completion_threshold,
        })
    }

    /// Load configuration from environment and CLI
    pub fn load() -> Result<Self, ConfigError> {
        // Load .env file if present
        let _ = dotenvy::dotenv();

        let args = CliArgs::parse();
        Self::from_args(args)
    }

    /// Get the API base URL for telemetry endpoints
    pub fn telemetry_api_url(&self) -> String {
        format!("{}/api/v1/telemetry", self.server_url)
    }

    /// Get the API base URL for metrics endpoints
    pub fn metrics_api_url(&self) -> String {
        format!("{}/api/v1/metrics", self.server_url)
    }

    /// Get the API base URL for sessions endpoints
    pub fn sessions_api_url(&self) -> String {
        format!("{}/api/v1/sessions", self.server_url)
    }

    /// Get the health check URL
    pub fn health_url(&self) -> String {
        format!("{}/api/v1/health", self.server_url)
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            mode: TelemetryMode::Live,
            ibt_file: None,
            playback_speed: 1.0,
            server_url: "http://localhost:8000".to_string(),
            upload_enabled: true,
            log_level: "info".to_string(),
            lap_completion_threshold: 0.05,
        }
    }
}

/// Configuration errors
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("IBT file path is required for replay mode")]
    MissingIbtFile,

    #[error("IBT file not found: {0}")]
    IbtFileNotFound(PathBuf),

    #[error("Invalid playback speed: {0}. Must be positive")]
    InvalidPlaybackSpeed(f64),

    #[error("Invalid lap completion threshold: {0}. Must be between 0.0 and 1.0")]
    InvalidThreshold(f32),

    #[error("Configuration error: {0}")]
    Other(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_telemetry_mode_from_str() {
        assert_eq!("live".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
        assert_eq!("Live".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
        assert_eq!("LIVE".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
        assert_eq!("replay".parse::<TelemetryMode>().unwrap(), TelemetryMode::Replay);
        assert!("invalid".parse::<TelemetryMode>().is_err());
    }

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.mode, TelemetryMode::Live);
        assert!(config.upload_enabled);
        assert_eq!(config.playback_speed, 1.0);
    }

    #[test]
    fn test_config_validation_replay_without_file() {
        let args = CliArgs {
            mode: TelemetryMode::Replay,
            file: None,
            speed: 1.0,
            server_url: "http://localhost:8000".to_string(),
            upload: true,
            log_level: "info".to_string(),
            lap_completion_threshold: 0.05,
        };
        assert!(matches!(args.validate(), Err(ConfigError::MissingIbtFile)));
    }

    #[test]
    fn test_config_validation_invalid_speed() {
        let args = CliArgs {
            mode: TelemetryMode::Live,
            file: None,
            speed: -1.0,
            server_url: "http://localhost:8000".to_string(),
            upload: true,
            log_level: "info".to_string(),
            lap_completion_threshold: 0.05,
        };
        assert!(matches!(args.validate(), Err(ConfigError::InvalidPlaybackSpeed(_))));
    }

    #[test]
    fn test_api_urls() {
        let config = Config {
            server_url: "http://example.com:8000".to_string(),
            ..Default::default()
        };
        assert_eq!(config.telemetry_api_url(), "http://example.com:8000/api/v1/telemetry");
        assert_eq!(config.metrics_api_url(), "http://example.com:8000/api/v1/metrics");
        assert_eq!(config.sessions_api_url(), "http://example.com:8000/api/v1/sessions");
    }
}
