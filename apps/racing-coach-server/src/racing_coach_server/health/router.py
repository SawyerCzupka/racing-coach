"""FastAPI route handlers for health check feature."""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from racing_coach_server.dependencies import AsyncSessionDep
from racing_coach_server.health.schemas import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health", response_model=HealthCheckResponse, tags=["health"], operation_id="healthCheck"
)
async def health_check(
    db: AsyncSessionDep,
) -> HealthCheckResponse:
    """
    Comprehensive health check endpoint.

    Verifies:
    - Server is running
    - Database connectivity
    - Database can execute queries

    Returns:
        HealthCheckResponse: Status information about the server and database
    """
    db_status = "unknown"
    db_message = ""

    try:
        # Test database connectivity with a simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        db_status = "healthy"
        db_message = "Database connection successful"
        logger.debug("Health check: Database connection successful")
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database connection failed: {str(e)}"
        logger.error(f"Health check failed: {e}", exc_info=True)

    # Overall status is healthy only if all components are healthy
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"

    return HealthCheckResponse(
        status=overall_status,
        message="Racing Coach Server is running",
        database_status=db_status,
        database_message=db_message,
    )
