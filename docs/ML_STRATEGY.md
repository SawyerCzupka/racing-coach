# Racing Coach: Machine Learning Strategy

## Overview

This document outlines the technical approach to building ML-powered coaching capabilities for Racing Coach. The strategy balances pragmatic, achievable techniques with ambitious "AGI-native" research directions. The goal is to create coaching models that demonstrably outperform rule-based systems while maintaining real-time inference latency for live coaching.

---

## Philosophy: "AGI Native" Coaching Models

### Traditional Approach (What Most Competitors Do)
1. Build rule-based coaching system (if X, then Y)
2. Layer simple ML on top (classify lap quality, detect patterns)
3. Use general-purpose LLMs to convert rules to natural language
4. Results: Limited intelligence, doesn't learn nuanced patterns, brittle to edge cases

### AGI-Native Approach (Our Vision)
1. Train end-to-end model with all desired coaching capabilities
2. Model learns from data rather than hand-coded rules
3. Discovers subtle patterns humans might miss
4. Generalizes better to unseen situations
5. Results: More capable, nuanced coaching that improves over time

### Benefits of AGI-Native
- **More capable**: Learns complex, non-linear relationships in telemetry
- **Better generalization**: Applies learned physics to new car/track combos
- **Discovers insights**: May find coaching patterns human experts haven't articulated
- **Improves with data**: Gets smarter as more telemetry is collected
- **Adaptive**: Can personalize to individual driver style and skill level

### Challenges of AGI-Native
- **Data hungry**: Requires thousands of laps per car/track combo
- **Harder to interpret**: Black-box models, difficult to explain why certain coaching is given
- **Longer training**: More complex models take longer to train and tune
- **Inference latency**: Must optimize heavily for real-time use (<500ms)
- **Validation difficulty**: How do we know the model is giving "correct" coaching?

### Pragmatic Hybrid Strategy (Recommended Starting Point)
Start with proven techniques, incrementally add novel approaches:
1. **Phase 1**: Supervised learning on expert laps (learn optimal patterns)
2. **Phase 2**: Anomaly detection on user laps (identify deviations)
3. **Phase 3**: LLM post-processing for natural language coaching
4. **Phase 4**: Explore physics-informed NNs, reinforcement learning, transfer learning

This balances achievability (can deliver v1 quickly) with research ambition (path to AGI-native models).

---

## Data Strategy

### Primary Source: User-Collected Telemetry (MVP Crowdsourcing)

**MVP Strategy: Data Collection is the Goal**:
- MVP's primary purpose: launch public beta to crowdsource telemetry data
- Can't train ML models without data → must collect first
- Timeline: MVP launch → 1,000+ laps collected → begin ML prototyping
- Users opt-in during registration, toggle in settings

**Crowdsourcing via Freemium Exchange**:
- Free or discounted app access in exchange for opt-in telemetry sharing
- Users explicitly consent to data usage for ML training
- Clear value proposition: "Your data helps improve coaching for everyone"
- Success metric: 50%+ of MVP users opt-in to sharing

**Target Data Volume**:
- MVP goal: 1,000+ laps across all combos (trigger for ML work)
- Per-combo minimum: 500+ laps for initial prototype (e.g., Skip Barber @ Lime Rock)
- Per-combo optimal: 10,000+ laps for robust production models
- Distribution: Mix of skill levels (20% expert, 50% intermediate, 30% beginner)

**Data Quality Criteria**:
- Complete laps only (no crashes, disconnects, or pit stops mid-lap)
- All telemetry channels present (~50 fields)
- Reasonable lap times (filter extreme outliers: >5 std deviations from mean)
- Clean racing (no major track limit violations or collisions)

**Collection Strategy**:
- MVP Phase: Collect broadly across all car/track combos users drive
- ML Prototype Phase: Focus on single combo (most popular or most data)
- Scaling Phase: Expand to top 5-10 combos based on data volume
- Continuously collect as user base grows (iterative model improvement)

### Secondary Source: Expert/Reference Laps

**Top iRacing Drivers**:
- Partner with fast drivers to contribute reference laps
- Compensation: free Pro tier, recognition, coaching credit
- Legal: explicit permission to use telemetry for training

