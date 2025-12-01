# Racing Coach: System Architecture

## Overview

This document describes the technical architecture of Racing Coach, covering both the current implementation and planned production architecture for the managed service. The system is designed as a distributed application with real-time telemetry collection, time-series data storage, ML-powered coaching, and multi-user web dashboard.

**Competitive Context (2025)**: iRacing's partnership with Cosworth now provides all users free access to Pi Toolbox - professional-grade telemetry analysis software used by IndyCar/WEC teams. This commoditizes basic telemetry visualization. Racing Coach's architecture prioritizes **AI/ML coaching** as the primary differentiator, with telemetry viewing as a supporting feature rather than the main value proposition.

---

## Architecture Principles

1. **Event-Driven**: Loosely coupled components communicate via event bus (client) and async messaging (server)
2. **Async-First**: Non-blocking I/O throughout (async SQLAlchemy, FastAPI, React)
3. **Type-Safe**: Strong typing with Pydantic (Python) and TypeScript (web)
4. **Vertically Sliced**: Feature-first organization (telemetry, sessions, metrics, auth)
5. **Cloud-Native**: Containerized (Docker), horizontally scalable, managed infrastructure
6. **Privacy-Preserving**: User data isolation, opt-in telemetry sharing, anonymization pipeline

---

## System Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Machine                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Racing Coach Client (PySide6 Desktop App)                    │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐    │  │
│  │  │ iRacing    │→ │  Telemetry   │→ │  Event Bus        │    │  │
│  │  │ Collector  │  │  Processor   │  │  (Core Library)   │    │  │
│  │  └────────────┘  └──────────────┘  └───────────────────┘    │  │
│  │         ↓                                    ↓                │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐    │  │
│  │  │ Live Coach │  │  Metrics     │  │  Server API       │    │  │
│  │  │ Handler    │  │  Uploader    │  │  Client (HTTP)    │    │  │
│  │  └────────────┘  └──────────────┘  └───────────────────┘    │  │
│  │         ↓                                    ↓                │  │
│  │  ┌────────────┐                    ┌───────────────────┐    │  │
│  │  │    TTS     │                    │  WebSocket (WS)   │    │  │
│  │  │   Output   │                    │  for Live Updates │    │  │
│  │  └────────────┘                    └───────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                          HTTPS/WSS
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       Cloud Infrastructure                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  API Gateway / Load Balancer (HTTPS, WebSocket)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
│         ┌───────────────────────┼────────────────────┐              │
│         ↓                       ↓                    ↓              │
│  ┌─────────────┐        ┌──────────────┐    ┌──────────────┐      │
│  │ Racing Coach│        │  ML Model    │    │  Web Dashboard│      │
│  │   Server    │←──────→│  Service     │    │  (React SPA)  │      │
│  │  (FastAPI)  │        │  (FastAPI)   │    │  Static CDN   │      │
│  └─────────────┘        └──────────────┘    └──────────────┘      │
│         │                       │                                    │
│         ↓                       ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  PostgreSQL + TimescaleDB (Time-Series Hypertables)      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                 │                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  Object Storage (S3) - ML Models, Exports, Backups       │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Client Application (Desktop)

**Technology Stack**:
- **Language**: Python 3.11+
- **GUI Framework**: PySide6 (Qt for Python)
- **iRacing Integration**: `pyirsdk` (telemetry SDK)
- **Event System**: `racing-coach-core` event bus

**Architecture**:
- **Collectors**: Gather telemetry from iRacing (60 Hz polling loop)
  - `IracingCollector`: Live telemetry via shared memory
  - `ReplayCollector`: Offline telemetry via IBT file parsing
- **Event Bus**: Decoupled communication between components
  - `LapCompletedEvent`: Fired when lap finishes
  - `SessionStartedEvent`: Fired when session begins
  - `TelemetryFrameEvent`: Fired per telemetry frame (60 Hz)
- **Handlers**: React to events
  - `MetricsUploadHandler`: Upload lap metrics to server
  - `LiveCoachingHandler`: (Future) Real-time coaching logic
- **API Client**: HTTP client for server communication (`racing-coach-core.client`)

