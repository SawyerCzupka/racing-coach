# Racing Coach Server - Architecture Migration Specification

## Overview

This document specifies the target architecture for the racing-coach-server application. The migration involves refactoring from a horizontally-layered architecture to a feature-first (vertical slices) architecture with the following key principles:

- **Feature-first organization**: All code related to a feature lives in its own top-level directory
- **No repositories**: Data access logic lives directly in services
- **Class-based services**: Services are implemented as classes with encapsulated state
- **Async-first**: All I/O operations use async/await with SQLAlchemy AsyncSession
- **Transactional integrity**: Each endpoint operates within a transaction that rolls back on failure
- **Type-safe**: Python 3.13+ type hints with strict type checking

---

## Project Structure

```
src/racing_coach_server/
├── database/                          # Database setup and configuration
│   ├── __init__.py
│   ├── engine.py                      # SQLAlchemy engine and session factory
│   ├── base.py                        # Declarative base with MappedAsDataclass
│   └── init_db.py                     # Database initialization (tables, TimescaleDB setup)
│
├── telemetry/                         # Telemetry feature (sessions, laps, telemetry data)
│   ├── __init__.py                    # Empty per Netflix/Dispatch pattern
│   ├── router.py                      # FastAPI route handlers
│   ├── schemas.py                     # Pydantic request/response models
│   ├── models.py                      # SQLAlchemy ORM models
│   ├── service.py                     # TelemetryService (business logic + data access)
│   └── exceptions.py                  # Feature-specific exceptions
│
├── health/                            # Health check feature
│   ├── __init__.py
│   ├── router.py
│   └── schemas.py
│
├── app.py                             # FastAPI application setup
├── config.py                          # Configuration (environment, settings)
├── logging.py                         # Logging configuration and setup
├── exceptions.py                      # Base application exceptions
├── dependencies.py                    # Dependency injection functions
├── main.py                            # Entry point (uvicorn startup)
```

### Future Feature Structure

When adding new features with subfeatures (loose coupling):
```
analytics/
├── __init__.py
├── router.py                          # Aggregates lap_analysis and comparison routers
├── lap_analysis/
│   ├── __init__.py
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── service.py
│   └── exceptions.py
├── comparison/
│   ├── __init__.py
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── service.py
│   └── exceptions.py
```

When coupling is very tight, keep as single feature:
```
coaching/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── service.py
└── exceptions.py
```

---

## Key Implementation Patterns

### 1. Database Setup (`database/engine.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from racing_coach_server.config import settings

# Create async engine with asyncpg
engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://user:password@localhost/dbname
    echo=False,
    poolclass=NullPool,  # Or use QueuePool for connection pooling in production
)

# Session factory for creating AsyncSession instances
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncSession:
    """Dependency function to provide AsyncSession to route handlers."""
    async with AsyncSessionFactory() as session:
        yield session
```

### 2. Database Base (`database/base.py`)

```python
from sqlalchemy.orm import MappedAsDataclass, declarative_base

# Base for all models - using MappedAsDataclass for dataclass integration
Base = declarative_base(cls=MappedAsDataclass)
```

### 3. Feature Models (`telemetry/models.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import MappedAsDataclass, Mapped, mapped_column
from racing_coach_server.database.base import Base

class TrackSession(Base):
    __tablename__ = "track_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    track_id: Mapped[str] = mapped_column(String)
    car_id: Mapped[str] = mapped_column(String)
    series_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_track_car", "track_id", "car_id"),
    )
```

### 4. Feature Schemas (`telemetry/schemas.py`)

```python
from uuid import UUID
from pydantic import BaseModel, Field

class LapUploadRequest(BaseModel):
    lap: LapTelemetry  # From racing-coach-core
    session: SessionFrame  # From racing-coach-core

class LapUploadResponse(BaseModel):
    status: str = "success"
    message: str = "Lap uploaded successfully"
    lap_id: UUID