**Official iRacing Alien Laps**:
- VRS (Virtual Racing School) telemetry (if partnership possible)
- iRacing Time Trial record laps (if accessible)
- Legal/ethical review required before scraping

**Racing Team Data**:
- Partner with esports teams (e.g., Team Redline, Williams Esports)
- Exchange: free team features for telemetry access
- Bulk data source, high-quality laps

### Tertiary Source: Synthetic Data Augmentation (Future)

**Physics-Based Simulation**:
- Generate synthetic telemetry by simulating car physics
- Vary parameters: tire compound, fuel load, track temp, driver aggression
- Benefits: infinite data, control edge cases, no privacy concerns
- Challenges: Simulator physics must match iRacing closely (difficult!)

**Data Augmentation Techniques**:
- Add noise to real telemetry (simulate sensor variance)
- Time-shift telemetry (slightly earlier/later braking)
- Speed scaling (simulate faster/slower drivers)
- Track condition variation (wet vs. dry, hot vs. cold)

**Current Assessment**: Not pursuing synthetic data for prototype. Focus on real user data first. Revisit if data collection is too slow.

### Privacy & Ethics

**Anonymization Pipeline**:
- Strip all personally identifiable information (username, email, IP, customer ID)
- Assign random anonymous IDs to laps (irreversible mapping)
- Remove any user-submitted comments or metadata
- Aggregate statistics only (no individual driver profiling)

**Consent & Transparency**:
- Opt-in checkbox: "I consent to sharing my telemetry data for ML training"
- Privacy policy clearly explains data usage
- Users can revoke consent anytime (future data not collected, past data already anonymized)
- Self-hosted users keep all data local (never shared)

**Compliance**:
- GDPR (EU): Right to access, right to erasure, data minimization
- CCPA (California): Disclosure of data collection, opt-out mechanism
- Legal review before commercial launch

---

## Model Architecture Research Directions

### Option 1: Sequence-to-Sequence Models (Recommended for Prototype)

**Architecture**:
- **Input**: Telemetry time series (T timesteps, N channels)
  - Channels: speed, throttle, brake, clutch, steering, lat/lon G, yaw rate, lap distance, RPM, gear, etc.
  - Example: 60 Hz × 90 seconds = 5,400 timesteps per lap
- **Output**: Optimal telemetry values + deviation scores per timestep
  - Target brake pressure at T=1000 is 80%, user applied 60% → deviation: -20%
  - Target apex speed at corner X is 120 km/h, user achieved 115 km/h → deviation: -5 km/h
- **Model**: LSTM or Transformer encoder-decoder
  - Encoder: learns representation of telemetry sequence
  - Decoder: predicts optimal values at each timestep
- **Training**: Supervised learning on expert laps (learn what "good" looks like)

**Pros**:
- Well-established architecture (LSTM/Transformers proven for sequence modeling)
- Interpretable outputs (can explain why each coaching message is generated)
- Moderate data requirements (500-1,000 laps sufficient for prototype)
- Fast inference (10-50ms for 5,400-timestep sequence on modern GPU)

**Cons**:
- May not capture complex physics (weight transfer, tire dynamics)
- Requires labeled "optimal" data (assumes expert laps are perfect)
- Less generalizable (trained per car/track combo)

**Implementation Plan**:
1. Preprocess telemetry: normalize channels, segment laps, extract features
2. Train LSTM/Transformer on expert laps (learn optimal patterns)
3. Evaluate on validation set (90%+ accuracy target)
4. Deploy for inference: user lap → model → deviations → coaching messages

### Option 2: Physics-Informed Neural Networks (PINNs)

**Architecture**:
- **Input**: Same as Option 1 (telemetry time series)
- **Physics Constraints**: Incorporate racing physics equations into loss function
  - Tire friction: lateral G ≤ μ × vertical load
  - Weight transfer: longitudinal accel → load shift front/rear
  - Power/torque curves: RPM and throttle → acceleration
  - Aerodynamics: speed² → downforce → grip
- **Output**: Optimal telemetry + physics-based explanations
- **Training**: Hybrid loss = prediction error + physics violation penalty

