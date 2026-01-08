use std::sync::Arc;

use async_trait::async_trait;
use tokio::sync::broadcast;
use tokio::task::JoinHandle;
use tokio_util::sync::CancellationToken;
use tracing::{info, warn};

use super::bus::EventBus;
use super::types::{Event, EventKind};

/// Context passed to handlers - allows publishing follow-up events
#[derive(Clone)]
pub struct HandlerContext {
    bus: EventBus,
}

impl HandlerContext {
    fn new(bus: EventBus) -> Self {
        Self { bus }
    }

    /// Publish a follow-up event
    pub fn publish(&self, event: Event) {
        self.bus.publish(event);
    }
}

/// Trait for event handlers
#[async_trait]
pub trait EventHandler: Send + Sync {
    /// Which event kind this handler processes
    fn handles(&self) -> EventKind;

    /// Process the event
    async fn handle(&self, event: Event, ctx: &HandlerContext);

    /// Handler name for logging
    fn name(&self) -> &'static str {
        std::any::type_name::<Self>()
    }
}

/// Registry for managing handler lifecycle
pub struct HandlerRegistry {
    handlers: Vec<Arc<dyn EventHandler>>,
    cancel_token: CancellationToken,
}

impl HandlerRegistry {
    pub fn new() -> Self {
        Self {
            handlers: Vec::new(),
            cancel_token: CancellationToken::new(),
        }
    }

    /// Register a handler
    pub fn register<H: EventHandler + 'static>(&mut self, handler: H) {
        self.handlers.push(Arc::new(handler));
    }

    /// Spawn all handler tasks, returns join handles
    pub fn run(&self, bus: EventBus) -> Vec<JoinHandle<()>> {
        let mut tasks = Vec::new();

        for handler in &self.handlers {
            let kind = handler.handles();
            let mut rx = bus.subscribe(kind);
            let handler = Arc::clone(handler);
            let bus_clone = bus.clone();
            let token = self.cancel_token.clone();
            let handler_name = handler.name();

            tasks.push(tokio::spawn(async move {
                info!("Handler {} started, listening for {:?}", handler_name, kind);

                let mut events_received: u64 = 0;
                let mut events_lagged: u64 = 0;

                loop {
                    tokio::select! {
                        _ = token.cancelled() => {
                            info!(
                                "Handler {} shutting down - received: {}, lagged: {}",
                                handler_name, events_received, events_lagged
                            );
                            break;
                        }
                        result = rx.recv() => {
                            match result {
                                Ok(event) => {
                                    events_received += 1;
                                    let ctx = HandlerContext::new(bus_clone.clone());
                                    handler.handle(event, &ctx).await;
                                }
                                Err(broadcast::error::RecvError::Lagged(n)) => {
                                    events_lagged += n;
                                    warn!(
                                        "Handler {} lagged, dropped {} events (total lagged: {})",
                                        handler_name, n, events_lagged
                                    );
                                }
                                Err(broadcast::error::RecvError::Closed) => {
                                    info!(
                                        "Handler {} channel closed - received: {}, lagged: {}",
                                        handler_name, events_received, events_lagged
                                    );
                                    break;
                                }
                            }
                        }
                    }
                }
            }));
        }

        tasks
    }

    /// Signal all handlers to shut down
    pub fn shutdown(&self) {
        info!("Signaling handler shutdown");
        self.cancel_token.cancel();
    }
}

impl Default for HandlerRegistry {
    fn default() -> Self {
        Self::new()
    }
}