**Data Flow**:
1. `IracingCollector` polls iRacing SDK (60 Hz)
2. Telemetry frames emitted as `TelemetryFrameEvent`
3. On lap completion, `LapCompletedEvent` fired
4. `MetricsUploadHandler` extracts metrics (braking zones, corners)
5. Upload lap telemetry + metrics to server via `POST /api/v1/telemetry/lap`

**Live Coaching Flow** (Future):
1. `LiveCoachingHandler` subscribes to `TelemetryFrameEvent`
2. Send telemetry to server via WebSocket or HTTP polling
3. Server responds with coaching messages
4. `LiveCoachingHandler` triggers TTS output
5. Audio played to driver during session

**Deployment**:
- **Packaged**: PyInstaller or Nuitka (single executable for Windows)
- **Auto-Update**: Check server for new versions, download and install
- **Config**: Local YAML/TOML file (server URL, TTS settings, coaching aggressiveness)

---

### 2. Server Application (FastAPI)

**Technology Stack**:
- **Language**: Python 3.11+
- **Framework**: FastAPI (async ASGI)
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15+ with TimescaleDB extension
- **Validation**: Pydantic v2
- **Migrations**: Alembic

**Architecture**: Feature-First (Vertical Slices)

```
apps/racing-coach-server/src/racing_coach_server/
├── auth/                 # User authentication and authorization
│   ├── router.py         # Endpoints: /api/v1/auth/register, /login, /refresh
│   ├── service.py        # JWT creation, password hashing, user management
│   ├── schemas.py        # Pydantic models: RegisterRequest, LoginResponse
│   └── dependencies.py   # FastAPI dependencies: get_current_user()
├── telemetry/            # Telemetry upload and retrieval
│   ├── router.py         # Endpoints: POST /api/v1/telemetry/lap
│   ├── service.py        # Store telemetry frames in TimescaleDB
│   ├── schemas.py        # TelemetryFrame, LapUploadRequest
│   └── models.py         # SQLAlchemy models: TelemetryFrame (hypertable)
├── sessions/             # Session management
│   ├── router.py         # Endpoints: GET /api/v1/sessions, /sessions/{id}
│   ├── service.py        # Query sessions, aggregate session stats
│   ├── schemas.py        # SessionResponse, SessionDetailResponse
│   └── models.py         # SQLAlchemy models: Session, Lap
├── metrics/              # Lap metrics (braking zones, corners)
│   ├── router.py         # Endpoints: POST /api/v1/metrics/lap, GET /metrics/compare
│   ├── service.py        # Store and retrieve metrics
│   ├── comparison_service.py  # Compare two laps (delta calculations)
│   ├── schemas.py        # BrakingZone, Corner, MetricsUploadRequest
│   └── models.py         # SQLAlchemy models: BrakingZone, Corner
├── ml/                   # (Future) ML model inference
│   ├── router.py         # Endpoints: POST /api/v1/ml/score-lap
│   ├── service.py        # Load model, run inference, return structured feedback
│   └── models.py         # (Not SQLAlchemy, ML model wrapper)
├── coaching/             # (Future) Live coaching orchestration
│   ├── router.py         # Endpoints: WebSocket /api/v1/coaching/live
│   ├── service.py        # Receive telemetry, generate coaching, return messages
│   └── schemas.py        # CoachingMessage, LiveTelemetryFrame
├── health/               # Health checks
│   └── router.py         # Endpoints: GET /api/v1/health
└── app.py                # FastAPI app initialization, CORS, middleware
```

**Database Models**:

