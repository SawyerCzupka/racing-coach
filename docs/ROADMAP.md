# Racing Coach: Development Roadmap

## Overview

This roadmap outlines the phased development approach for Racing Coach, prioritizing managed service MVP over self-hosted deployment. The strategy focuses on delivering live coaching capabilities early, establishing secure multi-user infrastructure, and progressively building toward ML-powered coaching intelligence.

## Current State Assessment

### What's Working ✅
- **Telemetry Collection**: Client successfully connects to iRacing via `pyirsdk`, captures 60Hz telemetry (~50 channels)
- **Data Storage**: PostgreSQL + TimescaleDB hypertables for time-series telemetry, async SQLAlchemy ORM
- **Metrics Extraction**: Braking zone and corner detection algorithms (Python + Rust implementations)
- **Server API**: FastAPI async server with feature-first organization (telemetry, sessions, metrics, health)
- **Lap Comparison**: Distance-based alignment, delta calculations for braking/cornering metrics
- **Visualization**: Plotly-based charts (track map, speed, inputs, G-forces, friction circle)
- **Web Dashboard**: React 19 + TypeScript, auto-generated API client from OpenAPI spec

### Partially Working ⚠️
- **Web Dashboard**: Minimal but functional, displays data but lacks interactive features
- **Braking/Corner Detection**: Works but uses simplistic thresholds (5% brake, 15% steering) that don't adapt to car/track/driver
- **Server API**: Complete endpoints but no authentication or authorization

### Critical Gaps ❌
- **User Authentication**: No auth system (blocking managed service deployment)
- **Live Coaching**: No real-time feedback generation or TTS delivery
- **ML Models**: No machine learning capabilities whatsoever
- **Security**: CORS missing, error leakage, hardcoded credentials, no input validation
- **Testing**: Minimal test coverage (no web tests, no E2E tests)
- **CI/CD**: No automated pipeline

### Production Readiness Score: 5.5/10
(Per `PRODUCTION_READINESS.md` assessment)

**Blocking issues for managed service**:
1. Security vulnerabilities (auth, CORS, credential management)
2. Insufficient testing coverage
3. No deployment infrastructure

---

## Development Milestones

### Milestone 1: MVP - Public Beta Launch
**Duration**: 12-16 weeks (~10 hrs/week)
**Priority**: CRITICAL (enable data crowdsourcing for ML)
**Goal**: Launch public beta with live coaching and data collection to crowdsource telemetry for future ML training

#### Tasks

**1.1 Simple Authentication (3-4 weeks)**
- [ ] Email/password registration and login (server endpoints)
- [ ] JWT tokens (access token only, skip refresh for MVP)
- [ ] Password hashing (bcrypt)
- [ ] User database table and schema migrations
- [ ] Client authentication integration (store token, send with requests)
- [ ] Basic error handling and validation

**1.2 Reference Lap System (2 weeks)**
- [ ] "Set as reference lap" feature in desktop client
- [ ] Reference lap storage (per car/track combo per user)
- [ ] Reference lap selection UI in client
- [ ] API endpoints for reference lap CRUD
- [ ] Default reference selection (fastest user lap for combo)

**1.3 Live Coaching Logic (3-4 weeks)**
- [ ] Real-time lap comparison algorithm (distance-based alignment)
- [ ] Deviation detection (braking point delta, apex speed delta, line deviation)
- [ ] Rule-based coaching message generation ("Brake earlier", "Carry more speed")
- [ ] Configurable thresholds (sensitivity settings)
- [ ] Message cooldown logic (avoid spamming driver)
- [ ] Performance optimization (<100ms alignment latency)

**1.4 TTS Integration (2 weeks)**
- [ ] Evaluate TTS options (local: pyttsx3, cloud: Google TTS)
- [ ] Integrate chosen TTS library
- [ ] Voice configuration (speed, volume)
- [ ] Audio output testing with iRacing
- [ ] Fallback to on-screen text if TTS fails

**1.5 Client GUI for Coaching (3 weeks)**
- [ ] Coaching settings panel (enable/disable, volume, aggressiveness)
- [ ] Reference lap selection dropdown
- [ ] Live coaching status indicator
- [ ] Real-time delta display (current vs reference)
- [ ] Session summary (coaching messages received)

