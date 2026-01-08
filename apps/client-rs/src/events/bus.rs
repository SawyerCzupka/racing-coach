use std::sync::Arc;
use std::{collections::HashMap, error::Error};

use tokio::sync::broadcast;

use super::types::{Event, EventKind};

pub use broadcast::Receiver;
pub use broadcast::error::SendError;

/// Event bus with discriminant-keyed channels for efficient routing
#[derive(Clone)]
pub struct EventBus {
    inner: Arc<EventBusInner>,
}

struct EventBusInner {
    channels: HashMap<EventKind, broadcast::Sender<Event>>,
    capacity: usize,
}

impl EventBus {
    /// Create a new event bus with the given channel capacity
    pub fn new(capacity: usize) -> Self {
        let channels = EventKind::all()
            .map(|kind| {
                let (tx, _) = broadcast::channel(capacity);
                (kind, tx)
            })
            .collect();

        Self {
            inner: Arc::new(EventBusInner { channels, capacity }),
        }
    }

    /// Publish an event to the appropriate channel (sync - no await needed)
    pub fn publish(&self, event: Event) -> Result<usize, SendError<Event>> {
        let kind = event.kind();
        self.inner
            .channels
            .get(&kind)
            .expect("all event kinds have channels")
            .send(event)
    }

    /// Subscribe to a specific event kind
    pub fn subscribe(&self, kind: EventKind) -> Receiver<Event> {
        self.inner
            .channels
            .get(&kind)
            .expect("all event kinds have channels")
            .subscribe()
    }

    /// Get the configured channel capacity
    pub fn capacity(&self) -> usize {
        self.inner.capacity
    }
}