**Pros**:
- Data-efficient (learns from fewer laps because physics guides learning)
- Better generalization (physics applies to all cars/tracks)
- Interpretable (can explain coaching in terms of physics: "You violated tire friction limit")
- Novel research direction (potential academic publication)

**Cons**:
- Requires deep physics expertise (tire models, suspension dynamics)
- Complex implementation (deriving differentiable physics equations)
- Validation difficulty (how accurate are our physics assumptions?)
- Longer development time (less proven in racing domain)

**Implementation Plan** (Future):
1. Research racing physics literature (tire models, vehicle dynamics)
2. Implement differentiable physics simulator (JAX or PyTorch)
3. Integrate physics constraints into NN loss function
4. Train on smaller dataset (test data-efficiency claim)
5. Compare to Option 1 (does physics help or hurt?)

### Option 3: Reinforcement Learning (RL)

**Architecture**:
- **Agent**: Neural network that controls car (outputs throttle, brake, steering)
- **Environment**: Racing simulator (iRacing SDK or custom physics sim)
- **Reward**: Minimize laptime while staying on track
- **Training**: RL algorithm (PPO, SAC, TD3) learns optimal racing policy

**Pros**:
- Discovers novel techniques (may find faster lines than human experts)
- No labeled data required (learns from trial and error)
- Generalizes well (learns fundamental racing principles)
- Exciting research direction (potential for breakthrough insights)

**Cons**:
- Requires racing simulator integration (complex, may need iRacing API access)
- Extremely long training time (millions of laps in simulation)
- Sample inefficiency (RL notoriously data-hungry)
- Sim-to-real gap (simulated racing may not transfer to iRacing physics)
- Inference is policy execution, not coaching (hard to convert to coaching messages)

**Implementation Plan** (Long-Term Research):
1. Build or integrate racing simulator (iRacing SDK, Assetto Corsa, custom)
2. Implement RL algorithm (PPO, SAC)
3. Train agent on single car/track (expect weeks/months of GPU time)
4. Analyze learned policy (what techniques did it discover?)
5. Convert policy to coaching: "RL agent brakes 5m later than you, try that"

**Current Assessment**: Too ambitious for initial prototype. Interesting long-term research direction but not pragmatic for v1.

### Option 4: Hybrid Approach (Pragmatic Recommendation)

**Combine Best of All Worlds**:
1. **Supervised learning (Seq2Seq)** on expert laps → learn optimal patterns
2. **Anomaly detection** on user laps → identify deviations from expert distribution
3. **LLM post-processing** → convert structured feedback to natural language
4. **(Future) Physics-informed losses** → improve generalization
5. **(Future) RL insights** → discover novel techniques to teach users

**Phase 1: Supervised Learning + Anomaly Detection**
- Train LSTM/Transformer on expert laps (learn optimal telemetry patterns)
- Compute anomaly scores: user lap deviates from learned distribution
- Output structured feedback: {brake_point_delta: -10m, apex_speed_delta: -5 km/h, anomaly_score: 0.7}

**Phase 2: LLM Natural Language Conversion**
- Structured feedback → prompt for LLM:
  - "Brake point is 10 meters late in Turn 3. Apex speed is 5 km/h slow. Anomaly score is 0.7 (high). Generate coaching message."
- LLM output: "You're braking too late into Turn 3, which is causing you to miss the apex. Try braking 10 meters earlier to carry more speed through the corner."
- TTS converts text to audio for live delivery

**Phase 3: Iterative Improvement**
- Collect user feedback on coaching quality
- Retrain models with more data
- Experiment with physics-informed losses (if improvement is measurable)
- Explore RL for discovering novel techniques

**Why This Works**:
- Pragmatic: can deliver v1 quickly with proven techniques
- Ambitious: path to AGI-native models via iterative improvement
- Flexible: can swap components (different LLMs, better anomaly detection)
- Scalable: same architecture works for multiple car/track combos

---

## Prototype Plan: Single Car/Track

### Target: Skip Barber @ Lime Rock Park