```

### 5. Feature Services (`telemetry/service.py`)

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from racing_coach_server.telemetry.models import TrackSession, Lap, Telemetry
from racing_coach_server.telemetry.schemas import LapUploadResponse
from racing_coach_server.telemetry.exceptions import SessionNotFoundError
from racing_coach_coach_core.models import LapTelemetry, SessionFrame

class TelemetryService:
    """Service for telemetry domain: sessions, laps, and telemetry data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        """
        Idempotent session creation - returns existing session if found,
        creates new one otherwise.
        """
        stmt = select(TrackSession).where(
            (TrackSession.track_id == session_frame.track_id) &
            (TrackSession.car_id == session_frame.car_id)
        )
        result = await self.db.execute(stmt)
        existing_session = result.scalar_one_or_none()

        if existing_session:
            return existing_session

        new_session = TrackSession(
            track_id=session_frame.track_id,
            car_id=session_frame.car_id,
            series_id=session_frame.series_id,
        )
        self.db.add(new_session)
        await self.db.flush()  # Flush to get the ID
        return new_session

    async def get_latest_session(self) -> TrackSession | None:
        """Get the most recent track session."""
        stmt = select(TrackSession).order_by(TrackSession.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_lap(
        self,
        session_id: UUID,
        lap_number: int,
        lap_time: float,
        is_valid: bool = True,
    ) -> Lap:
        """Create a lap record for a session."""
        lap = Lap(
            track_session_id=session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )
        self.db.add(lap)
        await self.db.flush()
        return lap

    async def add_telemetry_sequence(
        self,
        telemetry_sequence: TelemetrySequence,
        lap_id: UUID,
        session_id: UUID,
    ) -> None:
        """Batch insert telemetry frames."""
        frames = [
            Telemetry(
                lap_id=lap_id,
                session_id=session_id,
                timestamp=frame.session_time,
                # ... map all fields from frame to Telemetry model
            )
            for frame in telemetry_sequence.frames
        ]
        self.db.add_all(frames)
```

### 6. Feature Router (`telemetry/router.py`)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from racing_coach_server.dependencies import get_telemetry_service
from racing_coach_server.telemetry.service import TelemetryService
from racing_coach_server.telemetry.schemas import LapUploadRequest, LapUploadResponse
from racing_coach_coach_core.models import LapTelemetry, SessionFrame

router = APIRouter()

@router.post(
    "/lap",
    response_model=LapUploadResponse,
    tags=["telemetry"],
)
async def upload_lap(
    request: LapUploadRequest,
    service: TelemetryService = Depends(get_telemetry_service),
) -> LapUploadResponse:
    """Upload a lap with telemetry data."""
    lap_number = request.lap.frames[0].lap_number

    session = await service.add_or_get_session(request.session)
    lap = await service.add_lap(session.id, lap_number, request.lap.lap_time)
    await service.add_telemetry_sequence(request.lap, lap.id, session.id)

    return LapUploadResponse(lap_id=lap.id)
```

### 7. Feature Exceptions (`telemetry/exceptions.py`)

```python
from racing_coach_server.exceptions import RacingCoachException

class TelemetryException(RacingCoachException):
    """Base exception for telemetry domain."""
    pass

class SessionNotFoundError(TelemetryException):
    """Raised when a session cannot be found."""
    pass

class InvalidLapDataError(TelemetryException):
    """Raised when lap data is invalid."""
    pass
```

### 8. Base Application Exception (`exceptions.py`)

```python
class RacingCoachException(Exception):
    """Base exception for all racing coach application errors."""
    pass
```

### 9. Dependency Injection (`dependencies.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from racing_coach_server.database.engine import get_async_session
from racing_coach_server.telemetry.service import TelemetryService

async def get_telemetry_service(
    db: AsyncSession = Depends(get_async_session),
) -> TelemetryService:
    """Provide TelemetryService with injected AsyncSession."""
    return TelemetryService(db)
```

### 10. Logging Configuration (`logging.py`)

```python
import logging
import sys
from racing_coach_server.config import settings

def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.INFO if not settings.debug else logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set uvicorn log level
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
```

### 11. Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### 12. FastAPI App Setup (`app.py`)

```python
from fastapi import FastAPI
from racing_coach_server.logging import setup_logging
from racing_coach_server import telemetry, health

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Racing Coach Server",
    version="0.1.0",
)