```sql
-- Users (multi-tenancy)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (1 iRacing session = 1 record)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    track_name VARCHAR(255) NOT NULL,
    car_name VARCHAR(255) NOT NULL,
    session_type VARCHAR(50),  -- Practice, Qualify, Race
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP
);

-- Laps (1 lap = 1 record)
CREATE TABLE laps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lap_number INT NOT NULL,
    lap_time FLOAT,  -- seconds
    is_valid BOOLEAN DEFAULT TRUE,
    completed_at TIMESTAMP NOT NULL
);

-- Telemetry Frames (TimescaleDB hypertable)
CREATE TABLE telemetry_frames (
    time TIMESTAMPTZ NOT NULL,
    lap_id UUID REFERENCES laps(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    speed FLOAT,
    throttle FLOAT,
    brake FLOAT,
    clutch FLOAT,
    steering FLOAT,
    gear INT,
    rpm FLOAT,
    lat FLOAT,  -- GPS latitude
    lon FLOAT,  -- GPS longitude
    alt FLOAT,  -- GPS altitude
    lat_accel FLOAT,  -- Lateral G
    lon_accel FLOAT,  -- Longitudinal G
    vert_accel FLOAT, -- Vertical G
    yaw_rate FLOAT,
    pitch_rate FLOAT,
    roll_rate FLOAT,
    -- ... (50+ channels total)
    PRIMARY KEY (time, lap_id)
);
SELECT create_hypertable('telemetry_frames', 'time');
CREATE INDEX idx_telemetry_lap ON telemetry_frames(lap_id, time DESC);
CREATE INDEX idx_telemetry_user ON telemetry_frames(user_id, time DESC);

-- Braking Zones (extracted metrics)
CREATE TABLE braking_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lap_id UUID REFERENCES laps(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    start_distance FLOAT,  -- Lap distance %
    end_distance FLOAT,
    entry_speed FLOAT,
    min_speed FLOAT,
    max_brake_pressure FLOAT,
    duration FLOAT,  -- seconds
    is_trail_braking BOOLEAN
);

-- Corners (extracted metrics)
CREATE TABLE corners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lap_id UUID REFERENCES laps(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    start_distance FLOAT,
    apex_distance FLOAT,
    end_distance FLOAT,
    entry_speed FLOAT,
    apex_speed FLOAT,
    exit_speed FLOAT,
    max_lat_g FLOAT,
    time_in_corner FLOAT
);
```

**API Endpoints**:

**Authentication**:
- `POST /api/v1/auth/register` - Create new user account
- `POST /api/v1/auth/login` - Login, receive JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate refresh token

**Telemetry**:
- `POST /api/v1/telemetry/lap` - Upload lap telemetry and session metadata
- `GET /api/v1/telemetry/sessions/latest` - Get user's latest session

**Sessions**:
- `GET /api/v1/sessions` - List user's sessions (paginated)
- `GET /api/v1/sessions/{id}` - Get session details with all laps

**Metrics**:
- `POST /api/v1/metrics/lap` - Upload extracted metrics (braking zones, corners)
- `GET /api/v1/metrics/lap/{lap_id}` - Get metrics for a specific lap
- `GET /api/v1/metrics/compare?lap1={id}&lap2={id}` - Compare two laps

**ML Coaching** (Future):
- `POST /api/v1/ml/score-lap` - Score a lap, return structured feedback
- `GET /api/v1/ml/models` - List available ML models (per car/track)

**Live Coaching** (Future):
- `WebSocket /api/v1/coaching/live` - Real-time telemetry streaming + coaching messages

**Authorization**:
- All endpoints (except `/auth/*` and `/health`) require JWT in `Authorization: Bearer <token>` header
- FastAPI dependency `get_current_user()` validates JWT and extracts `user_id`
- All database queries filtered by `user_id` (user isolation)

**Performance Optimizations**:
- Connection pooling: AsyncPG pool (min=5, max=20 connections)
- Query optimization: Indexes on `user_id`, `lap_id`, `time` (TimescaleDB)
- Compression: TimescaleDB automatic compression for old telemetry (>7 days)
- Caching: Redis for session metadata, reference laps (future)

---

### 3. ML Model Service (Future)

**Technology Stack**:
- **Language**: Python 3.11+
- **Framework**: FastAPI (separate microservice)
- **ML Libraries**: PyTorch or TensorFlow, ONNX Runtime
- **Serving**: NVIDIA Triton Inference Server (optional, for high scale)

**Architecture**:
- **Model Repository**: S3 bucket with versioned models (e.g., `skippy-limerock-v1.onnx`)
- **Model Loader**: Download model on startup, keep in memory
- **Inference Endpoint**: `POST /ml/score-lap` (input: telemetry JSON, output: structured feedback)
- **Preprocessing**: Normalize telemetry, segment into fixed-length sequences
- **Postprocessing**: Convert model outputs to structured feedback (deltas, anomaly scores)

**API Contract**:

