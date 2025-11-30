from fastapi import APIRouter

from racing_coach_server.core_test.router import router as ct_router
from racing_coach_server.health.router import router as health_router
from racing_coach_server.metrics.router import router as metrics_router
from racing_coach_server.sessions.router import router as sessions_router
from racing_coach_server.telemetry.router import router as telemetry_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="")
api_router.include_router(telemetry_router, prefix="/telemetry")
api_router.include_router(metrics_router, prefix="/metrics")
api_router.include_router(sessions_router, prefix="/sessions")
api_router.include_router(ct_router)