**Why This Combo?**
- **Simple**: Short track (~1 minute laps), limited corners (6 turns), forgiving car
- **Popular**: Many iRacers run this combo (easy to collect data)
- **Beginner-friendly**: Low-downforce, slow car (easier to model physics)
- **Iconic**: Classic combo for learning (good marketing story)

### Phase 1: Data Collection (4 weeks)

**Target Data**:
- 500+ total laps (100 expert, 400 varied skill levels)
- Expert laps: 1:05.0 or faster (top 5% of iRacing laptimes)
- Intermediate: 1:06.0-1:08.0 (50% of dataset)
- Beginner: 1:08.0+ (30% of dataset)

**Collection Strategy**:
- Recruit beta users running Skip Barber @ Lime Rock
- Incentivize: free Pro tier for 3 months in exchange for 20+ clean laps
- Manual review: filter crashes, track limit violations, incomplete laps

**Data Processing**:
1. Extract telemetry from database (TimescaleDB hypertable)
2. Normalize channels (z-score normalization per channel)
3. Segment laps (detect lap start/end via lap distance wraparound)
4. Label skill level (based on laptime percentile)
5. Train/val/test split: 80% / 10% / 10%

### Phase 2: Baseline Model Training (4 weeks)

**Model Architecture**:
- **Input**: Telemetry sequence (5,400 timesteps × 20 channels)
  - Channels: speed, throttle, brake, steering, lat G, lon G, yaw rate, lap_dist, RPM, gear, etc.
- **Encoder**: 2-layer bidirectional LSTM (256 hidden units each)
- **Decoder**: 2-layer LSTM (256 hidden units)
- **Output**: Optimal values per channel + confidence scores

**Training Setup**:
- Framework: PyTorch (flexibility) or TensorFlow (production ecosystem)
- Loss: Mean Squared Error (MSE) on expert lap telemetry
- Optimizer: Adam (lr=0.001, decay over epochs)
- Batch size: 32 laps
- Epochs: 50-100 (early stopping on validation loss)
- Hardware: 1x NVIDIA A100 or 4x V100 GPUs (4-8 hours training time)

**Validation**:
- MSE on test set (target: <5% error on critical channels: speed, brake, steering)
- Visual inspection: plot predicted vs. actual telemetry (should be nearly identical)
- Lap time prediction: model's optimal telemetry should yield expert-level laptime

**Anomaly Detection**:
- Train autoencoder on expert laps (learn normal distribution)
- User lap → reconstruction error = anomaly score
- High anomaly score → deviation from optimal technique
- Threshold: anomaly score >0.7 → trigger coaching message

### Phase 3: LLM Integration (2 weeks)

**Structured Feedback Generation**:
- Model outputs: {brake_point_delta: -10m, apex_speed_delta: -5 km/h, line_deviation: 2.3m}
- Convert to structured text:
  ```json
  {
    "corner": "Turn 3",
    "issues": [
      {"type": "braking", "severity": "high", "delta": "-10m", "description": "Braking too late"},
      {"type": "speed", "severity": "medium", "delta": "-5 km/h", "description": "Apex speed slow"}
    ]
  }
  ```

**LLM Prompt Engineering**:
```
You are a professional racing coach. Given the following telemetry analysis for Turn 3:
- Braking point: 10 meters late (high severity)
- Apex speed: 5 km/h slow (medium severity)
- Racing line: 2.3 meters off optimal

Generate a concise, actionable coaching message (1-2 sentences) for the driver.
```

**LLM Output**:
"You're braking too late into Turn 3, which is causing you to miss the apex. Try braking 10 meters earlier to carry more speed through the corner."

**LLM Model Selection**:
- Test: GPT-4, Claude Sonnet, GPT-3.5, Llama 3 70B (local)
- Evaluate: coaching quality (manual review), latency, cost
- Production: likely GPT-4 or Claude (best quality), cache common patterns

**TTS Integration**:
- Convert LLM output to audio via pyttsx3 (local, free) or ElevenLabs (cloud, high quality)
- Optimize for latency (<1 second text-to-audio)

### Phase 4: Evaluation (2 weeks)

