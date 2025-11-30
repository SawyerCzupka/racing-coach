"""FastAPI application setup for Racing Coach Server."""

from fastapi import FastAPI

from racing_coach_server.logging import setup_logging

from .api import api_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Racing Coach Server",
    version="0.1.0",
    description="API server for racing telemetry data collection and analysis",
)

# Include routers
app.include_router(api_router, prefix="/api/v1")
