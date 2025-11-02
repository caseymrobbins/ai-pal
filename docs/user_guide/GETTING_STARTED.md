# AI-PAL Getting Started Guide

Welcome to AI-PAL (AI-Powered Agency & Learning), a production-ready cognitive partner designed to enhance your capabilities while ensuring you retain and grow your agency.

## What is AI-PAL?

AI-PAL is a unique AI system built on the principle of **Agency Retention** - it helps you accomplish tasks while ensuring you become more capable, not less. Unlike traditional AI assistants that can lead to skill atrophy, AI-PAL:

- 📈 **Tracks your skill development** through the Autonomy Retention Index (ARI)
- 🎯 **Scaffolds your growth** with the Fractal Flow Engine (FFE)
- 🛡️ **Monitors AI quality** through Epistemic Debt Management (EDM)
- 🚦 **Enforces ethical boundaries** via the 4-Gate System
- 🗳️ **Empowers users** through the AHO Tribunal appeal process
- 🤝 **Privacy-first social features** for sharing wins and mutual support
- 🧠 **Personality-aware task framing** using your signature strengths

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/caseymrobbins/ai-pal.git
cd ai-pal

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialize data directory
mkdir -p ~/.ai-pal/data

# Set up your API keys (optional - local mode works without)
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

### Your First Command

The easiest way to use AI-PAL is through the CLI:

```bash
# Check system status
ai-pal status

# Output:
# ✓ AI-PAL System Status
#
#   Core System:
#     Gates: ✓ Operational
#     ARI Monitor: ✓ Operational (0 snapshots)
#     EDM Monitor: ✓ Operational (0 debts)
#     FFE Engine: ✓ Operational
#
#   Priority 3 Features:
#     Social Features: ✓ Enabled
#     Personality Discovery: ✓ Enabled
#     Teaching Mode: ✓ Enabled
```

### Discover Your Personality

AI-PAL can discover your unique signature strengths to better frame tasks:

```bash
ai-pal personality discover

# Interactive assessment with 10 questions
# Discovers your strengths across 8 dimensions:
# - Analytical, Creative, Social, Practical
# - Strategic, Empathetic, Resilient, Curious
```

### Start Your First Goal

```bash
ai-pal start "Learn Python web development"

# FFE will:
# 1. Ingest and estimate the goal's value
# 2. Use 80/20 scoping to find high-impact tasks
# 3. Create 5 atomic blocks (15-90 minutes each)
# 4. Reframe tasks using your signature strengths
# 5. Track momentum and provide rewards
```

### Complete a Task

```bash
ai-pal complete "Finished Flask tutorial chapter 1"

# Celebrates your win and updates progress tapestry
# Updates agency metrics based on your growth
```

## Understanding the Response

When you use AI-PAL, you don't just get answers - you get comprehensive feedback about your agency development:

### CLI Output Example

```bash
ai-pal ari

# Output:
# ✓ Agency Metrics for default_user
#
#   Current ARI Score: 0.85 (Excellent)
#
#   Dimensions:
#     Decision Quality:      0.90 ███████████████████░
#     Skill Development:     0.85 █████████████████░░░
#     AI Reliance:           0.80 ████████████████░░░░
#     Bottleneck Resolution: 0.82 ████████████████░░░░
#     Confidence:            0.88 █████████████████░░░
#     Engagement:            0.87 █████████████████░░░
#     Autonomy Perception:   0.83 ████████████████░░░░
#
#   Status: ✓ Healthy autonomy levels
```

### API Response Example

When using the Python API or REST API:

```json
{
  "model_response": "Let me guide you through implementing Flask authentication...",
  "metadata": {
    "ari_snapshot": {
      "decision_quality": 0.90,
      "skill_development": 0.85,
      "ai_reliance": 0.80,
      "bottleneck_resolution": 0.82,
      "user_confidence": 0.88,
      "engagement": 0.87,
      "autonomy_perception": 0.83,
      "autonomy_retention": 0.85
    },
    "epistemic_debts": [],
    "gate_results": {
      "gate_1_passed": true,
      "gate_2_passed": true,
      "gate_3_passed": true,
      "gate_4_passed": true
    }
  }
}
```

## Core Concepts

### 1. Autonomy Retention Index (ARI)

