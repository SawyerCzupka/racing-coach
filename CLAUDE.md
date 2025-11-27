# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Racing Coach is an AI-powered sim racing coach that provides real-time feedback for iRacing. It collects telemetry data, analyzes driving performance against reference data, and provides actionable insights.

## Repository Structure

This is a monorepo managed with `uv` workspaces:

- **apps/racing-coach-server**: FastAPI server with async SQLAlchemy and TimescaleDB
- **apps/racing-coach-client**: Desktop app that connects to iRacing via pyirsdk (Must run on Win11 w/o Docker to properly connect to iracing in live mode)
- **apps/racing-coach-web**: Vite + React 19 + TypeScript dashboard
- **libs/racing-coach-core**: Shared Python library for telemetry models, algorithms, and event handling

## Common Commands

### Server (apps/racing-coach-server)

```bash
cd apps/racing-coach-server
uv sync --group test           # Install with test dependencies
uv run fastapi dev src/racing_coach_server/app.py  # Run dev server
uv run pytest                  # Run all tests
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only (requires Docker)
uv run alembic upgrade head    # Run migrations
uv run alembic revision --autogenerate -m "message"  # Create migration
```

### Client (apps/racing-coach-client)

```bash
cd apps/racing-coach-client
uv sync --group test
uv run run-client              # Launch desktop app
uv run pytest
uv run pytest -m unit
```

### Core Library (libs/racing-coach-core)

```bash
cd libs/racing-coach-core
uv sync --group test
uv run pytest
```

### Web Dashboard (apps/racing-coach-web)

```bash
cd apps/racing-coach-web
npm install
npm run generate:api           # Generate API client from OpenAPI (server must be running)
npm run dev                    # Start dev server on port 3000
npm run build                  # Production build
npm run lint
npm run format
```

### Docker (full stack)

```bash
docker compose up              # Start TimescaleDB, server, web, and pgAdmin
docker compose up timescaledb racing-coach-server  # Server + DB only
```

## Architecture Notes

### Server (Feature-First Organization)

The server uses vertical slices: `health/`, `telemetry/`, `sessions/`, `metrics/`. Each feature module has its own `router.py`, `schemas.py`, `service.py`, and `models.py`.

- Database: AsyncPG + SQLAlchemy async with TimescaleDB hypertables for time-series telemetry
- API docs: http://localhost:8000/docs when running

### Client (Event-Driven Architecture)

The client uses an event bus pattern from racing-coach-core for decoupled communication between components. Collectors gather iRacing data, handlers process events (lap completion, metrics upload, etc.).

### Core Library Modules

- **algs/**: Analysis algorithms (braking zones, cornering, metrics extraction)
- **events/**: Event bus system with typed events
- **models/**: Pydantic models for telemetry data, events, and API responses
- **viz/**: Plotly-based chart generation for lap analysis
- **client/**: HTTP client for server communication

### Web Dashboard

Uses Orval to auto-generate TypeScript types and TanStack Query hooks from the FastAPI OpenAPI spec (`npm run generate:api`). The API client is generated to `src/api/generated/`.

## Code Style

- Python: Ruff for linting/formatting, basedpyright in strict mode, line length 100
- TypeScript: ESLint + Prettier
- All Python apps use pytest with markers: `unit`, `integration`, `slow`
- Integration tests use testcontainers for isolated PostgreSQL instances
