//! Replay connection for IBT files

use futures::{Stream, StreamExt};
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::broadcast;
use tokio_stream::wrappers::{BroadcastStream, errors::BroadcastStreamRecvError};
use tokio_util::sync::CancellationToken;
use tracing::{debug, info, warn};

use crate::driver::{Driver, SyncState};
use crate::provider::Provider;
use crate::providers::replay::ReplayProvider;
use crate::stream::ThrottleExt;
use crate::types::{FramePacket, UpdateRate};
use crate::{FrameAdapter, Result, SessionInfo, VariableSchema};

/// Replay connection from IBT file
pub struct ReplayConnection {
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

impl ReplayConnection {
    /// Open an IBT file for replay.
    ///
    /// Waits for the first frame to be available before returning to ensure
    /// the connection is fully initialized and ready for subscriptions.
    pub async fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref();
        info!("Opening IBT file: {}", path.display());

        // Create provider and extract metadata
        let provider = ReplayProvider::new(path)?;
        let schema = provider.schema();
        let source_hz = provider.tick_rate();

        // Spawn driver tasks
        let channels = Driver::spawn(provider);

        // Wait for first frame to be available via broadcast
        let mut rx = channels.frame_tx.subscribe();
        let timeout = std::time::Duration::from_secs(5);
        let wait_result = tokio::time::timeout(timeout, async {
            // Wait for first frame via broadcast receiver
            rx.recv().await.ok()
        })
        .await;

        if wait_result.is_err() || wait_result.as_ref().ok().and_then(|o| o.as_ref()).is_none() {
            warn!("Timeout waiting for first frame from replay file");
        }

        info!("Replay connection opened ({}Hz)", source_hz);

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
        let frames = BroadcastStream::new(self.frame_tx.subscribe()).filter_map(|result| async move {
            match result {
                Ok(frame) => Some(frame),
                Err(BroadcastStreamRecvError::Lagged(n)) => {
                    warn!("Frame subscriber lagged by {} frames", n);
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

    /// Get current session info (if available) - synchronous access
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

impl Drop for ReplayConnection {
    fn drop(&mut self) {
        debug!("Dropping replay connection");
        // Cancel tasks on drop for clean shutdown
        self.cancel.cancel();
    }
}
