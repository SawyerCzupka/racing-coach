# Base stage
FROM python:3.13-slim-trixie AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Development stage
FROM base AS development
# Copy shared library (needed for editable install to work)
COPY libs/racing-coach-core /app/libs/racing-coach-core

# Copy only dependency files for the main app
COPY apps/racing-coach-server/pyproject.toml apps/racing-coach-server/uv.lock ./apps/racing-coach-server/

WORKDIR /app/apps/racing-coach-server
# Step 1: Install 3rd party dependencies only (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

# Copy application code after 3rd party dependencies are installed
COPY apps/racing-coach-server /app/apps/racing-coach-server

# Step 2: Install local packages (racing-coach-core and racing-coach-server)
# This layer will be quick since all 3rd party deps are already installed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Command will be overridden by docker-compose
CMD ["uv", "run", "fastapi", "run", "src/racing_coach_server/app.py", "--host", "0.0.0.0"]

# Builder stage for production
FROM base AS builder
# Copy shared library (needed for editable install to work)
COPY libs/racing-coach-core ./libs/racing-coach-core

# Copy only dependency files for the main app
COPY apps/racing-coach-server/pyproject.toml apps/racing-coach-server/uv.lock ./apps/racing-coach-server/

WORKDIR /app/apps/racing-coach-server
# Step 1: Install 3rd party production dependencies only (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code after 3rd party dependencies are installed
COPY apps/racing-coach-server ./apps/racing-coach-server
COPY libs ./libs

# Step 2: Install local packages (racing-coach-core and racing-coach-server)
# This layer will be quick since all 3rd party deps are already installed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.13-slim-trixie AS production

WORKDIR /app

# Copy virtual environment from builder (keep at same path)
COPY --from=builder /app/apps/racing-coach-server/.venv /app/apps/racing-coach-server/.venv

# Copy application code
COPY libs /app/libs
COPY apps/racing-coach-server /app/apps/racing-coach-server

# Add virtual environment to PATH
ENV PATH="/app/apps/racing-coach-server/.venv/bin:$PATH"

WORKDIR /app/apps/racing-coach-server

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=2)"

# Run the application
CMD ["fastapi", "run", "src/racing_coach_server/app.py"]