# Include routers
app.include_router(telemetry.router, prefix="/api/v1/telemetry")
app.include_router(health.router, prefix="/api/v1")
```

### 13. Entry Point (`main.py`)

```python
import uvicorn
from racing_coach_server.app import app

if __name__ == "__main__":
    uvicorn.run(
        "racing_coach_server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

---

## Transactional Pattern

Each endpoint should operate within a transaction that automatically rolls back on failure. This is achieved through AsyncSession context management:

```python
@router.post("/lap")
async def upload_lap(
    request: LapUploadRequest,
    service: TelemetryService = Depends(get_telemetry_service),
) -> LapUploadResponse:
    """
    Upload a lap with telemetry data.

    The transaction is managed by FastAPI's dependency system:
    - AsyncSession is obtained via get_async_session()
    - If any operation fails, FastAPI will rollback the session
    - If all operations succeed, changes are committed
    """
    try:
        session = await service.add_or_get_session(request.session)
        lap = await service.add_lap(session.id, lap_number, request.lap.lap_time)
        await service.add_telemetry_sequence(request.lap, lap.id, session.id)

        # Commit happens automatically when context exits successfully
        await service.db.commit()

        return LapUploadResponse(lap_id=lap.id)
    except Exception:
        await service.db.rollback()
        raise
```

Alternatively, if you prefer explicit transaction management, create a context manager in `database/engine.py`:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def transactional_session(session: AsyncSession):
    """Context manager for transactional operations."""
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

Then use in endpoints:
```python
async def upload_lap(...) -> LapUploadResponse:
    async with transactional_session(db) as session:
        service = TelemetryService(session)
        # ... operations
        return LapUploadResponse(lap_id=lap.id)
```

---

## Logging Pattern

Use module-level loggers in every file:

```python
import logging

logger = logging.getLogger(__name__)

class TelemetryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.debug("TelemetryService initialized")

    async def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        logger.info(f"Getting or creating session for track {session_frame.track_id}")
        # ...
```

---

## Type Hints

Use Python 3.13+ patterns exclusively:

```python
# ✅ DO: Use | for unions
def get_session(session_id: UUID) -> TrackSession | None:
    ...

# ❌ DON'T: Use Optional
from typing import Optional
def get_session(session_id: UUID) -> Optional[TrackSession]:
    ...

# ✅ DO: Use collections for generics
from collections.abc import Sequence
def process_frames(frames: Sequence[TelemetryFrame]) -> None:
    ...

# ❌ DON'T: Use typing.List, typing.Dict
from typing import List
def process_frames(frames: List[TelemetryFrame]) -> None:
    ...
```

---

## Migration Checklist

- [ ] Create `database/` module with `engine.py` and `base.py`
- [ ] Create `telemetry/` feature directory with all files
- [ ] Create `health/` feature directory
- [ ] Create root-level `app.py` with FastAPI setup
- [ ] Create root-level `config.py`
- [ ] Create root-level `logging.py`
- [ ] Create root-level `exceptions.py`
- [ ] Create root-level `dependencies.py`
- [ ] Create root-level `main.py`
- [ ] Update imports in all files
- [ ] Test that all endpoints work
- [ ] Run type checker (should be clean with strict mode)
- [ ] Update `pyproject.toml` if needed for async dependencies
- [ ] Delete old `database/repositories/` directory
- [ ] Delete old single-service files
- [ ] Update git and commit changes

---

## Notes

- Keep `__init__.py` files empty per Netflix/Dispatch pattern
- Use `logging.getLogger(__name__)` at module level, not per-function
- Always use `await` with async SQLAlchemy operations
- Use `select()` from `sqlalchemy` instead of query API for SQLAlchemy 2.0+
- Feature-specific exceptions should inherit from feature base (e.g., `TelemetryException`)
- Features are independent; avoid circular imports by keeping dependencies flowing inward
- `core/` files live directly in `src/racing_coach_server/`, not in a subdirectory
