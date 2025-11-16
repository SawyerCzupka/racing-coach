# Racing Coach Server

API server for racing telemetry data collection and analysis built with FastAPI, SQLAlchemy (async), and TimescaleDB.

## Features

- **Async-First Architecture**: Built with Python's async/await using AsyncPG
- **Feature-First Organization**: Vertical slices for better maintainability
- **TimescaleDB Integration**: Optimized time-series storage for telemetry data
- **Transaction Management**: Automatic commit/rollback with context managers
- **Type-Safe**: Python 3.13+ type hints with strict type checking
- **Comprehensive Testing**: Unit and integration tests with testcontainers

## Prerequisites

- Python 3.12+
- PostgreSQL with TimescaleDB extension
- Docker (for running tests with testcontainers)
- uv (for dependency management)

## Installation

### 1. Install Dependencies

```bash
cd apps/racing-coach-server
uv sync
```

### 2. Install Test Dependencies

```bash
uv sync --group test
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
database_url=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
debug=False
```

## Database Setup

This project uses **Alembic** for database migrations.

### Initialize Database

Run all migrations to set up the database schema and TimescaleDB hypertables:

```bash
alembic upgrade head
```

### Create New Migration

After modifying models, generate a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Review the generated migration in `migrations/versions/` before applying it.

### Rollback Migration

Roll back the last migration:

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

## Running the Server

### Development Mode (with auto-reload)

```bash
python -m racing_coach_server.main
```

Or with uvicorn directly:

```bash
uvicorn racing_coach_server.app:app --reload
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run with Coverage

```bash
pytest --cov=racing_coach_server --cov-report=html
```

View the coverage report at `htmlcov/index.html`.

## API Endpoints

- `GET /api/v1/health` - Server and database health check
- `POST /api/v1/telemetry/lap` - Upload lap telemetry data
- `GET /api/v1/telemetry/sessions/latest` - Get most recent session

For detailed API documentation, visit http://localhost:8000/docs when the server is running.