**Request**:
```json
{
  "lap_id": "uuid",
  "car": "Skip Barber Formula 2000",
  "track": "Lime Rock Park",
  "telemetry": [
    {"time": 0.0, "speed": 120.5, "throttle": 0.8, "brake": 0.0, "steering": 0.1, ...},
    {"time": 0.016, "speed": 121.2, "throttle": 0.85, "brake": 0.0, "steering": 0.12, ...},
    ...
  ]
}
```

**Response**:
```json
{
  "lap_id": "uuid",
  "model_version": "skippy-limerock-v1",
  "overall_score": 0.85,  // 0-1, higher is better
  "feedback": [
    {
      "corner": "Turn 3",
      "distance": 0.42,  // 42% lap distance
      "type": "braking",
      "severity": "high",
      "delta": {"brake_point": -10.5, "unit": "meters"},
      "description": "Braking too late"
    },
    {
      "corner": "Turn 3",
      "distance": 0.43,
      "type": "speed",
      "severity": "medium",
      "delta": {"apex_speed": -5.2, "unit": "km/h"},
      "description": "Apex speed slow"
    }
  ]
}
```

**Deployment**:
- **Container**: Docker image with model baked in (or download on startup)
- **GPU**: Deploy on GPU instance (AWS P3, GCP T4) for <100ms inference
- **Horizontal Scaling**: Multiple instances behind load balancer
- **Monitoring**: Prometheus metrics (inference latency, error rate, throughput)

---

### 4. Web Dashboard (React)

**Technology Stack**:
- **Language**: TypeScript
- **Framework**: React 19
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS (or Material-UI, shadcn/ui)
- **State Management**: TanStack Query (React Query) for server state
- **Charts**: Recharts or Plotly.js
- **API Client**: Auto-generated from OpenAPI spec via Orval

**Architecture**:
```
apps/racing-coach-web/src/
├── api/
│   └── generated/        # Orval-generated API client (TypeScript + React Query hooks)
├── components/
│   ├── Auth/             # Login, Register, ProtectedRoute
│   ├── Dashboard/        # Session list, lap cards
│   ├── LapDetail/        # Charts, metrics, telemetry visualization
│   ├── LapComparison/    # Side-by-side lap comparison
│   └── LiveCoaching/     # Live coaching controls, status
├── pages/
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── SessionDetailPage.tsx
│   ├── LapComparisonPage.tsx
│   └── SettingsPage.tsx
├── hooks/
│   ├── useAuth.ts        # Auth context (JWT storage, login/logout)
│   └── useLiveCoaching.ts # WebSocket connection for live updates
└── App.tsx               # Router, Auth context provider
```

**Key Features**:
- **Authentication**: JWT stored in HttpOnly cookie or localStorage
- **Protected Routes**: Redirect to login if unauthenticated
- **Session Browser**: List sessions with filters (car, track, date)
- **Lap Detail**: Charts (speed, inputs, G-forces), metrics table (braking zones, corners)
- **Lap Comparison**: Overlay charts, delta times, side-by-side metrics
- **Live Coaching** (Future): Real-time session status, coaching messages received

**API Client Generation**:
```bash
# Server must be running on localhost:8000
npm run generate:api
# Fetches OpenAPI spec from http://localhost:8000/openapi.json
# Generates TypeScript types and React Query hooks in src/api/generated/
```

**Deployment**:
- **Build**: `npm run build` → static files in `dist/`
- **Hosting**: CDN (Cloudflare, Vercel, Netlify) or S3 + CloudFront
- **Environment Variables**: API base URL (injected at build time)

---

### 5. Database (PostgreSQL + TimescaleDB)

**Technology Stack**:
- **Database**: PostgreSQL 15+
- **Extension**: TimescaleDB (time-series optimization)
- **Hosting**: Managed service (AWS RDS, Timescale Cloud, Supabase)

**TimescaleDB Hypertables**:
- `telemetry_frames`: Partitioned by time (1-day chunks)
- **Compression**: Automatic after 7 days (10x storage reduction)
- **Retention**: Raw telemetry kept for 90 days, then aggregated or archived

**Indexes**:
- `idx_telemetry_lap`: (lap_id, time DESC) - Fast lap telemetry retrieval
- `idx_telemetry_user`: (user_id, time DESC) - User isolation queries
- `idx_sessions_user`: (user_id, started_at DESC) - Session list pagination
- `idx_laps_session`: (session_id, lap_number) - Session lap retrieval

