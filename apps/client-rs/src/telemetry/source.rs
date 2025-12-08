//! Telemetry source abstraction for live and replay modes.

use futures::Stream;
use pitwall::{Pitwall, ReplayConnection, SessionInfo, UpdateRate};
use std::path::Path;
use std::pin::Pin;
use std::sync::Arc;
use tracing::{debug, info};

use super::frame::RacingFrame;
use crate::config::TelemetryMode;

/// Telemetry source configuration
#[derive(Debug, Clone)]
pub struct TelemetrySourceConfig {
    pub mode: TelemetryMode,
    pub ibt_file: Option<std::path::PathBuf>,
    pub playback_speed: f64,
}

/// Errors that can occur when working with telemetry sources
#[derive(Debug, thiserror::Error)]
pub enum TelemetrySourceError {
    #[error("Failed to open IBT file: {0}")]
    IbtOpenError(String),

    #[error("Failed to connect to iRacing: {0}")]
    ConnectionError(String),

    #[error("No IBT file specified for replay mode")]
    MissingIbtFile,
}

/// Abstract telemetry source that can be either live or replay
pub enum TelemetrySource {
    /// Replay from IBT file
    Replay(ReplaySource),

    /// Live connection to iRacing (Windows only)
    #[cfg(windows)]
    Live(LiveSource),
}

impl TelemetrySource {
    /// Create a new telemetry source based on configuration
    pub async fn create(config: &TelemetrySourceConfig) -> Result<Self, TelemetrySourceError> {
        match config.mode {
            TelemetryMode::Replay => {
                let path = config
                    .ibt_file
                    .as_ref()
                    .ok_or(TelemetrySourceError::MissingIbtFile)?;
                let source = ReplaySource::open(path, config.playback_speed).await?;
                Ok(TelemetrySource::Replay(source))
            }
            TelemetryMode::Live => {
                #[cfg(windows)]
                {
                    let source = LiveSource::connect().await?;
                    Ok(TelemetrySource::Live(source))
                }
                #[cfg(not(windows))]
                {
                    Err(TelemetrySourceError::ConnectionError(
                        "Live mode is only available on Windows".to_string(),
                    ))
                }
            }
        }
    }

    /// Subscribe to telemetry frames
    pub fn subscribe(&self, rate: UpdateRate) -> Pin<Box<dyn Stream<Item = RacingFrame> + Send>> {
        match self {
            TelemetrySource::Replay(source) => source.subscribe(rate),
            #[cfg(windows)]
            TelemetrySource::Live(source) => source.subscribe(rate),
        }
    }

    /// Get current session information
    pub fn current_session(&self) -> Option<Arc<SessionInfo>> {
        match self {
            TelemetrySource::Replay(source) => source.current_session(),
            #[cfg(windows)]
            TelemetrySource::Live(source) => source.current_session(),
        }
    }

    /// Get session info update stream
    pub fn session_updates(&self) -> Pin<Box<dyn Stream<Item = Arc<SessionInfo>> + Send>> {
        match self {
            TelemetrySource::Replay(source) => source.session_updates(),
            #[cfg(windows)]
            TelemetrySource::Live(source) => source.session_updates(),
        }
    }

    /// Get source frequency in Hz
    pub fn source_hz(&self) -> f64 {
        match self {
            TelemetrySource::Replay(source) => source.connection.source_hz(),
            #[cfg(windows)]
            TelemetrySource::Live(source) => source.connection.source_hz(),
        }
    }
}

/// Replay telemetry source from IBT file
pub struct ReplaySource {
    connection: ReplayConnection,
}

impl ReplaySource {
    /// Open an IBT file for replay
    pub async fn open<P: AsRef<Path>>(
        path: P,
        speed: f64,
    ) -> Result<Self, TelemetrySourceError> {
        let path = path.as_ref();
        info!("Opening IBT file: {} (speed: {}x)", path.display(), speed);

        let connection = Pitwall::open(path, speed)
            .await
            .map_err(|e| TelemetrySourceError::IbtOpenError(e.to_string()))?;

        debug!("Replay source opened at {}Hz", connection.source_hz());

        Ok(Self { connection })
    }

    /// Subscribe to telemetry frames
    pub fn subscribe(&self, rate: UpdateRate) -> Pin<Box<dyn Stream<Item = RacingFrame> + Send>> {
        use futures::StreamExt;
        Box::pin(self.connection.subscribe::<RacingFrame>(rate).boxed())
    }

    /// Get current session information
    pub fn current_session(&self) -> Option<Arc<SessionInfo>> {
        self.connection.current_session()
    }

    /// Get session info update stream
    pub fn session_updates(&self) -> Pin<Box<dyn Stream<Item = Arc<SessionInfo>> + Send>> {
        use futures::StreamExt;
        Box::pin(self.connection.session_updates().boxed())
    }
}

/// Live telemetry source connected to iRacing (Windows only)
#[cfg(windows)]
pub struct LiveSource {
    connection: pitwall::LiveConnection,
}

#[cfg(windows)]
impl LiveSource {
    /// Connect to live iRacing telemetry
    pub async fn connect() -> Result<Self, TelemetrySourceError> {
        info!("Connecting to iRacing...");

        let connection = Pitwall::connect()
            .await
            .map_err(|e| TelemetrySourceError::ConnectionError(e.to_string()))?;

        info!("Connected to iRacing at {}Hz", connection.source_hz());

        Ok(Self { connection })
    }

    /// Subscribe to telemetry frames
    pub fn subscribe(&self, rate: UpdateRate) -> Pin<Box<dyn Stream<Item = RacingFrame> + Send>> {
        use futures::StreamExt;
        Box::pin(self.connection.subscribe::<RacingFrame>(rate).boxed())
    }

    /// Get current session information
    pub fn current_session(&self) -> Option<Arc<SessionInfo>> {
        self.connection.current_session()
    }

    /// Get session info update stream
    pub fn session_updates(&self) -> Pin<Box<dyn Stream<Item = Arc<SessionInfo>> + Send>> {
        use futures::StreamExt;
        Box::pin(self.connection.session_updates().boxed())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_source_config() {
        let config = TelemetrySourceConfig {
            mode: TelemetryMode::Replay,
            ibt_file: Some(std::path::PathBuf::from("test.ibt")),
            playback_speed: 2.0,
        };

        assert_eq!(config.mode, TelemetryMode::Replay);
        assert_eq!(config.playback_speed, 2.0);
    }
}