ARI tracks whether AI assistance is helping or hindering your capability development across **7 dimensions**:

1. **Decision Quality** (0-1): How well you make decisions
2. **Skill Development** (0-1): Are you learning or depending?
3. **AI Reliance** (0-1): Healthy use vs. unhealthy dependency
4. **Bottleneck Resolution** (0-1): Can you solve problems independently?
5. **User Confidence** (0-1): Do you feel capable?
6. **Engagement** (0-1): Are you actively participating?
7. **Autonomy Perception** (0-1): Do you feel in control?

**ARI Score** = Average of 7 dimensions

- **0.9-1.0**: Excellent - High autonomy
- **0.7-0.9**: Good - Healthy use
- **0.5-0.7**: Warning - Approaching dependency
- **< 0.5**: Critical - Agency floor breached (system pauses)

**Goal**: Keep ARI above 0.7 and trending upward.

### 2. Fractal Flow Engine (FFE)

FFE helps you build momentum and achieve goals through:

- **Goal Ingestion**: Natural language → structured goals with value estimation
- **80/20 Scoping**: AI-powered identification of high-impact tasks (20% that yields 80% value)
- **5-Block Stop Rule**: Breaks work into manageable 15-90 minute atomic blocks
- **Signature Strength Amplifier**: Reframes tasks to match your unique strengths
- **Momentum Loop**: State machine (planning → working → review → celebrate)
- **Growth Scaffold**: Detects bottlenecks and provides targeted scaffolding
- **Reward Emitter**: Celebrates wins with personalized pride language
- **Progress Tapestry**: Visual win tracking with narrative connections
- **Epic Meaning Module**: Connects daily wins to long-term aspirations

### 3. Epistemic Debt Management (EDM)

EDM monitors the quality of AI-generated content in real-time:

- **Unfalsifiable Claims**: Statements that can't be proven wrong
- **Unverified Assertions**: Claims without evidence
- **Vague Claims**: Imprecise or ambiguous statements
- **Severity Scoring**: Low, medium, high, critical
- **Debt Resolution**: Track when debts are resolved

**Goal**: Keep epistemic debt low for reliable, actionable information.

### 4. The 4-Gate System

Every significant AI interaction passes through four ethical gates:

1. **Gate 1 - Net Agency Test**: Does this enhance your capability? (ΔAgency ≥ 0)
2. **Gate 2 - Extraction Analysis**: Are there dark patterns, lock-ins, or coercion?
3. **Gate 3 - Humanity Override**: Can you stop or modify this? (Real appeals process)
4. **Gate 4 - Performance Parity**: Is the system fast and non-discriminatory?

If any gate fails, the interaction is blocked or flagged for review through the **AHO Tribunal**.

### 5. Priority 3 Features

**Social Relatedness** (Privacy-First):
- Create and join user-defined groups
- Share wins (user-initiated only, never automatic)
- Encourage others' achievements
- No vanity metrics, no FOMO mechanics
- Granular privacy controls

**Advanced Personality Profiling**:
- Interactive strength discovery (8 types)
- Dynamic updates from behavioral observation
- Evidence-based confidence scoring
- Automatic strength refinement over time

**Learn-by-Teaching Mode**:
- Explain concepts to a "student AI"
- AI generates clarifying questions
- Teaching quality scoring
- Explanation evaluation and feedback

**Curiosity Compass**:
- Transform bottlenecks into exploration opportunities
- 15-minute exploration blocks
- Discovery tracking and celebration

## Common Use Cases

### 1. Learning New Skills

```bash
# Define a learning goal
ai-pal start "Master React hooks and state management"

# FFE creates a 5-block learning path:
# Block 1 (30 min): Understand useState basics
# Block 2 (45 min): Build simple counter component
# Block 3 (60 min): Learn useEffect for side effects
# Block 4 (45 min): Implement custom hooks
# Block 5 (30 min): Refactor existing code to use hooks

# Work on each block and celebrate completion
ai-pal complete "Built working counter with useState!"
```

### 2. Building Projects

```bash
# Start a project goal
ai-pal start "Build a todo app with authentication"

# FFE uses 80/20 scoping to identify high-value tasks:
# - Focus on core CRUD operations first (80% of value)
# - Add authentication second
# - Polish UI last

# Work in focused blocks
# Momentum Loop keeps you in flow state
```

