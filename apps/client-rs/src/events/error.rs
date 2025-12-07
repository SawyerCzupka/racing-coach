use thiserror::Error;

#[derive(Debug, Error)]
pub enum EventBusError {
    #[error("Event channel closed")]
    ChannelClosed,

    #[error("Event bus not running")]
    NotRunning,
}

#[derive(Debug, Error)]
pub enum HandlerError {
    #[error("Handler processing failed: {0}")]
    ProcessingError(String),

    #[error("Event publishing failed")]
    PublishError(#[from] EventBusError),
}
