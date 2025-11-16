"""Pytest configuration and shared fixtures for racing-coach-server tests."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pytest_factoryboy import register
from pytest_mock import MockerFixture
from racing_coach_server.app import app
from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    AsyncTransaction,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

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
def postgres_container():
    """
    Start a PostgreSQL container with TimescaleDB for the entire test session.

    This fixture:
    - Starts one PostgreSQL container per test session (expensive operation)
    - Automatically handles container lifecycle (start/stop)
    - Uses timescale/timescaledb:latest-pg16 image which includes TimescaleDB extension
    """
    with PostgresContainer("timescale/timescaledb:2.18.1-pg17") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def db_engine(postgres_container: PostgresContainer):
    """
    Create async SQLAlchemy engine with full schema from Alembic migrations.

    This fixture:
    - Gets connection URL from TestContainers
    - Ensures TimescaleDB extension is installed
    - Runs all Alembic migrations to populate schema
    - Converts psycopg URL to asyncpg for async operations
    - Creates async engine for the session

    The database schema is created once per test session for performance.
    Individual tests get transaction isolation via the db_session fixture.
    """
    # Get synchronous connection URL from TestContainers
    sync_url = postgres_container.get_connection_url()

    print(f"Test database URL: {sync_url}")

    # Ensure TimescaleDB extension is installed
    import psycopg2
    from sqlalchemy.engine import make_url

    try:
        # Parse SQLAlchemy URL and convert to psycopg2 format
        url = make_url(sync_url)
        psycopg2_url = (
            f"postgresql://{url.username}:{url.password}@{url.host}:{url.port}/{url.database}"
        )
        conn = psycopg2.connect(psycopg2_url)
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not create timescaledb extension: {e}")

    # Configure Alembic programmatically
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    alembic_config = Config(str(alembic_ini_path))
    alembic_config.set_main_option("sqlalchemy.url", sync_url)

    # Run all migrations on the test database
    # This executes ALL your custom DDL, indexes, constraints, triggers, etc.
    command.upgrade(alembic_config, "head")

    # Convert to async URL for asyncpg driver
    async_url = sync_url.replace("psycopg2", "asyncpg")

    # Create async engine
    engine = create_async_engine(async_url, echo=False)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def connection(db_engine: AsyncEngine):
    """
    Session-scoped database connection for transaction management.

    This connection is reused across all tests in the session.
    Individual test isolation is handled by the transaction fixture.
    """
    async with db_engine.connect() as connection:
        yield connection


@pytest_asyncio.fixture()
async def transaction(connection: AsyncConnection):
    """
    Function-scoped transaction that rolls back after each test.

    This ensures complete isolation between tests while maintaining
    the efficiency of transaction rollback (~1ms) vs database recreation.

    Each test gets a fresh transaction that is automatically rolled back
    when the test completes, ensuring no test data persists.
    """
    async with connection.begin() as transaction:
        yield transaction


@pytest_asyncio.fixture()
async def db_session(connection: AsyncConnection, transaction: AsyncTransaction):
    """
    Provide isolated AsyncSession for each test with automatic rollback.

    This fixture:
    - Creates a new session per test
    - Uses savepoint for transaction isolation within parent transaction
    - Automatically rolls back all changes after test completes
    - Ensures complete test isolation without recreating database

    Usage:
        async def test_create_lap(db_session):
            lap = Lap(lap_number=1, lap_time=90.5)
            db_session.add(lap)
            await db_session.commit()
            # Automatically rolled back after test
    """
    session = AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    yield session

    await session.close()
    await transaction.rollback()


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

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# Mock Fixtures for Unit Tests
# ============================================================================


@pytest.fixture
def mock_db_session(mocker: MockerFixture):
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


# def pytest_configure(config):
#     """Configure custom pytest markers."""
#     config.addinivalue_line(
#         "markers",
#         "unit: mark test as a unit test (mocks external dependencies)",
#     )
#     config.addinivalue_line(
#         "markers",
#         "integration: mark test as an integration test (uses test database)",
#     )
#     config.addinivalue_line(
#         "markers",
#         "slow: mark test as slow (takes longer than 1 second)",
#     )
