//! Driver spawns and manages telemetry processing tasks

use std::sync::{Arc, RwLock};
use tokio::sync::broadcast;
use tokio_util::sync::CancellationToken;
use tracing::{debug, error, info, trace, warn};

use super::provider::Provider;
use super::types::FramePacket;
use crate::SessionInfo;

/// Buffer capacity for frame broadcast channel (~4.3 seconds at 60Hz)
pub const FRAME_BUFFER_CAPACITY: usize = 256;
/// Buffer capacity for session broadcast channel (sessions change rarely)
pub const SESSION_BUFFER_CAPACITY: usize = 16;

/// Shared state for synchronous access to current values
pub struct SyncState {
    /// Current frame (most recently received)
    pub current_frame: RwLock<Option<Arc<FramePacket>>>,
    /// Current session info (most recently parsed)
    pub current_session: RwLock<Option<Arc<SessionInfo>>>,
}

impl SyncState {
    /// Create new sync state with no initial values
    pub fn new() -> Self {
        Self {
            current_frame: RwLock::new(None),
            current_session: RwLock::new(None),
        }
    }
}

impl Default for SyncState {
    fn default() -> Self {
        Self::new()
    }
}

/// Result of spawning driver tasks
pub struct DriverChannels {
    /// Sender for telemetry frames (subscribers call .subscribe())
    pub frame_tx: broadcast::Sender<Arc<FramePacket>>,
    /// Sender for session info updates (subscribers call .subscribe())
    pub session_tx: broadcast::Sender<Arc<SessionInfo>>,
    /// Shared state for synchronous access to current values
    pub sync_state: Arc<SyncState>,
    /// Cancellation token for graceful shutdown
    pub cancel: CancellationToken,
}

/// Driver spawns and manages telemetry processing tasks
///
/// Spawns a frame reader task that owns the Provider and detects session changes.
/// YAML parsing happens in short-lived spawned tasks to maintain <1ms frame latency.
pub struct Driver;

impl Driver {
    /// Spawn driver tasks for the given provider
    ///
    /// Returns broadcast senders for frames and sessions, sync state for current values,
    /// plus a cancellation token for graceful shutdown.
    pub fn spawn<P>(provider: P) -> DriverChannels
    where
        P: Provider,
    {
        // Create broadcast channels
        let (frame_tx, _) = broadcast::channel(FRAME_BUFFER_CAPACITY);
        let (session_tx, _) = broadcast::channel(SESSION_BUFFER_CAPACITY);

        // Create shared sync state for current value access
        let sync_state = Arc::new(SyncState::new());

        // Create cancellation token for coordinated shutdown
        let cancel = CancellationToken::new();

        // Clone what we need for the frame reader task
        let cancel_frame = cancel.clone();
        let frame_tx_clone = frame_tx.clone();
        let session_tx_clone = session_tx.clone();
        let sync_state_clone = sync_state.clone();

        // Spawn frame reader task (owns the provider)
        // YAML parsing happens via short-lived spawned tasks (see frame_reader_task)
        tokio::spawn(async move {
            Self::frame_reader_task(
                provider,
                frame_tx_clone,
                session_tx_clone,
                sync_state_clone,
                cancel_frame,
            )
            .await;
        });

        DriverChannels { frame_tx, session_tx, sync_state, cancel }
    }

    /// Frame reader task - reads frames and detects session changes
    async fn frame_reader_task<P>(
        mut provider: P,
        frame_tx: broadcast::Sender<Arc<FramePacket>>,
        session_tx: broadcast::Sender<Arc<SessionInfo>>,
        sync_state: Arc<SyncState>,
        cancel: CancellationToken,
    ) where
        P: Provider,
    {
        info!("Frame reader task started");
        let mut frame_count = 0u64;
        let mut error_count = 0u32;
        let mut last_session_version = None;
        const MAX_ERRORS: u32 = 10;

        loop {
            // Check for cancellation between frames
            if cancel.is_cancelled() {
                info!("Frame reader cancelled");
                break;
            }

            // Use select to allow cancellation during provider.next_frame()
            let result = tokio::select! {
                _ = cancel.cancelled() => {
                    info!("Frame reader cancelled during read");
                    break;
                }
                result = provider.next_frame() => result,
            };

            match result {
                Ok(Some(packet)) => {
                    frame_count += 1;
                    error_count = 0; // Reset error count on success
                    let version = packet.session_version;

                    trace!(
                        "Frame {}: tick={}, session_version={}",
                        frame_count, packet.tick, version
                    );

                    let frame = Arc::new(packet);

                    // Update sync state for current_frame() access
                    {
                        let mut guard = sync_state.current_frame.write().unwrap();
                        *guard = Some(frame.clone());
                    }

                    // Detect session version change
                    if last_session_version != Some(version) {
                        debug!(
                            "Session version changed: {} -> {}",
                            last_session_version.unwrap_or(0),
                            version
                        );

                        // Fetch YAML and spawn short-lived task to parse it
                        // This avoids blocking frame processing while YAML parsing happens
                        match provider.session_yaml(version).await {
                            Ok(Some(yaml)) => {
                                debug!(
                                    "Fetched session YAML ({} bytes) for version {}",
                                    yaml.len(),
                                    version
                                );

                                // Clone for the spawned task
                                let session_tx_clone = session_tx.clone();
                                let sync_state_clone = sync_state.clone();

                                // Spawn detached task to parse YAML without blocking frame reader
                                // Task automatically cleans up when parsing completes (~1-10ms)
                                tokio::spawn(async move {
                                    match SessionInfo::parse(&yaml) {
                                        Ok(session) => {
                                            let session = Arc::new(session);
                                            debug!(
                                                "Session parsed: Track={}",
                                                session.weekend_info.track_name
                                            );

                                            // Update sync state for current_session() access
                                            {
                                                let mut guard =
                                                    sync_state_clone.current_session.write().unwrap();
                                                *guard = Some(session.clone());
                                            }

                                            // Broadcast to all subscribers (ignore if no receivers)
                                            let _ = session_tx_clone.send(session);
                                        }
                                        Err(e) => {
                                            warn!("Failed to parse session YAML: {}", e);
                                        }
                                    }
                                });
                            }
                            Ok(None) => {
                                debug!("No session YAML for version {}", version);
                            }
                            Err(e) => {
                                warn!("Failed to get session YAML: {}", e);
                            }
                        }

                        last_session_version = Some(version);
                    }

                    // Broadcast frame to all subscribers (ignore if no receivers)
                    let _ = frame_tx.send(frame);
                }
                Ok(None) => {
                    info!("Provider stream ended after {} frames", frame_count);
                    // No explicit end-of-stream signal needed - dropping the sender
                    // will cause all receivers to get RecvError::Closed
                    break;
                }
                Err(e) => {
                    // Provider error - don't crash on transient failures
                    error_count += 1;
                    error!("Provider error ({}/{}): {}", error_count, MAX_ERRORS, e);

                    if error_count >= MAX_ERRORS {
                        error!("Too many provider errors, shutting down");
                        break;
                    }

                    // Exponential backoff: 50ms, 100ms, 200ms, ...
                    let backoff = std::time::Duration::from_millis(50 * (1 << error_count.min(5)));
                    tokio::time::sleep(backoff).await;
                }
            }
        }

        info!("Frame reader task ended (processed {} frames)", frame_count);
    }
}
