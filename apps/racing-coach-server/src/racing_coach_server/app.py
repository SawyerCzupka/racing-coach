"""FastAPI application setup for Racing Coach Server."""

from fastapi import FastAPI

from racing_coach_server.health.router import router as health_router
from racing_coach_server.logging import setup_logging
from racing_coach_server.metrics.router import router as metrics_router
from racing_coach_server.telemetry.router import router as telemetry_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Racing Coach Server",
    version="0.1.0",
    description="API server for racing telemetry data collection and analysis",
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(telemetry_router, prefix="/api/v1/telemetry")
app.include_router(metrics_router, prefix="/api/v1/metrics")