**A/B Testing Setup**:
- 50% of beta users: ML coaching (telemetry → model → LLM → TTS)
- 50% of beta users: rule-based coaching (if X > threshold, then Y)
- Blind test: users don't know which coaching they're receiving
- Duration: 2 weeks, 10+ sessions per user

**Quantitative Metrics**:
- Laptime improvement: compare week 1 vs. week 2 laptimes per group
- Consistency: lap-to-lap variance (lower is better)
- Engagement: sessions completed, coaching messages dismissed vs. acknowledged

**Qualitative Metrics**:
- Post-test survey: "Which coaching was more helpful?" (5-point Likert scale)
- Open-ended feedback: "What did you like/dislike about the coaching?"
- Manual review: listen to coaching messages, assess relevance and clarity

**Success Criteria**:
- ML coaching group improves laptimes 20%+ faster than rule-based group
- 70%+ of ML coaching users rate it as "very helpful" or "extremely helpful"
- Coaching message quality (manual review): 90%+ messages are relevant and actionable

### Phase 5: Production Integration (4 weeks)

**ML Model Serving Infrastructure**:
- Deploy model as FastAPI microservice (separate from main server)
- Endpoint: `POST /api/v1/ml/score-lap` (input: telemetry JSON, output: structured feedback)
- Model caching: keep model in memory (avoid loading overhead)
- Batching: process multiple laps in parallel (if traffic scales)

**Inference Optimization**:
- Quantization: reduce model precision (FP32 → FP16 or INT8) for faster inference
- ONNX export: convert PyTorch/TF model to ONNX for optimized runtime
- GPU inference: deploy on GPU instance (AWS P3, GCP T4) for <100ms latency
- Fallback: if ML inference fails, fall back to rule-based coaching (robustness)

**Monitoring & Logging**:
- Track inference latency (P50, P95, P99)
- Log model predictions and user feedback (continuous improvement loop)
- Alert on high error rates or latency spikes
- A/B test dashboard (real-time comparison of ML vs. rule-based)

**Deployment Strategy**:
- Blue-green deployment: deploy new model version without downtime
- Gradual rollout: 10% → 50% → 100% of users (monitor for regressions)
- Rollback plan: keep previous model version ready (instant rollback if issues)

---

## Scaling Strategy

### Short-Term (6-12 months): Expand to 5-10 Combos

**Target Combos** (prioritize by popularity):
1. Skip Barber @ Lime Rock Park (prototype)
2. Mazda MX-5 @ Lime Rock Park (different car, same track)
3. Skip Barber @ Summit Point (same car, different track)
4. Formula Vee @ Lime Rock Park (higher performance car)
5. GT3 @ Spa-Francorchamps (high-downforce, complex track)

**Fine-Tuning Strategy**:
- Start with base model trained on Skip Barber @ Lime Rock
- Fine-tune on new combo (transfer learning: only retrain final layers)
- Requires 200-500 laps per new combo (vs. 500+ for training from scratch)
- Reduces training time by 50-70% (2-4 hours vs. 8+ hours)

**Evaluation**:
- Test each combo independently (90%+ accuracy target)
- Cross-combo validation: does Lime Rock model help at Summit Point? (measure generalization)

### Medium-Term (1-2 years): Generalized Model

**Multi-Task Learning**:
- Train single model on all car/track combos simultaneously
- Model learns general racing physics (braking, cornering, weight transfer)
- Task-specific heads: final layers specialize per combo
- Benefits: better generalization, faster adaptation to new combos

**Transfer Learning for New Combos**:
- Generalized base model + fine-tuning on 100-200 laps of new combo
- Should achieve 85%+ accuracy with minimal data (vs. 90%+ with full dataset)
- Enables rapid expansion to long-tail combos (less popular)

**Hierarchical Architecture**:
- Layer 1: General racing physics (shared across all combos)
- Layer 2: Car-specific (low-downforce vs. high-downforce)
- Layer 3: Track-specific (fast corners vs. slow corners)
- Benefits: interpretable, efficient, modular

### Long-Term (2-3 years): Advanced Techniques

