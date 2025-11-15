"""Pytest configuration and shared fixtures for racing-coach-server tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pytest_factoryboy import register
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from racing_coach_server.app import app
from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService
from tests.factories import (
    LapFactory,
    SessionFrameFactory,
    TelemetryFactory,
    TelemetryFrameFactory,
    TrackSessionFactory,
)

# Register factories to create pytest fixtures automatically
register(TelemetryFrameFactory)
register(SessionFrameFactory)
register(TrackSessionFactory)
register(LapFactory)
register(TelemetryFactory)


# ============================================================================
# Database Fixtures - Integration Tests
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:
    """
    Create and start a PostgreSQL container with TimescaleDB for integration tests.

    This fixture is session-scoped to avoid spinning up containers for each test.
    """
    # Use the official TimescaleDB image
    postgres = PostgresContainer(
        image="timescale/timescaledb:latest-pg16",
        driver="asyncpg",
    )
    postgres.start()
    yield postgres
    postgres.stop()


@pytest.fixture(scope="session")
def test_database_url(postgres_container: PostgresContainer) -> str:
    """Get the database URL for the test database."""
    # Replace psycopg2 driver with asyncpg
    url = postgres_container.get_connection_url()
    return url.replace("psycopg2", "asyncpg")


@pytest.fixture(scope="session")
async def test_engine(test_database_url: str):
    """Create a test database engine."""
    engine = create_async_engine(test_database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database(test_engine, test_database_url: str) -> None:
    """
    Set up the test database schema using Alembic migrations.

    This runs once per test session.
    """
    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_database_url)
    command.upgrade(alembic_cfg, "head")

    yield

    # Teardown: drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("DROP SCHEMA public CASCADE")))
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("CREATE SCHEMA public")))


@pytest.fixture
async def db_session(
    test_engine, setup_database
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for a test.

    This fixture is function-scoped and creates a new session for each test.
    After the test, all changes are rolled back.
    """
    # Create a connection
    async with test_engine.connect() as connection:
        # Begin a transaction
        trans = await connection.begin()

        # Create a session bound to the connection
        AsyncSessionFactory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with AsyncSessionFactory() as session:
            yield session

        # Rollback the transaction
        await trans.rollback()


# ============================================================================
# Service Fixtures
# ============================================================================


@pytest.fixture
def telemetry_service(db_session: AsyncSession) -> TelemetryService:
    """Create a TelemetryService instance for testing."""
    return TelemetryService(db_session)


# ============================================================================
# FastAPI Client Fixtures
# ============================================================================


@pytest.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FastAPI app with database dependency override.

    This allows integration tests to use the test database instead of the real one.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# Mock Fixtures for Unit Tests
# ============================================================================


@pytest.fixture
def mock_db_session(mocker):
    """Create a mock AsyncSession for unit tests."""
    mock_session = mocker.AsyncMock(spec=AsyncSession)
    mock_session.commit = mocker.AsyncMock()
    mock_session.rollback = mocker.AsyncMock()
    mock_session.flush = mocker.AsyncMock()
    mock_session.execute = mocker.AsyncMock()
    mock_session.add = mocker.Mock()
    mock_session.add_all = mocker.Mock()
    return mock_session


# ============================================================================
# Parameterization Helpers
# ============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test (mocks external dependencies)",
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (uses test database)",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (takes longer than 1 second)",
    )
