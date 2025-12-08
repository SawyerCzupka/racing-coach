//! HTTP client for Racing Coach server API.
//!
//! Provides async methods for all server endpoints.

use reqwest::Client;
use tracing::{debug, error, info, instrument};
use uuid::Uuid;

use super::models::*;

/// API client errors
#[derive(Debug, thiserror::Error)]
pub enum ApiError {
    #[error("HTTP request failed: {0}")]
    RequestFailed(#[from] reqwest::Error),

    #[error("Server returned error: {status} - {message}")]
    ServerError { status: u16, message: String },

    #[error("Failed to parse response: {0}")]
    ParseError(String),

    #[error("Resource not found: {0}")]
    NotFound(String),
}

/// Racing Coach API client
#[derive(Debug, Clone)]
pub struct RacingCoachClient {
    client: Client,
    base_url: String,
}

impl RacingCoachClient {
    /// Create a new API client
    pub fn new(base_url: impl Into<String>) -> Self {
        Self {
            client: Client::new(),
            base_url: base_url.into(),
        }
    }

    /// Create a client with custom reqwest Client
    pub fn with_client(client: Client, base_url: impl Into<String>) -> Self {
        Self {
            client,
            base_url: base_url.into(),
        }
    }

    // ========================================================================
    // Health Endpoints
    // ========================================================================

    /// Check server health
    #[instrument(skip(self))]
    pub async fn health_check(&self) -> Result<HealthResponse, ApiError> {
        let url = format!("{}/api/v1/health", self.base_url);
        debug!("Health check: {}", url);

        let response = self.client.get(&url).send().await?;

        if response.status().is_success() {
            // Try to parse as JSON, fall back to simple response
            match response.json::<HealthResponse>().await {
                Ok(health) => Ok(health),
                Err(_) => Ok(HealthResponse {
                    status: "ok".to_string(),
                    version: None,
                }),
            }
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            Err(ApiError::ServerError { status, message })
        }
    }

    // ========================================================================
    // Telemetry Endpoints
    // ========================================================================

    /// Upload lap telemetry to server
    #[instrument(skip(self, lap, session), fields(lap_id = %lap_id))]
    pub async fn upload_lap(
        &self,
        lap: &LapTelemetryApi,
        session: &SessionFrameApi,
        lap_id: Uuid,
    ) -> Result<LapUploadResponse, ApiError> {
        let url = format!("{}/api/v1/telemetry/lap?lap_id={}", self.base_url, lap_id);
        debug!("Uploading lap telemetry: {} frames", lap.frames.len());

        let request = LapUploadRequest {
            lap: lap.clone(),
            session: session.clone(),
        };

        let response = self.client.post(&url).json(&request).send().await?;

        if response.status().is_success() {
            let result = response.json::<LapUploadResponse>().await?;
            info!("Lap uploaded successfully: lap_id={}", result.lap_id);
            Ok(result)
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            error!("Failed to upload lap: {} - {}", status, message);
            Err(ApiError::ServerError { status, message })
        }
    }

    /// Get latest session info
    #[instrument(skip(self))]
    pub async fn get_latest_session(&self) -> Result<SessionFrameApi, ApiError> {
        let url = format!("{}/api/v1/telemetry/sessions/latest", self.base_url);
        debug!("Getting latest session");

        let response = self.client.get(&url).send().await?;

        if response.status().is_success() {
            Ok(response.json::<SessionFrameApi>().await?)
        } else if response.status() == reqwest::StatusCode::NOT_FOUND {
            Err(ApiError::NotFound("No sessions found".to_string()))
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            Err(ApiError::ServerError { status, message })
        }
    }

    // ========================================================================
    // Metrics Endpoints
    // ========================================================================

    /// Upload lap metrics to server
    #[instrument(skip(self, metrics), fields(lap_id = %lap_id))]
    pub async fn upload_metrics(
        &self,
        metrics: &LapMetricsApi,
        lap_id: Uuid,
    ) -> Result<MetricsUploadResponse, ApiError> {
        let url = format!("{}/api/v1/metrics/lap", self.base_url);
        debug!("Uploading lap metrics: {} braking zones, {} corners",
            metrics.braking_zones.len(),
            metrics.corners.len()
        );

        let request = MetricsUploadRequest {
            lap_metrics: metrics.clone(),
            lap_id: lap_id.to_string(),
        };

        let response = self.client.post(&url).json(&request).send().await?;

        if response.status().is_success() {
            let result = response.json::<MetricsUploadResponse>().await?;
            info!("Metrics uploaded successfully: id={}", result.lap_metrics_id);
            Ok(result)
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            error!("Failed to upload metrics: {} - {}", status, message);
            Err(ApiError::ServerError { status, message })
        }
    }

    /// Get metrics for a specific lap
    #[instrument(skip(self), fields(lap_id = %lap_id))]
    pub async fn get_lap_metrics(&self, lap_id: Uuid) -> Result<LapMetricsResponse, ApiError> {
        let url = format!("{}/api/v1/metrics/lap/{}", self.base_url, lap_id);
        debug!("Getting lap metrics");

        let response = self.client.get(&url).send().await?;

        if response.status().is_success() {
            Ok(response.json::<LapMetricsResponse>().await?)
        } else if response.status() == reqwest::StatusCode::NOT_FOUND {
            Err(ApiError::NotFound(format!("Metrics not found for lap {}", lap_id)))
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            Err(ApiError::ServerError { status, message })
        }
    }

    // ========================================================================
    // Sessions Endpoints
    // ========================================================================

    /// List all sessions
    #[instrument(skip(self))]
    pub async fn list_sessions(&self) -> Result<SessionListResponse, ApiError> {
        let url = format!("{}/api/v1/sessions", self.base_url);
        debug!("Listing sessions");

        let response = self.client.get(&url).send().await?;

        if response.status().is_success() {
            Ok(response.json::<SessionListResponse>().await?)
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            Err(ApiError::ServerError { status, message })
        }
    }

    /// Get session details
    #[instrument(skip(self), fields(session_id = %session_id))]
    pub async fn get_session(&self, session_id: Uuid) -> Result<SessionDetailResponse, ApiError> {
        let url = format!("{}/api/v1/sessions/{}", self.base_url, session_id);
        debug!("Getting session details");

        let response = self.client.get(&url).send().await?;

        if response.status().is_success() {
            Ok(response.json::<SessionDetailResponse>().await?)
        } else if response.status() == reqwest::StatusCode::NOT_FOUND {
            Err(ApiError::NotFound(format!("Session {} not found", session_id)))
        } else {
            let status = response.status().as_u16();
            let message = response.text().await.unwrap_or_default();
            Err(ApiError::ServerError { status, message })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = RacingCoachClient::new("http://localhost:8000");
        assert_eq!(client.base_url, "http://localhost:8000");
    }
}
