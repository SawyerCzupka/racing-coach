use std::sync::Arc;
use tokio::sync::{broadcast, mpsc, Notify};
use tracing::{debug, error, info, warn};

use super::error::EventBusError;
use super::handler::{EventHandler, HandlerContext};
use super::types::{Event, TimestampedEvent};

/// Configuration for the EventBus
#[derive(Debug, Clone)]
pub struct EventBusConfig {
    /// Maximum number of events that can be buffered in the broadcast channel
    pub channel_capacity: usize,
}

impl Default for EventBusConfig {
    fn default() -> Self {
        Self {
            channel_capacity: 1000,
        }
    }
}

/// The main event bus for broadcasting events to handlers
pub struct EventBus {
    /// Broadcast sender - cloned for each publish
    sender: broadcast::Sender<TimestampedEvent>,

    /// For thread-safe publishing from sync contexts
    sync_sender: mpsc::UnboundedSender<TimestampedEvent>,
    sync_receiver: tokio::sync::Mutex<mpsc::UnboundedReceiver<TimestampedEvent>>,

    /// Shutdown signal
    shutdown: Arc<Notify>,

    /// Configuration
    config: EventBusConfig,
}

impl EventBus {
    /// Create a new EventBus with default configuration
    pub fn new() -> Self {
        Self::with_config(EventBusConfig::default())
    }

    /// Create a new EventBus with custom configuration
    pub fn with_config(config: EventBusConfig) -> Self {
        let (sender, _) = broadcast::channel(config.channel_capacity);
        let (sync_sender, sync_receiver) = mpsc::unbounded_channel();

        Self {
            sender,
            sync_sender,
            sync_receiver: tokio::sync::Mutex::new(sync_receiver),
            shutdown: Arc::new(Notify::new()),
            config,
        }
    }

    /// Subscribe to events, returning a receiver
    pub fn subscribe(&self) -> broadcast::Receiver<TimestampedEvent> {
        self.sender.subscribe()
    }

    /// Get a handle for publishing events (can be cloned and shared)
    pub fn publisher(&self) -> EventPublisher {
        EventPublisher {
            sender: self.sender.clone(),
            sync_sender: self.sync_sender.clone(),
        }
    }

    /// Publish an event (async context)
    pub async fn publish(&self, event: Event) -> Result<(), EventBusError> {
        let timestamped = TimestampedEvent::new(event);
        self.sender
            .send(timestamped)
            .map_err(|_| EventBusError::ChannelClosed)?;
        Ok(())
    }

    /// Publish an event from sync code (thread-safe)
    pub fn publish_sync(&self, event: Event) -> Result<(), EventBusError> {
        let timestamped = TimestampedEvent::new(event);
        self.sync_sender
            .send(timestamped)
            .map_err(|_| EventBusError::ChannelClosed)
    }

    /// Get a shutdown notifier
    pub fn shutdown_signal(&self) -> Arc<Notify> {
        self.shutdown.clone()
    }

    /// Run the event loop (call this in a spawned task)
    ///
    /// This method will block until the shutdown signal is received.
    /// It processes events from both the sync bridge and broadcast channel,
    /// dispatching them to all registered handlers concurrently.
    pub async fn run(self: Arc<Self>, handlers: Vec<Arc<dyn EventHandler>>) {
        let mut event_receiver = self.sender.subscribe();
        let mut sync_receiver = self.sync_receiver.lock().await;

        info!("Event bus started with {} handlers", handlers.len());
        for handler in &handlers {
            debug!("Registered handler: {}", handler.name());
        }

        loop {
            tokio::select! {
                // Handle events from sync bridge
                Some(timestamped) = sync_receiver.recv() => {
                    // Forward to broadcast channel
                    if let Err(e) = self.sender.send(timestamped) {
                        error!("Failed to forward event from sync bridge: {}", e);
                    }
                }

                // Handle events from broadcast channel
                result = event_receiver.recv() => {
                    match result {
                        Ok(timestamped) => {
                            let publisher = self.publisher();
                            let ctx = HandlerContext {
                                publisher: &publisher,
                                timestamp: timestamped.timestamp,
                            };

                            // Dispatch to all handlers concurrently
                            let results = futures::future::join_all(
                                handlers.iter().map(|h| {
                                    let handler = Arc::clone(h);
                                    let event = &timestamped.event;
                                    let ctx_ref = &ctx;
                                    async move {
                                        match handler.handle(event, ctx_ref).await {
                                            Ok(true) => {
                                                debug!("Handler {} processed event", handler.name());
                                            }
                                            Ok(false) => {
                                                // Handler ignored the event (expected)
                                            }
                                            Err(e) => {
                                                error!("Handler {} failed: {}", handler.name(), e);
                                            }
                                        }
                                    }
                                })
                            ).await;

                            // Results are already processed in the closures above
                            drop(results);
                        }
                        Err(broadcast::error::RecvError::Lagged(n)) => {
                            warn!("Event receiver lagged by {} messages", n);
                        }
                        Err(broadcast::error::RecvError::Closed) => {
                            info!("Event channel closed");
                            break;
                        }
                    }
                }

                // Handle shutdown signal
                _ = self.shutdown.notified() => {
                    info!("Shutdown signal received");
                    break;
                }
            }
        }

        info!("Event bus stopped");
    }

    /// Signal the event bus to shutdown
    pub fn shutdown(&self) {
        self.shutdown.notify_waiters();
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new()
    }
}

/// A clonable handle for publishing events
#[derive(Clone)]
pub struct EventPublisher {
    sender: broadcast::Sender<TimestampedEvent>,
    sync_sender: mpsc::UnboundedSender<TimestampedEvent>,
}

impl EventPublisher {
    /// Publish an event (async context)
    pub async fn publish(&self, event: Event) -> Result<(), EventBusError> {
        let timestamped = TimestampedEvent::new(event);
        self.sender
            .send(timestamped)
            .map_err(|_| EventBusError::ChannelClosed)?;
        Ok(())
    }

    /// Publish from sync code
    pub fn publish_sync(&self, event: Event) -> Result<(), EventBusError> {
        let timestamped = TimestampedEvent::new(event);
        self.sync_sender
            .send(timestamped)
            .map_err(|_| EventBusError::ChannelClosed)
    }
}