### 3. Social Learning

```bash
# Create a support group
ai-pal social create-group "Web Dev Learners" \
  --description "Support group for learning web development"

# Share a win with your group
# (This is done through the API or when prompted by the CLI)

# View your groups
ai-pal social groups
```

### 4. Learn by Teaching

```bash
# Start a teaching session
ai-pal teach start "Explain how HTTP requests work"

# Student AI asks questions:
# "What's the difference between GET and POST?"
# "How does the client know the request succeeded?"
# "What happens if the server is down?"

# Your explanations are evaluated for:
# - Accuracy
# - Clarity
# - Completeness
# - Teaching effectiveness
```

## Using the Python API

For programmatic access:

```python
from ai_pal.core.integrated_system import IntegratedACSystem
from ai_pal.core.config import SystemConfig

# Initialize the system
config = SystemConfig(
    enable_social_features=True,
    enable_personality_discovery=True,
    enable_teaching_mode=True
)
system = IntegratedACSystem(config)

# Process a request
result = await system.process_request(
    user_id="user-123",
    message="Help me understand binary search",
    context={}
)

print(f"Response: {result['response']}")
print(f"ARI Score: {result['ari_snapshot']['autonomy_retention']}")

# Start an FFE goal
goal = await system.ffe_engine.goal_ingestor.ingest_goal(
    user_id="user-123",
    description="Learn data structures",
    importance=8
)

# Get 5-block plan
plan = await system.ffe_engine.create_5_block_plan(
    user_id="user-123",
    goal_id=goal.goal_id
)

for block in plan.blocks:
    print(f"Block {block.block_index}: {block.description}")
```

## Using the REST API

AI-PAL provides a comprehensive REST API with 23 endpoints:

```bash
# Start API server
uvicorn ai_pal.api.main:app --reload

# Health check
curl http://localhost:8000/health

# Create a goal
curl -X POST http://localhost:8000/api/ffe/goals \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "description": "Learn machine learning",
    "importance": 8
  }'

# Start personality discovery
curl -X POST http://localhost:8000/api/personality/discover/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# View API documentation
open http://localhost:8000/docs
```

## Monitoring Your Progress

### View Your Agency Metrics

```bash
# Current ARI score across all dimensions
ai-pal ari

# System status with recent activity
ai-pal status
```

### Check Your Strengths

```bash
# View discovered signature strengths
ai-pal personality show

# Output shows your top strengths:
# - Analytical: 0.85
# - Creative: 0.75
# - Strategic: 0.80
# (etc.)
```

### Review Your Social Activity

```bash
# View your groups
ai-pal social groups

# See shared wins and encouragements
# (Through API or web interface)
```

## Appealing AI Decisions

If you disagree with an AI decision, you can submit an appeal through the **AHO Tribunal**:

```python
from ai_pal.gates.enhanced_tribunal import EnhancedTribunal, Appeal, AppealPriority

tribunal = EnhancedTribunal()

# Submit an appeal
appeal = await tribunal.submit_appeal(
    Appeal(
        appeal_id="appeal-001",
        user_id="your-user-id",
        action_id="blocked-action-123",
        ai_decision="Gate 1 blocked: potential deskilling risk",
        user_complaint="I believe this would help me learn the concept faster",
        priority=AppealPriority.HIGH
    )
)

# Appeals are reviewed by 7 stakeholder roles:
# - User advocate, Developer, Ethics board, Domain expert,
#   Community rep, Ops/Support, Product owner
#
# Decision timeline:
# - Critical: 6 hours
# - High: 1 day
# - Medium: 3 days
# - Low: 7 days
```

## Best Practices

### 1. Set Learning Goals, Not Output Goals

```bash
# ❌ Bad: "Build me a REST API"
# ✅ Good: "Help me learn to build a REST API"

ai-pal start "Learn to build RESTful APIs with Flask"
```

### 2. Review Your ARI Weekly

```bash
# Check your agency trends
ai-pal ari

# If trending downward:
# - Work more independently
# - Use AI for guidance, not answers
# - Focus on understanding, not just completion
```

### 3. Verify High-Stakes Information

