"""Pytest configuration and shared fixtures for racing-coach-server tests."""

import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock

# Set test environment variables before importing app modules
os.environ["SESSION_COOKIE_SECURE"] = "false"

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from polyfactory.pytest_plugin import register_fixture
from pytest_mock import MockerFixture
from racing_coach_server.app import app
from racing_coach_server.auth.service import AuthService
from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    AsyncTransaction,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer  # pyright: ignore[reportMissingTypeStubs]

from tests.polyfactories import (
    BrakingMetricsDBFactory,
    CornerMetricsDBFactory,
    DeviceAuthorizationFactory,
    DeviceTokenFactory,
    LapFactory,
    LapMetricsDBFactory,
    LapTelemetryFactory,
    SessionFrameFactory,
    TelemetryDBFactory,
    TelemetryFrameFactory,
    TelemetrySequenceFactory,
    TrackSessionFactory,
    UserFactory,
    UserSessionFactory,
)

# Register all polyfactory factories as pytest fixtures
register_fixture(TelemetryFrameFactory)
register_fixture(SessionFrameFactory)
register_fixture(LapTelemetryFactory)
register_fixture(TelemetrySequenceFactory)
register_fixture(TrackSessionFactory)
register_fixture(LapFactory)
register_fixture(TelemetryDBFactory)
register_fixture(LapMetricsDBFactory)
register_fixture(BrakingMetricsDBFactory)
register_fixture(CornerMetricsDBFactory)
register_fixture(UserFactory)
register_fixture(UserSessionFactory)
register_fixture(DeviceTokenFactory)
register_fixture(DeviceAuthorizationFactory)


# ============================================================================
# Database Fixtures - Integration Tests
# ============================================================================


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """
    Start a PostgreSQL container with TimescaleDB for the entire test session.

    This fixture:
    - Starts one PostgreSQL container per test session (expensive operation)
    - Automatically handles container lifecycle (start/stop)
    - Uses timescale/timescaledb:latest-pg16 image which includes TimescaleDB extension

    Yields:
        PostgresContainer: The started PostgreSQL container instance.
    """
    with PostgresContainer("timescale/timescaledb:2.18.1-pg17") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def db_engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, None]:
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

    Args:
        postgres_container: The PostgreSQL test container.

    Yields:
        AsyncEngine: Configured async database engine.
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
async def connection(db_engine: AsyncEngine) -> AsyncGenerator[AsyncConnection, None]:
    """
    Session-scoped database connection for transaction management.

    This connection is reused across all tests in the session.
    Individual test isolation is handled by the transaction fixture.

    Args:
        db_engine: The async database engine.

    Yields:
        AsyncConnection: Database connection for the test session.
    """
    async with db_engine.connect() as connection:
        yield connection


@pytest_asyncio.fixture()
async def transaction(connection: AsyncConnection) -> AsyncGenerator[AsyncTransaction, None]:
    """
    Function-scoped transaction that rolls back after each test.

    This ensures complete isolation between tests while maintaining
    the efficiency of transaction rollback (~1ms) vs database recreation.

    Each test gets a fresh transaction that is automatically rolled back
    when the test completes, ensuring no test data persists.

    Args:
        connection: The database connection.

    Yields:
        AsyncTransaction: Transaction that will be rolled back after test.
    """
    async with connection.begin() as transaction:
        yield transaction


@pytest_asyncio.fixture()
async def db_session(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide isolated AsyncSession for each test with automatic rollback.

    This fixture:
    - Creates a new session per test
    - Uses savepoint for transaction isolation within parent transaction
    - Automatically rolls back all changes after test completes
    - Ensures complete test isolation without recreating database

    Args:
        connection: The database connection.
        transaction: The transaction for this test.

    Yields:
        AsyncSession: Isolated session for the test.

    Example:
        ```python
        async def test_create_lap(db_session: AsyncSession) -> None:
            lap = Lap(lap_number=1, lap_time=90.5)
            db_session.add(lap)
            await db_session.commit()
            # Automatically rolled back after test
        ```
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
    """
    Create a TelemetryService instance for testing.

    Args:
        db_session: The database session to inject into the service.

    Returns:
        TelemetryService: Configured service instance for testing.
    """
    return TelemetryService(db_session)


@pytest.fixture
def auth_service(db_session: AsyncSession) -> AuthService:
    """
    Create an AuthService instance for testing.

    Args:
        db_session: The database session to inject into the service.

    Returns:
        AuthService: Configured service instance for testing.
    """
    return AuthService(db_session)


# ============================================================================
# FastAPI Client Fixtures
# ============================================================================


@pytest.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FastAPI app with database dependency override.

    This allows integration tests to use the test database instead of the real one.

    Args:
        db_session: The test database session to override the app dependency.

    Yields:
        AsyncClient: Configured HTTP client for testing FastAPI endpoints.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# Mock Fixtures for Unit Tests
# ============================================================================


@pytest.fixture
def mock_db_session(mocker: MockerFixture) -> AsyncMock:
    """
    Create a mock AsyncSession for unit tests.

    This fixture provides a fully mocked AsyncSession with all common methods
    pre-configured as AsyncMocks or Mocks as appropriate.

    Args:
        mocker: The pytest-mock fixture for creating mocks.

    Returns:
        AsyncMock: Mocked AsyncSession with configured methods.
    """
    mock_session = mocker.AsyncMock(spec=AsyncSession)
    mock_session.commit = mocker.AsyncMock()
    mock_session.rollback = mocker.AsyncMock()
    mock_session.flush = mocker.AsyncMock()
    mock_session.execute = mocker.AsyncMock()
    mock_session.add = mocker.Mock()
    mock_session.add_all = mocker.Mock()
    return mock_session
