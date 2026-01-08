//! Live telemetry connection for Windows

use crate::Result;

#[cfg(windows)]
use {
    crate::driver::{Driver, SyncState},
    crate::provider::Provider,
    crate::providers::live::LiveProvider,
    crate::stream::ThrottleExt,
    crate::types::{FramePacket, UpdateRate},
    crate::{FrameAdapter, SessionInfo, VariableSchema},
    futures::{Stream, StreamExt},
    std::sync::Arc,
    std::time::Duration,
    tokio::sync::broadcast,
    tokio_stream::wrappers::{BroadcastStream, errors::BroadcastStreamRecvError},
    tokio_util::sync::CancellationToken,
    tracing::{debug, info, warn},
};

/// Live connection to iRacing telemetry
#[cfg(windows)]
pub struct LiveConnection {
    /// Frame broadcast sender (for creating subscribers)
    frame_tx: broadcast::Sender<Arc<FramePacket>>,

    /// Session broadcast sender (for creating subscribers)
    session_tx: broadcast::Sender<Arc<SessionInfo>>,

    /// Shared sync state for current_frame()/current_session() access
    sync_state: Arc<SyncState>,

    /// Variable schema
    schema: Arc<VariableSchema>,

    /// Source frequency
    source_hz: f64,

    /// Cancellation token for stopping tasks
    cancel: CancellationToken,
}

#[cfg(windows)]
impl LiveConnection {
    /// Create a new live connection.
    ///
    /// This method establishes a connection to iRacing's shared memory and starts
    /// monitoring for telemetry data. The connection will wait for iRacing to
    /// start a session before streaming frames.
    pub async fn connect() -> Result<Self> {
        info!("Connecting to iRacing live telemetry");

        // Create provider and extract metadata
        let provider = LiveProvider::new()?;
        let schema = provider.schema();
        let source_hz = provider.tick_rate();

        // Spawn driver tasks - they will wait for iRacing to start
        let channels = Driver::spawn(provider);

        // Don't wait for frames here - let the streams handle waiting
        // This allows the connection to be established even if iRacing isn't
        // in a session yet. The streams will wait for data.

        info!("Live connection established ({}Hz) - waiting for iRacing session", source_hz);

        Ok(Self {
            frame_tx: channels.frame_tx,
            session_tx: channels.session_tx,
            sync_state: channels.sync_state,
            schema,
            source_hz,
            cancel: channels.cancel,
        })
    }

    /// Subscribe to telemetry frames
    pub fn subscribe<T>(&self, rate: UpdateRate) -> impl Stream<Item = T> + 'static
    where
        T: FrameAdapter + Send + 'static,
    {
        // Validate schema once at subscription time
        let validation = T::validate_schema(&self.schema).expect("Schema validation failed");

        // Create base frame stream from broadcast channel
        // BroadcastStream waits for the next message, which is perfect for live
        // where we don't have data yet when iRacing hasn't started.
        let frames = BroadcastStream::new(self.frame_tx.subscribe()).filter_map(|result| async move {
            match result {
                Ok(frame) => Some(frame),
                Err(BroadcastStreamRecvError::Lagged(n)) => {
                    debug!("Live subscriber lagged by {} frames", n);
                    None
                }
            }
        });

        // Apply rate control and adaptation
        let effective_rate = rate.normalize(self.source_hz);

        match effective_rate {
            UpdateRate::Native => {
                // Direct adaptation, no throttling
                frames.map(move |packet| T::adapt(&packet, &validation)).boxed()
            }
            UpdateRate::Max(hz) => {
                // Throttle then adapt
                let interval = Duration::from_secs_f64(1.0 / hz as f64);
                frames.throttle(interval).map(move |packet| T::adapt(&packet, &validation)).boxed()
            }
        }
    }

    /// Get session updates as a stream
    ///
    /// Sessions are automatically detected by the Driver when session versions
    /// change, and YAML is parsed asynchronously without blocking frame processing.
    ///
    /// This stream waits for the next session update. Use current_session() for
    /// immediate access to the most recent session.
    pub fn session_updates(&self) -> impl Stream<Item = Arc<SessionInfo>> + 'static {
        BroadcastStream::new(self.session_tx.subscribe()).filter_map(|result| async move {
            match result {
                Ok(session) => Some(session),
                Err(BroadcastStreamRecvError::Lagged(n)) => {
                    warn!("Session subscriber lagged by {} updates", n);
                    None
                }
            }
        })
    }

    /// Get current session info (if any) - synchronous access
    pub fn current_session(&self) -> Option<Arc<SessionInfo>> {
        self.sync_state.current_session.read().unwrap().clone()
    }

    /// Get current frame (if available) - synchronous access
    pub fn current_frame(&self) -> Option<Arc<FramePacket>> {
        self.sync_state.current_frame.read().unwrap().clone()
    }

    /// Get the source telemetry frequency
    pub fn source_hz(&self) -> f64 {
        self.source_hz
    }

    /// Get the variable schema
    pub fn schema(&self) -> &VariableSchema {
        &self.schema
    }
}

#[cfg(windows)]
impl Drop for LiveConnection {
    fn drop(&mut self) {
        debug!("Dropping live connection");
        // Cancel tasks on drop for clean shutdown
        self.cancel.cancel();
    }
}

// Non-Windows stub implementation
#[cfg(not(windows))]
pub struct LiveConnection {
    _private: (),
}

#[cfg(not(windows))]
impl LiveConnection {
    /// Attempt to create a live connection on non-Windows platforms.
    ///
    /// This always returns an error as live telemetry is only available on Windows.
    /// Consider using `Pitwall::open()` with an IBT file for cross-platform testing.
    pub async fn connect() -> Result<Self> {
        Err(crate::TelemetryError::unsupported_platform("Live telemetry", "Windows"))
    }
}
