"""FastAPI application setup for Racing Coach Server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from racing_coach_server.config import settings
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

# CORS middleware for web and marketing site
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")