**Backups**:
- Daily automated backups (managed service or pg_dump)
- Retention: 30 days
- Point-in-time recovery (PITR) for disaster recovery

**Scaling**:
- **Vertical**: Increase CPU/RAM (16 vCPU, 64 GB RAM for 1M+ laps)
- **Horizontal**: TimescaleDB distributed hypertables (multi-node, future)
- **Read Replicas**: Offload analytics queries to read replicas

---

### 6. Object Storage (S3)

**Use Cases**:
- **ML Models**: Versioned model files (e.g., `models/skippy-limerock-v1.onnx`)
- **Data Exports**: CSV/Parquet exports for ML training
- **Backups**: Database backups, session replays
- **Static Assets**: Web dashboard assets (if not using CDN)

**Structure**:
```
racing-coach-production/
├── models/
│   ├── skippy-limerock-v1.onnx
│   ├── skippy-limerock-v1.metadata.json
│   └── mx5-limerock-v1.onnx
├── exports/
│   ├── 2025-12-01-skippy-limerock-telemetry.parquet
│   └── 2025-12-01-mx5-limerock-telemetry.parquet
├── backups/
│   └── db-backup-2025-12-01.sql.gz
└── replays/ (future)
    └── session-uuid.mp4
```

---

## Data Flow: Lap Upload

### Step-by-Step

1. **Client**: User completes lap in iRacing
2. **Client**: `IracingCollector` detects lap completion, emits `LapCompletedEvent`
3. **Client**: `MetricsUploadHandler` extracts metrics:
   - Braking zones (via `racing-coach-core.algs.braking`)
   - Corners (via `racing-coach-core.algs.cornering`)
4. **Client**: Upload telemetry + metrics to server:
   ```
   POST /api/v1/telemetry/lap
   {
     "session": {...},  // Track, car, session type
     "lap": {...},      // Lap number, lap time
     "telemetry": [...] // Array of telemetry frames (60 Hz)
   }
   POST /api/v1/metrics/lap
   {
     "lap_id": "uuid",
     "braking_zones": [...],
     "corners": [...]
   }
   ```
5. **Server**: Validate JWT, extract `user_id`
6. **Server**: Create session (if new) and lap records
7. **Server**: Bulk insert telemetry frames into TimescaleDB hypertable
8. **Server**: Insert braking zones and corners into metrics tables
9. **Server**: Return `201 Created` with lap ID
10. **Web Dashboard**: User refreshes, sees new lap in session list

---

## Data Flow: Live Coaching (Future)

### Step-by-Step

1. **Client**: User starts iRacing session, enables live coaching
2. **Client**: Establish WebSocket connection to server: `wss://api.racingcoach.io/api/v1/coaching/live`
3. **Server**: Authenticate WebSocket via JWT query param or header
4. **Client**: Stream telemetry frames in real-time (every 1 second = 60 frames batched)
5. **Server**: Align current telemetry with reference lap (distance-based)
6. **Server**: Detect deviations (braking point, apex speed, racing line)
7. **Server**: (Optional) Call ML service for anomaly detection
8. **Server**: Generate coaching message: "Brake earlier in Turn 3"
9. **Server**: Send coaching message via WebSocket
10. **Client**: Receive message, trigger TTS output
11. **Client**: Audio played to driver during session

**Latency Target**: <200ms end-to-end (telemetry sent → coaching received)

---

## Security Architecture

### Authentication (JWT-Based)

**Registration Flow**:
1. User submits email + password to `POST /api/v1/auth/register`
2. Server hashes password (bcrypt or argon2)
3. Server creates user record, returns JWT tokens:
   - **Access Token**: Short-lived (15 minutes), used for API requests
   - **Refresh Token**: Long-lived (7 days), used to refresh access token
4. Client stores tokens (HttpOnly cookie or localStorage)

**Login Flow**:
1. User submits email + password to `POST /api/v1/auth/login`
2. Server verifies password hash
3. Server returns JWT tokens (same as registration)

**Authorization**:
- All protected endpoints require `Authorization: Bearer <access_token>` header
- FastAPI dependency `get_current_user()` validates JWT signature and expiration
- Extract `user_id` from JWT claims, inject into request context