```bash
# For critical decisions, always verify AI responses
# Check epistemic debts through the API:
debts = system.edm_monitor.get_recent_debts(user_id="user", days=1)

high_risk = [d for d in debts if d.severity in ["high", "critical"]]
if high_risk:
    print("⚠️ Verify this information with authoritative sources")
```

### 4. Use FFE for Complex Projects

```bash
# Break large goals into manageable pieces
ai-pal start "Build and deploy a full-stack application"

# FFE automatically:
# 1. Scopes the goal (80/20 analysis)
# 2. Creates 5 atomic blocks
# 3. Tracks momentum
# 4. Celebrates wins
# 5. Identifies bottlenecks
```

### 5. Leverage Social Features for Support

```bash
# Create accountability groups
ai-pal social create-group "100 Days of Code" \
  --description "Daily coding accountability"

# Share wins to build momentum
# Encourage others to create positive culture
```

## Configuration

### CLI Configuration

The CLI uses the system's default configuration. To customize:

```python
# Edit ~/.ai-pal/config.json (if it exists)
# Or set environment variables:
export ANTHROPIC_API_KEY="sk-ant-..."
export ENABLE_SOCIAL_FEATURES=true
export ENABLE_PERSONALITY_DISCOVERY=true
```

### Python API Configuration

```python
from ai_pal.core.config import SystemConfig

config = SystemConfig(
    # Phase 1: Gates
    enable_gates=True,
    enable_tribunal=True,

    # Phase 2: Monitoring
    enable_ari=True,
    enable_edm=True,
    enable_self_improvement=True,

    # Phase 3: Advanced
    enable_privacy=True,
    enable_context=True,
    enable_orchestration=True,
    enable_dashboard=True,

    # Phase 5: FFE
    enable_ffe=True,

    # Priority 3: Advanced Features
    enable_social_features=True,
    enable_personality_discovery=True,
    enable_teaching_mode=True,

    # Model preferences
    default_model_provider="anthropic",  # or "openai", "local"
    optimization_strategy="balanced",     # or "speed", "cost", "quality"

    # Privacy
    data_dir=Path.home() / ".ai-pal" / "data",
    max_context_tokens=4096,
    history_retention_days=90
)

system = IntegratedACSystem(config)
```

## Troubleshooting

### "Gate 1 blocked my request"

Your request was flagged as potentially deskilling. Try:

1. **Rephrase to emphasize learning**: "Help me understand how to..." instead of "Do this for me..."
2. **Request scaffolding**: "Guide me through the steps..." instead of "Give me the answer..."
3. **Submit an appeal** if you believe it's a false positive (appeals are free and reviewed by humans)

### "High epistemic debt detected"

The AI's response contains questionable claims. Actions:

1. **Review the debts**: Check which claims are flagged
2. **Verify with authoritative sources**: Don't trust high-severity debts
3. **Ask for evidence**: Request citations or supporting data
4. **Report patterns**: If certain topics always have high debt, report to developers

### "Agency score declining"

Your autonomy is decreasing. To recover:

1. **Work independently first**: Try solving problems before asking AI
2. **Implement solutions yourself**: Use AI for guidance, not implementation
3. **Review learning paths**: Check FFE goals for skill development opportunities
4. **Take breaks from AI**: Build confidence through independent work

### CLI not found

```bash
# Ensure package is installed in editable mode
pip install -e .

# Check installation
which ai-pal

# If not found, add to PATH:
export PATH="$PATH:$HOME/.local/bin"
```

## Next Steps

- **[FFE User Manual](FFE_USER_MANUAL.md)**: Detailed guide to the Fractal Flow Engine
- **[Architecture Guide](../developer/ARCHITECTURE.md)**: System design and components
- **[API Reference](../developer/API_REFERENCE.md)**: Complete API documentation
- **[Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md)**: Production deployment

## Support

- **Documentation**: [docs/](../)
- **GitHub Issues**: [github.com/caseymrobbins/ai-pal/issues](https://github.com/caseymrobbins/ai-pal/issues)
- **GitHub Discussions**: [github.com/caseymrobbins/ai-pal/discussions](https://github.com/caseymrobbins/ai-pal/discussions)

---

**Remember**: AI-PAL's goal is to make you more capable, not more dependent. Use it as a partner in growth, not a replacement for thinking.

*"The best AI is the one that makes itself less necessary over time."*