**Physics-Informed Neural Networks (PINNs)**:
- Integrate racing physics equations into model architecture
- Model learns residuals: physics model + learned corrections
- Benefits: extreme data efficiency, explains coaching in physics terms
- Research risk: may not improve on pure data-driven approach

**Real-Time Adaptive Coaching**:
- Model adapts to individual driver's skill level over time
- Beginner: focus on fundamentals (braking points, racing line)
- Advanced: focus on marginal gains (trail braking, throttle modulation)
- Personalization: learn driver's weaknesses, prioritize coaching accordingly

**Predictive Coaching**:
- Model anticipates mistakes before they happen
- Example: "Your entry speed is too high, you'll understeer at apex"
- Delivered 1-2 seconds before the issue occurs (proactive, not reactive)
- Requires prediction horizon: model forecasts future telemetry

**Reinforcement Learning Insights**:
- Train RL agent to discover novel racing techniques
- Analyze learned policy: what does agent do differently than humans?
- Convert insights to coaching: "RL agent found a faster line through Turn 3"
- High-risk, high-reward: may discover nothing new, or may revolutionize coaching

---

## Related Research

Recent academic work demonstrates the viability of ML approaches for racing telemetry analysis and coaching:

### AI-Enabled Sim Racing Performance Prediction (2024)

**Study**: "[AI-enabled prediction of sim racing performance using telemetry data](https://www.sciencedirect.com/science/article/pii/S2451958824000472)"

**Key Findings**:
- Analyzed 174 participants completing 1327 laps on Brands-Hatch (Assetto Corsa Competizione)
- Identified key performance metrics: speed, lateral acceleration, steering angle, lane deviation
- ML models successfully classified driver skill levels from telemetry
- Narrowed 84 telemetry channels down to 46 critical channels for analysis

**Relevance to Racing Coach**: Validates that ML can extract meaningful performance insights from sim racing telemetry. Confirms our focus on key channels (speed, inputs, G-forces) is well-founded.

### AI Approach for Analyzing Driving Behaviour (2023)

**Study**: "[An AI Approach for Analyzing Driving Behaviour in Simulated Racing](https://www.researchgate.net/publication/376031773)"

**Key Findings**:
- ML algorithms successfully classify laps into performance levels
- Evaluate driving behaviors and create prediction models
- Highlight features with significant impact on driver performance
- Demonstrates that elite drivers differ from low-skilled drivers in measurable ways

**Relevance to Racing Coach**: Supports our anomaly detection approach - ML can learn what "expert" driving looks like and identify deviations in user laps.

### Formula RL: Deep Reinforcement Learning (2021)

**Study**: "[Formula RL: Deep Reinforcement Learning for Autonomous Racing](https://arxiv.org/abs/2104.11106)"

**Key Findings**:
- RL agents can learn racing from raw telemetry without explicit rules
- Demonstrates potential for discovering novel racing techniques
- Highlights sim-to-real challenges

**Relevance to Racing Coach**: Long-term research direction. While too ambitious for initial prototype, RL could discover optimal techniques that human experts haven't articulated.

### Key Takeaways for Racing Coach