**Token Refresh**:
1. Access token expires (15 minutes)
2. Client sends refresh token to `POST /api/v1/auth/refresh`
3. Server validates refresh token, issues new access token
4. If refresh token expires (7 days), force re-login

### Authorization (Multi-Tenancy)

**User Isolation**:
- All database queries filtered by `user_id` (extracted from JWT)
- Users can only access their own sessions, laps, and telemetry
- Admin role (future): can access all user data for moderation

**Data Privacy**:
- Telemetry sharing is opt-in (checkbox during registration)
- Anonymization pipeline strips PII before ML training
- Self-hosted users keep all data local (never sent to cloud)

### Security Best Practices

**HTTPS Everywhere**:
- Enforce HTTPS in production (Let's Encrypt SSL)
- HSTS header: `Strict-Transport-Security: max-age=31536000`

**CORS Configuration**:
- Allow only web dashboard origin: `https://app.racingcoach.io`
- Credentials allowed for cookies

**Input Validation**:
- Pydantic schemas validate all API inputs
- Reject malformed requests (400 Bad Request)

**Rate Limiting**:
- Prevent abuse: 100 requests/minute per user (via API key or JWT)
- DDoS protection: Cloudflare or AWS Shield

**Error Handling**:
- Never leak sensitive info in error responses (no stack traces in production)
- Generic errors: `{"detail": "Internal server error"}` (log details server-side)

**Secrets Management**:
- Environment variables for sensitive config (database password, JWT secret)
- Never commit secrets to Git (use `.env` files, gitignored)
- Rotate secrets periodically (JWT secret every 90 days)

---

## Deployment Architecture

### Development (Local)

**Docker Compose**:
```yaml
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: racing_coach
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: racing_coach_dev
    ports:
      - "5432:5432"

  racing-coach-server:
    build: ./apps/racing-coach-server
    environment:
      DATABASE_URL: postgresql+asyncpg://racing_coach:dev_password@timescaledb:5432/racing_coach_dev
      JWT_SECRET: dev_secret
    ports:
      - "8000:8000"
    depends_on:
      - timescaledb

  racing-coach-web:
    build: ./apps/racing-coach-web
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "3000:3000"
```

**Run**:
```bash
docker compose up
# Server: http://localhost:8000
# Web: http://localhost:3000
# DB: localhost:5432
```

### Production (Managed Service)

**Cloud Provider Options**:
- **AWS**: ECS Fargate (server), RDS PostgreSQL (db), S3 (storage), CloudFront (web CDN)
- **GCP**: Cloud Run (server), Cloud SQL (db), GCS (storage), Cloud CDN (web)
- **DigitalOcean**: App Platform (server + web), Managed PostgreSQL (db), Spaces (storage)
- **Fly.io**: Fly Machines (server), Supabase (db + auth), Cloudflare R2 (storage)

**Recommended Stack (Cost-Optimized)**:
- **Server**: Fly.io or Railway ($10-50/month for 2-4 instances)
- **Database**: Supabase or Timescale Cloud ($25-100/month for 10 GB)
- **Storage**: Cloudflare R2 ($0.015/GB, cheaper than S3)
- **Web**: Cloudflare Pages or Vercel (free tier)
- **Total**: $50-200/month for 100-1,000 users

**High-Scale Stack (1,000+ Users)**:
- **Server**: AWS ECS Fargate (auto-scaling, 4-16 instances)
- **Database**: AWS RDS TimescaleDB (db.m5.xlarge, 100 GB SSD)
- **Storage**: S3 Standard (with Glacier archival)
- **Web**: CloudFront CDN
- **ML Service**: EC2 P3 instances (GPU inference)
- **Total**: $500-2,000/month

**CI/CD Pipeline**:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd apps/racing-coach-server
          uv run pytest

  build-server:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t racing-coach-server:${{ github.sha }} ./apps/racing-coach-server
      - name: Push to registry
        run: docker push registry.fly.io/racing-coach:${{ github.sha }}

  deploy:
    needs: build-server
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Fly.io
        run: flyctl deploy --image registry.fly.io/racing-coach:${{ github.sha }}
```

---

## Monitoring & Observability

### Logging

**Server Logs**:
- **Level**: INFO in production, DEBUG in development
- **Format**: JSON structured logs (timestamp, level, message, user_id, request_id)
- **Storage**: Cloudwatch Logs, Datadog, or Loki

**Example Log**:
```json
{
  "timestamp": "2025-12-01T12:34:56Z",
  "level": "INFO",
  "message": "Lap uploaded successfully",
  "user_id": "uuid",
  "lap_id": "uuid",
  "request_id": "abc123",
  "duration_ms": 245
}
```

### Metrics

**Application Metrics** (Prometheus format):
- `http_requests_total{method, endpoint, status}` - Request count
- `http_request_duration_seconds{method, endpoint}` - Request latency histogram
- `db_query_duration_seconds{query}` - Database query latency
- `ml_inference_duration_seconds{model}` - ML inference latency
- `active_users` - Current WebSocket connections (live coaching)

**Infrastructure Metrics**:
- CPU, memory, disk usage
- Database connections (active, idle)
- Network I/O

**Alerting**:
- Error rate >1% → Slack/PagerDuty alert
- P95 latency >1s → Warning
- Database connections >80% capacity → Scale up

### Tracing

**Distributed Tracing** (OpenTelemetry):
- Trace requests across services (server → ML service → database)
- Identify bottlenecks (slow queries, ML inference latency)
- Tools: Jaeger, Zipkin, Datadog APM

---

## Self-Hosted Deployment

**Target Users**:
- Privacy-conscious users who want full data ownership
- Cost-sensitive users who can self-host cheaper than paying subscription
- Power users who want to customize/extend the system

**Deployment Options**:

**Option 1: Docker Compose (Simplest)**:
```bash
git clone https://github.com/sawyer/racing-coach
cd racing-coach
cp .env.example .env
# Edit .env with custom passwords, JWT secret
docker compose -f docker-compose.prod.yml up -d
# Access web at http://localhost:3000
```

**Option 2: Kubernetes (Advanced)**:
- Helm chart provided (future)
- Deploy to local k3s cluster or cloud Kubernetes

**Requirements**:
- 4 CPU cores, 8 GB RAM (minimum)
- 50 GB disk space (grows with telemetry data)
- Docker or Kubernetes

**Updates**:
- `git pull && docker compose up -d` (automatic migrations)

---

## Scalability Considerations

### Horizontal Scaling

**Server**:
- Stateless design (no in-memory sessions)
- Scale horizontally behind load balancer (2-16 instances)
- Session affinity not required

**Database**:
- TimescaleDB compression (10x storage reduction)
- Read replicas for analytics queries (future)
- Distributed hypertables for multi-node (future, 10M+ laps)

**ML Service**:
- Model loaded in memory (1-2 GB per instance)
- Scale horizontally (4-8 GPU instances for high load)
- Inference batching (process multiple laps in parallel)

### Performance Optimization

**API**:
- Response caching (Redis for session metadata)
- Database query optimization (indexes, EXPLAIN ANALYZE)
- Async I/O (FastAPI async, SQLAlchemy async)

**ML Inference**:
- Model quantization (FP16, INT8)
- ONNX Runtime (2-5x faster than PyTorch)
- GPU batching (process 8-16 laps in parallel)

**Web Dashboard**:
- Code splitting (lazy load pages)
- API response caching (React Query)
- CDN for static assets

---

## Future Architecture Enhancements

### Real-Time Data Pipeline (Kafka/Pulsar)

**Use Case**: High-throughput telemetry ingestion (1,000+ concurrent users)

**Architecture**:
```
Client → Kafka Producer → Kafka Topic → Stream Processor → TimescaleDB
                                      ↓
                                  ML Service (real-time scoring)
```

### Caching Layer (Redis)

**Use Cases**:
- Session metadata (avoid repeated DB queries)
- Reference laps (frequently accessed)
- ML model predictions (cache common laps)

### CDN for Telemetry Assets

**Use Case**: Serve telemetry charts as pre-rendered images (reduce client-side rendering)

**Architecture**:
- Server generates PNG charts on lap upload
- Store in S3, serve via CloudFront CDN
- Web dashboard embeds images (faster load times)

---

**Last Updated**: December 2025
**Document Owner**: Racing Coach Engineering Team
**Status**: Living document, updated as architecture evolves