**1.6 Telemetry Opt-In & Data Collection (2 weeks)**
- [ ] Consent checkbox during registration
- [ ] Telemetry sharing toggle in client settings
- [ ] Privacy policy and terms (GDPR-compliant)
- [ ] Clear explanation of data usage
- [ ] Mark telemetry with consent flag in database
- [ ] Data export endpoint (admin-only, for ML training)

**1.7 Essential Security & Deployment (2-3 weeks)**
- [ ] Fix CORS configuration
- [ ] Remove error leakage in responses
- [ ] Migrate hardcoded credentials to env vars
- [ ] Basic deployment setup (Docker Compose on VPS)
- [ ] SSL certificates (Let's Encrypt)
- [ ] Basic monitoring (uptime, logs)

#### Deliverable
Desktop app with live voice coaching. Users can register, upload telemetry, set reference laps, and receive real-time TTS feedback during iRacing sessions. Opt-in telemetry sharing enables data crowdsourcing for future ML training.

#### Success Criteria
- [ ] 20+ beta users registered and driving with live coaching
- [ ] 50%+ of users opt-in to telemetry sharing
- [ ] 1,000+ laps collected (crowdsourced data for ML)
- [ ] 70%+ users report coaching is helpful
- [ ] <300ms end-to-end coaching latency (telemetry → TTS)

---

### Milestone 2: Post-MVP Improvements (Optional)
**Duration**: 8-12 weeks (~10 hrs/week)
**Priority**: LOW (only if time/interest after MVP)
**Goal**: Polish user experience and add nice-to-have features

**Note**: With Cosworth Pi Toolbox now free, telemetry visualization is commoditized. Focus effort on ML coaching instead.

#### Tasks (Optional)

**2.1 Web Dashboard Basics**
- [ ] View session list and lap details (read-only)
- [ ] Simple telemetry charts (speed, inputs)
- [ ] Lap comparison view

**2.2 Enhanced Data Quality**
- [ ] Filter incomplete/invalid laps automatically
- [ ] Mark laps as "clean" vs. "dirty"
- [ ] Community reference lap ratings

#### Deliverable
Optional polish features if time permits after MVP.

#### Success Criteria
- Only pursue if MVP is successful and user feedback requests these features

---

### Milestone 3: ML Coaching Prototype
**Duration**: 16-20 weeks (~10 hrs/week)
**Priority**: HIGH (core innovation after MVP data collection)
**Goal**: Demonstrate ML-powered coaching on single car/track combo

**Note**: Only start after collecting 1,000+ laps from MVP users

#### Tasks

**3.1 Car/Track Selection & Data Collection (4 weeks)**
- [ ] Select prototype combo (e.g., Skip Barber @ Lime Rock Park)
- [ ] Use crowdsourced data from MVP (filter to combo, 500+ laps target)
- [ ] Clean and label data (mark laps as "expert", "intermediate", "beginner")
- [ ] Extract features (braking zones, corners, speeds, inputs, G-forces)
- [ ] Split data (80% train, 10% validation, 10% test)

**3.2 ML Architecture Research (3 weeks)**
- [ ] Literature review (racing telemetry ML papers - see ML_STRATEGY.md references)
- [ ] Evaluate architectures: LSTM, Transformer, Physics-Informed NN, Hybrid
- [ ] Prototype 2-3 approaches in Jupyter notebooks
- [ ] Select winning architecture based on accuracy and latency

**3.3 Train Baseline Model (5-6 weeks)**
- [ ] Supervised learning: telemetry → optimal values (brake point, apex speed, etc.)
- [ ] Anomaly detection: user lap vs. learned expert distribution
- [ ] Output: structured feedback (numeric deltas, anomaly scores)
- [ ] Hyperparameter tuning (learning rate, batch size, model depth)
- [ ] Validation: 90%+ accuracy on held-out laps

**3.4 LLM Integration for Natural Language (2 weeks)**
- [ ] Structured feedback → prompt engineering
- [ ] LLM converts to natural language coaching
- [ ] Test LLM models: GPT-4, Claude, local LLaMA
- [ ] Optimize for latency and cost (cache common patterns)

**3.5 A/B Testing & Evaluation (3 weeks)**
- [ ] Deploy ML coaching alongside rule-based coaching
- [ ] A/B test: 50% of users get ML, 50% get rule-based
- [ ] Metrics: user laptime improvement, subjective quality
- [ ] Surveys: preference between ML vs. rule-based
- [ ] Target: 70%+ prefer ML coaching

**3.6 Production Integration (3 weeks)**
- [ ] ML model serving infrastructure (FastAPI endpoint)
- [ ] Real-time inference: <500ms latency
- [ ] Fallback to rule-based if ML fails
- [ ] Monitoring: accuracy, latency, error rates
- [ ] Logging: track coaching message delivery

#### Deliverable
Functioning ML coaching model for 1 car/track combo (Skip Barber @ Lime Rock). Demonstrably more helpful than rule-based systems via A/B testing.

#### Success Criteria
- [ ] 90%+ model accuracy on held-out test laps
- [ ] 70%+ of beta users prefer ML coaching over rule-based
- [ ] <500ms inference latency (real-time use)
- [ ] Users report 10-20% faster laptime improvement with ML coaching

---

### Milestone 4: ML Scaling & Advanced Features
**Duration**: 20-24 weeks (~10 hrs/week)
**Priority**: MEDIUM (long-term differentiation)
**Goal**: Expand ML to multiple car/track combos, advanced features

#### Tasks

**4.1 Expand to Top 5 Car/Track Combos (6-8 weeks)**
- [ ] Select popular combos: MX-5 @ Lime Rock, GT3 @ Spa, Formula Vee @ Summit Point
- [ ] Collect 1,000+ laps per combo (leverage MVP crowdsourced data)
- [ ] Fine-tune base model for each combo (transfer learning)
- [ ] Validate performance (85%+ accuracy per combo)

**4.2 Hierarchical Model Architecture (6 weeks)**
- [ ] Train generalized base model (learns general racing physics)
- [ ] Fine-tune per car/track combo (specialization)
- [ ] Test generalization to unseen combos
- [ ] Measure performance vs. specialized models

**4.3 Real-Time ML Inference (3 weeks)**
- [ ] Optimize model for low-latency inference (<200ms)
- [ ] Batch inference for live coaching (1 second chunks)
- [ ] Server-side inference initially (client-side future)

**4.4 Advanced Anomaly Detection (4 weeks)**
- [ ] Tire lockup detection
- [ ] Understeer/oversteer detection
- [ ] Track limits violations
- [ ] Inconsistent inputs detection

**4.5 Community Reference Lap Marketplace (3 weeks)**
- [ ] Users can upload/share reference laps publicly
- [ ] Lap ratings and reviews
- [ ] Search/filter by car/track/laptime

#### Deliverable
Production-grade ML coaching across top 5-10 iRacing car/track combinations. Advanced anomaly detection and predictive laptime improvement features. Community-driven reference lap library.

#### Success Criteria
- [ ] ML coaching available for 5+ car/track combos
- [ ] 80%+ users prefer ML coaching over rule-based (sustained)
- [ ] Transfer learning reduces per-combo training time by 50%+
- [ ] Track boundary mapping working for 3+ tracks

---

### Milestone 5: Commercial Launch
**Duration**: 10-14 weeks (~10 hrs/week)
**Priority**: MEDIUM-HIGH (business sustainability)
**Goal**: Launch paid premium tier and marketing push

#### Tasks

**5.1 Pricing Tiers Definition (1-2 weeks)**
- [ ] Free tier: basic coaching (rule-based), limited laps/month
- [ ] Pro tier ($5-8/month): unlimited laps, ML coaching
- [ ] Enterprise tier: team features (future)

**5.2 Payment Integration (3 weeks)**
- [ ] Stripe integration (subscription management)
- [ ] Billing dashboard (view invoices, payment)
- [ ] Feature gating (subscription tier checks)
- [ ] Trial period (7-14 days free Pro)

**5.3 Self-Hosted Documentation (2-3 weeks)**
- [ ] Installation guide (Docker Compose)
- [ ] Configuration guide (env vars, database)
- [ ] Troubleshooting guide
- [ ] Update guide

**5.4 Marketing Website (3-4 weeks)**
- [ ] Landing page (value prop, features, pricing)
- [ ] Documentation site (user guides, tutorials)
- [ ] Blog (updates, racing tips)
- [ ] SEO optimization

**5.5 Community Building (ongoing)**
- [ ] Discord server (support, feedback)
- [ ] Reddit presence (r/iRacing, r/simracing)
- [ ] YouTube demos
- [ ] Partner with influencers

**5.6 Beta User Conversion (1 week)**
- [ ] Email campaign to beta users
- [ ] In-app upgrade prompts
- [ ] Referral program

#### Deliverable
Public commercial launch with free and paid tiers. Marketing website, community channels, and press coverage driving user acquisition.

#### Success Criteria
- [ ] 500+ registered users in first month post-launch
- [ ] 10%+ conversion from free to Pro tier
- [ ] $1,000+ MRR (monthly recurring revenue) in first month
- [ ] 3+ press mentions or reviews

---

## Dependencies & Sequencing

### Critical Path
1. **Milestone 1 (Foundation & Security)** → BLOCKS all other milestones (can't launch without auth)
2. **Milestone 2 (Live Coaching MVP)** → BLOCKS Milestone 5 (ML needs coaching infrastructure)
3. **Milestone 3 (Data Collection)** → BLOCKS Milestone 5 (ML needs training data)
4. **Milestone 5 (ML Prototype)** → BLOCKS Milestone 6 (can't scale ML without prototype validation)

### Parallel Work Opportunities
- **Milestone 3 (Data Collection)** can run in parallel with Milestone 2 (Live Coaching)
- **Milestone 4 (Post-Session Analysis)** can run in parallel with Milestone 5 (ML Prototype)
- **Milestone 7 (Commercial Launch)** prep work can start during Milestone 6

### Recommended Sequencing
1. Milestone 1 (Foundation & Security) - 8-12 weeks
2. Milestone 2 (Live Coaching MVP) + Milestone 3 (Data Collection) in parallel - 6-8 weeks
3. Milestone 4 (Post-Session Analysis) + Milestone 5 (ML Prototype) in parallel - 12-16 weeks
4. Milestone 6 (ML Scaling) - 16-20 weeks
5. Milestone 7 (Commercial Launch) - 8-12 weeks

**Total Timeline**: ~18-24 months for full roadmap completion

---

## Risk Mitigation

### Technical Risks
- **ML models don't improve on rule-based coaching**: Validate with prototype (Milestone 5) before scaling
- **Insufficient training data**: Incentivize telemetry sharing via freemium model, partner with teams
- **iRacing SDK breaking changes**: Abstract telemetry layer, monitor SDK updates
- **Real-time inference latency**: Optimize models, use edge inference, batch processing

### Business Risks
- **Low conversion to paid tier**: Offer compelling premium features (ML coaching), trial period, competitive pricing
- **Competitors react (Trophi.ai, Garage 61 add similar features)**: Open source advantage, research focus, data network effects
- **Insufficient revenue to sustain development**: Accept hobby project outcome, community can continue via open source

### Operational Risks
- **Security breach**: Penetration testing, security audits, responsible disclosure program
- **Data privacy violations**: GDPR compliance, legal review of privacy policy, anonymization pipeline
- **Infrastructure downtime**: Monitoring, alerting, redundancy, disaster recovery plan

---

## Success Metrics Summary

### Short-Term (6 months)
- 100+ registered users
- Live coaching working in production (95%+ uptime)
- 1,000+ clean laps collected
- $0 revenue (free beta)

### Medium-Term (12 months)
- 500+ registered users (50+ paid Pro)
- ML coaching prototype validated (70%+ prefer ML)
- Post-session analysis competitive with Garage 61
- $2,000+ MRR

### Long-Term (24 months)
- 2,000+ users (500+ paid)
- ML coaching across 5+ car/track combos
- Self-hosted deployment active community
- $10,000+ MRR

---

**Last Updated**: December 2025
**Document Owner**: Racing Coach Team
**Status**: Living document, revised quarterly based on progress and priorities