1. **Validated Approach**: Multiple studies confirm ML can learn from racing telemetry
2. **Channel Selection**: 46-50 key channels are sufficient (we're already collecting ~50)
3. **Skill Classification**: ML can distinguish expert from beginner laps (supports our labeling strategy)
4. **Performance Prediction**: Models can predict lap quality and identify improvement opportunities
5. **Research Gap**: No existing work on real-time ML coaching for sim racing (our opportunity!)

---

## Open Questions & Research Directions

### 1. Track Geometry Without Explicit Boundary Data

**Problem**: iRacing provides GPS (lat/lon/alt) but no track boundaries. Difficult to determine corner entry/apex/exit precisely.

**Potential Solutions**:
- **Crowdsourced mapping**: users drive track edges, app records GPS coordinates
- **ML-based inference**: model learns track boundaries from racing line patterns
- **Computer vision**: extract boundaries from replay video (ambitious)
- **Reverse engineering**: decode Garage 61 binary track files (legal/ethical concerns)

**Research Question**: Can ML model learn corner phases without explicit boundaries? (use lateral G, steering angle as proxy)

### 2. General Racing Physics vs. Specialized Models

**Question**: Is it better to train one generalized model (all cars/tracks) or specialized models per combo?

**Hypothesis**: Generalized model is more data-efficient but less accurate per combo. Specialized models are more accurate but don't scale.

**Experiment**: Train both, compare accuracy and generalization. May find hybrid is best (general base + fine-tuned heads).

### 3. Model Complexity vs. Data Requirements

**Trade-off**: Complex models (large Transformers) learn better patterns but require more data. Simple models (small LSTMs) train on less data but may underfit.

**Research Question**: What's the optimal model size for 500 laps? 1,000 laps? 10,000 laps?

**Experiment**: Train models of varying sizes (1M, 10M, 100M parameters), plot accuracy vs. data volume.

### 4. Ground Truth for "Correct" Coaching

**Problem**: How do we validate that coaching is correct? Expert laps aren't perfect (drivers make mistakes). Fastest lap isn't always best technique.

**Potential Solutions**:
- Human expert review (manual validation, expensive)
- User feedback loop (thumbs up/down on coaching messages)
- Laptime improvement (does coaching actually help users improve?)
- Consistency with physics (does coaching violate racing principles?)

**Research Question**: Can we define a "correctness" metric for coaching beyond laptime?

### 5. Real-Time Inference Constraints

**Challenge**: Live coaching requires <200ms end-to-end latency (telemetry → ML → LLM → TTS). Large models are slow.

**Optimization Strategies**:
- Model quantization (FP16, INT8)
- Edge inference (run model on client device)
- Batch telemetry (process 1 second at a time, not per-frame)
- LLM caching (pre-generate common coaching messages)

**Research Question**: Can we achieve <200ms latency with high-quality models, or must we sacrifice accuracy for speed?

### 6. Sim Physics Updates (iRacing Tire Model Changes)

**Problem**: iRacing updates physics periodically (new tire model, aero changes). Does this invalidate trained models?

**Mitigation**:
- Collect telemetry per physics version (track which version data came from)
- Retrain models when physics changes (or fine-tune on new physics)
- Test model robustness: does Skip Barber model work across tire model versions?

**Research Question**: How sensitive are ML models to sim physics changes? Can we make them robust?

---

## Implementation Priorities

### Immediate (Milestone 5: ML Prototype)
1. Data collection: 500+ laps for Skip Barber @ Lime Rock
2. Train seq2seq model (LSTM/Transformer)
3. Integrate LLM for natural language coaching
4. A/B test: ML vs. rule-based coaching
5. Deploy production inference endpoint

### Near-Term (Milestone 6: ML Scaling)
1. Expand to 5 car/track combos
2. Implement transfer learning (fine-tuning)
3. Hierarchical model architecture (general + specialized)
4. Advanced anomaly detection (lockup, understeer, track limits)

### Long-Term (Research Directions)
1. Physics-informed neural networks (PINNs)
2. Reinforcement learning agent (discover novel techniques)
3. Real-time adaptive coaching (personalization)
4. Predictive coaching (anticipate mistakes)
5. Academic publications on novel ML techniques

---

## Success Criteria

### Prototype (Single Car/Track)
- [ ] 90%+ model accuracy on held-out test laps
- [ ] 70%+ users prefer ML coaching over rule-based
- [ ] <500ms inference latency (real-time use)
- [ ] Users improve laptimes 20%+ faster with ML coaching

### Production (5+ Car/Track Combos)
- [ ] 85%+ accuracy per combo (slightly lower OK if generalization is better)
- [ ] Transfer learning reduces training time by 50%+
- [ ] ML coaching available to all Pro tier users
- [ ] 1,000+ users actively using ML coaching

### Research Impact
- [ ] Novel ML technique published at top conference (NeurIPS, ICML, ICLR)
- [ ] Open-source dataset and models for racing research community
- [ ] Demonstrable improvement over existing sim racing coaching tools
- [ ] Potential applications beyond sim racing (real motorsports, autonomous vehicles)

---

**Last Updated**: December 2025
**Document Owner**: Racing Coach ML Team
**Status**: Living document, updated as research progresses
