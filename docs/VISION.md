# Racing Coach: Vision Document

## Mission

Transform sim racing coaching from expensive proprietary tools into an accessible, AI-powered, open-source platform that democratizes elite racing analysis for competitive iRacing drivers. Build novel ML/AI coaching capabilities that learn optimal racing technique from data and deliver real-time, personalized feedback that measurably improves driver performance.

## Target Audience

**Primary**: Competitive iRacing drivers seeking laptime improvements
- Skill level: Intermediate to advanced (assumes racing fundamentals understood)
- Goals: Shave tenths/seconds off laptimes, identify specific weaknesses, master new car/track combinations
- Willingness: Ready to analyze data and iterate on technique

**Secondary**: Racing teams and leagues needing telemetry analysis tools
- Team coaches wanting data-driven feedback for drivers
- League organizers seeking competitive analysis tools
- Esports teams training drivers systematically

## Market Position & Competitive Differentiation

### vs. iRacing + Cosworth Pi Toolbox (Free/£5+ per month)

**Cosworth Strengths**: Professional telemetry software used by IndyCar/WEC teams, free for all iRacing users (350,000+), advanced features from £5/month, live remote telemetry support

**Impact on Racing Coach**: Basic telemetry visualization is no longer a differentiator. Users already have professional-grade post-session analysis for free.

**Our Positioning**: AI/ML coaching is THE differentiator. Focus on real-time intelligent feedback, not telemetry visualization.

### vs. Trophi.ai (Tiered Pricing)

**Trophi.ai Strengths**: Real-time voice coaching, multi-lap analysis, track acclimatization, established user base, supports multiple sims (iRacing, F1, ACC, Le Mans Ultimate)

**Our Differentiators**:
- **Open source**: Self-hosted option for privacy-conscious users who want data ownership
- **Novel ML**: AGI-native coaching models that learn from data (not just rule-based comparison systems)
- **Research-driven**: Continuous innovation in ML techniques, potential academic contributions
- **Data network effects**: Community-driven training data improves models over time

### vs. Garage 61

**Note**: With Cosworth Pi Toolbox now free to all iRacing users, Garage 61's market position has changed significantly. Basic telemetry analysis is commoditized.

**Our Positioning**: Don't compete on telemetry visualization (Cosworth does this). Compete on intelligent AI coaching that learns from data.

### Key Strategic Differentiators

1. **AI/ML Coaching** (PRIMARY): Intelligent feedback that learns from data, not just rule-based comparisons
2. **Open Source + Self-Hosted**: Privacy, data ownership, no vendor lock-in
3. **Data Network Effects**: More users → more training data → better coaching models
4. **Research Innovation**: Novel ML techniques, potential academic contributions
5. **Freemium Model**: Core coaching free, advanced ML behind paywall

## Product Evolution

### Phase 1: MVP - Live Coaching Foundation
Drivers receive real-time voice coaching during iRacing sessions. Simple auth, rule-based feedback comparing current lap to reference lap via TTS. Goal: Launch public beta to crowdsource telemetry data for future ML training.

### Phase 2: ML-Powered Coaching (Core Innovation)
Train ML models on crowdsourced telemetry data. Intelligent coaching that learns optimal racing technique from expert laps, identifies performance anomalies, generates nuanced feedback beyond simple comparisons. Start with single car/track combo, validate superiority over rule-based approach.

**ML "AGI Native" Philosophy**: Train models end-to-end with all coaching capabilities. Don't build complex logic atop less-capable models. Balance proven techniques (supervised learning, anomaly detection) with novel research (physics-informed NNs, RL).

**Pipeline**: Telemetry → ML Model → Structured Feedback → LLM → Natural Language → TTS → Audio

### Phase 3: Advanced ML & Scale
Expand to top 10+ car/track combinations. Hierarchical models (general physics base + specialized fine-tuning). Real-time ML inference (<500ms), predictive coaching, advanced anomaly detection. Community reference lap marketplace.

### Phase 4: Commercial Maturity
Production-grade infrastructure, premium tiers (Free/Pro/Enterprise), team features, mobile app, esports integration. Sustainable revenue, active community, recognized as leading FOSS sim racing coaching platform.

## Technical Challenges

**Track Boundary Positioning**: iRacing provides GPS but no track boundaries. MVP uses steering/G-force heuristics to approximate corner zones. Long-term: crowdsourced mapping or reverse engineering.

**ML Model Generalization**: Start with specialized models per car/track combo (pragmatic, less data). Long-term: hierarchical models with general physics base + specialized fine-tuning.

## Success Milestones

**Year 1 (2025-2026)**: 100+ users, basic live coaching working, 1,000+ laps collected, initial ML prototype validated

**Year 2 (2026-2027)**: 1,000+ users (500+ paid), ML coaching demonstrably superior to rule-based, $5-10K MRR

**Year 3 (2027-2028)**: 5,000+ users, top 10 car/track combos covered, novel ML techniques published, $25K+ MRR

## What Success Looks Like

**Product**: Drivers choose Racing Coach for superior ML coaching insights (not just telemetry viz), data ownership (self-hosted), and measurable laptime improvements

**Technical**: 70%+ prefer ML coaching over rule-based, users improve 10-20% faster than unassisted, <500ms inference latency

**Business**: 40-50% free-to-paid conversion, $5-8/month pricing, sustainable revenue, self-hosted community growth

**Research**: Academic publications on racing ML, open datasets/models, conference recognition, applications beyond sim racing

**Community**: Active telemetry crowdsourcing, community reference laps, open-source contributions, racing team adoption

## Risks & Mitigation

**Insufficient Training Data**: Freemium exchange for telemetry, partner with racing teams, synthetic augmentation (future)

**Competitor Reaction**: Open source advantage, research focus on novel ML, data network effects

**iRacing SDK Changes**: Abstract telemetry layer, active monitoring, community fixes

**ML Generalization**: Accept specialized models as pragmatic, focus on popular combos, transfer learning

**Commercial Model Fails**: Acceptable! Open source ensures community continuation, self-hosted option maintains user access

## Conclusion

Racing Coach aims to become the leading open-source, AI-powered sim racing coaching platform by combining:
1. **Accessibility**: Freemium pricing and self-hosted option vs. expensive proprietary tools
2. **Intelligence**: Novel ML coaching models that learn from data, not just rule-based systems
3. **Community**: Open source ecosystem with network effects (more users → better models)
4. **Research**: Continuous innovation in ML techniques, pushing boundaries of sports coaching AI

Success means competitive iRacing drivers measurably improve faster with Racing Coach than with existing tools, while building a sustainable business and contributing novel ML research to the broader community.

---

**Last Updated**: December 2025
**Document Owner**: Racing Coach Team
**Status**: Living document, updated as product evolves
