# AI-PAL Getting Started Guide

Welcome to AI-PAL (AI-Powered Agency & Learning), an AI cognitive partner designed to enhance your capabilities while ensuring you retain and grow your agency.

## What is AI-PAL?

AI-PAL is a unique AI system built on the principle of **Agency Retention** - it helps you accomplish tasks while ensuring you become more capable, not less. Unlike traditional AI assistants that can lead to skill atrophy, AI-PAL:

- 📈 **Tracks your skill development** through the Agency Retention Index (ARI)
- 🎯 **Scaffolds your growth** with the Fractal Flow Engine (FFE)
- 🛡️ **Monitors AI quality** through Epistemic Debt Management (EDM)
- 🚦 **Enforces ethical boundaries** via the 4-Gate System
- 🗳️ **Empowers users** through the AHO Tribunal appeal process

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ai-pal.git
cd ai-pal

# Install dependencies
pip install -e .

# Set up your API keys (optional - for cloud models)
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

### Your First Request

```python
from ai_pal.core.integrated_system import IntegratedACSystem, ACConfig

# Initialize the system
config = ACConfig()
system = IntegratedACSystem(config=config)

# Process a request
result = await system.process_request(
    user_id="your-user-id",
    query="Help me learn how to implement binary search",
    session_id="session-1"
)

print(f"Response: {result.model_response}")
print(f"Agency Score: {result.metadata['ari_snapshot'].autonomy_retention}")
```

### Understanding the Response

AI-PAL doesn't just give you answers - it provides a comprehensive response with metadata:

```python
{
    "model_response": "Let me guide you through binary search...",
    "metadata": {
        "ari_snapshot": {
            "delta_agency": 0.15,      # Positive! You're learning
            "skill_development": 0.2,  # Skill increased
            "ai_reliance": 0.3,        # Moderate AI use
            "autonomy_retention": 0.85 # You retain high agency
        },
        "epistemic_debts": [],         # No questionable claims
        "gate_results": {
            "gate_1_passed": True,     # Net agency positive
            "gate_2_passed": True,     # No dark patterns
            "gate_3_passed": True,     # You can override
            "gate_4_passed": True      # Fast response
        }
    }
}
```

## Core Concepts

### 1. Agency Retention Index (ARI)

ARI tracks whether AI assistance is helping or hindering your capability development:

- **Delta Agency**: Change in your overall capability (-1.0 to +1.0)
- **Skill Development**: How much you learned from this interaction
- **AI Reliance**: How dependent you are on AI assistance
- **Autonomy Retention**: Your ability to act independently

**Goal**: Keep Delta Agency positive and Skill Development high.

### 2. Fractal Flow Engine (FFE)

FFE helps you build momentum and achieve goals through:

- **80/20 Scoping**: Identifies the 20% of work that yields 80% of value
- **5-Block Stop Rule**: Breaks work into manageable 15-90 minute blocks
- **Growth Scaffold**: Detects and helps you overcome bottlenecks
- **Strength Amplifier**: Frames tasks to leverage your signature strengths
- **Reward Emitter**: Celebrates wins to build intrinsic motivation

### 3. Epistemic Debt Management (EDM)

EDM monitors the quality of AI-generated content:

- **Unfalsifiable Claims**: Statements that can't be proven wrong
- **Unverified Assertions**: Claims without evidence
- **Vague Claims**: Imprecise or ambiguous statements

**Goal**: Keep epistemic debt low for reliable, actionable information.

### 4. The 4-Gate System

Every AI interaction passes through four ethical gates:

1. **Gate 1 - Net Agency**: Does this enhance your capability?
2. **Gate 2 - Extraction Static Analysis**: Are there dark patterns?
3. **Gate 3 - Humanity Override**: Can you stop or modify this?
4. **Gate 4 - Performance Parity**: Is the AI fast enough?

If any gate fails, the interaction is blocked or flagged for review.

## Common Use Cases

### Learning New Skills

```python
# AI-PAL provides scaffolding, not just answers
result = await system.process_request(
    user_id="learner-123",
    query="I want to learn React hooks",
    session_id="learning-react"
)

# FFE creates a learning path
goals = await system.ffe_engine.ingest_goal(
    user_id="learner-123",
    description="Master React hooks",
    complexity_level=TaskComplexityLevel.MULTI_STEP
)

# Get 5-block learning plan
plan = await system.ffe_engine.create_5_block_plan(
    goal_id=goals.goal_id,
    user_id="learner-123"
)
```

### Debugging Code

```python
# AI-PAL guides your debugging process
result = await system.process_request(
    user_id="dev-456",
    query="My API returns 500 errors. Help me debug.",
    session_id="debug-session"
)

# Check if you learned debugging skills
if result.metadata['ari_snapshot'].skill_development > 0.1:
    print("Great! You're developing debugging skills.")
else:
    print("Warning: You might be relying too much on AI.")
```

### Building Projects

```python
# FFE helps you scope and execute projects
goal = await system.ffe_engine.ingest_goal(
    user_id="builder-789",
    description="Build a todo app with authentication",
    complexity_level=TaskComplexityLevel.MULTI_PHASE
)

# Get 80/20 scoping
scoping_result = await system.ffe_engine.scoping_agent.scope_goal(
    goal=goal,
    personality=user_personality
)

# Work in focused blocks
for block in scoping_result.blocks:
    # Focus for 15-90 minutes
    result = await work_on_block(block)

    # Celebrate completion
    reward = await system.ffe_engine.reward_emitter.emit_reward(
        win=f"Completed {block.description}",
        personality=user_personality
    )
```

## Monitoring Your Progress

### View Your Agency Dashboard

```python
from ai_pal.ui.agency_dashboard import AgencyDashboard

dashboard = AgencyDashboard(user_id="your-user-id")

# Get current metrics
metrics = await dashboard.get_current_metrics()
print(f"Current Agency Score: {metrics['current_agency']}")
print(f"7-day Trend: {metrics['7_day_trend']}")

# Get recent snapshots
snapshots = await dashboard.get_recent_snapshots(days=7)

# Check for alerts
alerts = await dashboard.get_active_alerts()
for alert in alerts:
    print(f"⚠️ {alert.alert_type}: {alert.message}")
```

### Check Epistemic Debt

```python
# Review epistemic debt from recent interactions
debts = await system.edm_monitor.get_recent_debts(
    user_id="your-user-id",
    days=7
)

# High-severity debts require attention
critical_debts = [d for d in debts if d.severity == "high"]
if critical_debts:
    print(f"⚠️ {len(critical_debts)} high-severity debts detected")
```

## Appealing AI Decisions

If you disagree with an AI decision, you can submit an appeal:

```python
from ai_pal.gates.enhanced_tribunal import EnhancedTribunal, AppealPriority

tribunal = EnhancedTribunal()

# Submit an appeal
appeal = await tribunal.submit_appeal(
    Appeal(
        appeal_id="appeal-001",
        user_id="your-user-id",
        action_id="blocked-action-123",
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=AppealPriority.HIGH,
        ai_decision="Gate 1 blocked your request",
        user_complaint="I believe this would help me learn",
        decision_context={"gate": "gate_1", "reason": "deskilling_risk"}
    )
)

# Appeals are reviewed by multiple stakeholders
# You'll receive a decision within:
# - Critical: 6 hours
# - High: 1 day
# - Medium: 3 days
# - Low: 7 days
```

## Best Practices

### 1. Set Learning Goals

Define what you want to achieve, not just what you want AI to do for you:

```python
# ❌ Bad: "Write a function that..."
# ✅ Good: "Help me learn to write a function that..."

goal = await ffe.ingest_goal(
    user_id="user",
    description="Learn to implement authentication (not just get working code)",
    complexity_level=TaskComplexityLevel.MULTI_STEP
)
```

### 2. Review Your ARI Regularly

Check your agency trends weekly:

```python
# Get 30-day trend
trend = await ari_monitor.calculate_trend(
    user_id="user",
    days=30
)

if trend['direction'] == 'declining':
    print("⚠️ Your agency is declining. Try more hands-on work.")
```

### 3. Verify High-Stakes Information

For critical decisions, check epistemic debt:

```python
result = await system.process_request(
    user_id="user",
    query="What's the best treatment for this medical condition?",
    session_id="medical-query"
)

# Check epistemic debts
debts = result.metadata.get('epistemic_debts', [])
high_risk = [d for d in debts if d.get('high_risk_count', 0) > 0]

if high_risk:
    print("⚠️ This response contains unverified medical claims.")
    print("Consult a healthcare professional.")
```

### 4. Use FFE for Big Projects

Break large goals into manageable pieces:

```python
# Ingest main goal
main_goal = await ffe.ingest_goal(
    user_id="user",
    description="Build and deploy a production web app",
    complexity_level=TaskComplexityLevel.MULTI_PHASE
)

# FFE breaks it into atomic tasks
# Work on one 15-90 minute block at a time
# Celebrate small wins to build momentum
```

## Configuration

### Model Selection

AI-PAL supports multiple model providers:

```python
config = ACConfig(
    enable_model_orchestration=True,
    model_preferences={
        "default_provider": "anthropic",  # or "openai", "local"
        "optimization_goal": "balanced",   # or "speed", "quality", "cost"
    }
)
```

### Privacy Settings

Control data collection and retention:

```python
config = ACConfig(
    enable_ari_monitoring=True,   # Track agency
    enable_edm_monitoring=True,   # Monitor quality
    data_retention_days=90,       # Auto-delete old data
    pii_detection_enabled=True,   # Detect/redact PII
)
```

### Gate Configuration

Adjust gate sensitivity:

```python
config = ACConfig(
    enable_gates=True,
    gate_settings={
        "gate_1_threshold": 0.0,  # Require net positive agency
        "gate_2_enabled": True,   # Enable dark pattern detection
        "gate_3_required": True,  # Require override capability
        "gate_4_max_latency": 5000,  # Max 5 seconds
    }
)
```

## Troubleshooting

### "Gate 1 blocked my request"

Your request was flagged as potentially deskilling. Try:

1. Rephrase to emphasize learning: "Help me understand..."
2. Request scaffolding: "Guide me through..."
3. Submit an appeal if you believe it's a false positive

### "High epistemic debt detected"

The AI's response contains questionable claims. Review the debts:

```python
debts = result.metadata['epistemic_debts']
for debt in debts:
    print(f"{debt['type']}: {debt['claim']}")
    print(f"Severity: {debt['severity']}")
```

### "Agency score declining"

Your agency is decreasing. To recover:

1. Work on tasks independently before asking AI
2. Implement solutions yourself, using AI for guidance only
3. Review the learning path in your FFE goals

## Next Steps

- **User Manual**: Detailed guide to all features
- **Developer Docs**: Architecture and API reference
- **Tutorials**: Step-by-step walkthroughs
- **Community**: Join discussions and share experiences

## Support

- **Documentation**: https://docs.ai-pal.dev
- **GitHub Issues**: https://github.com/your-org/ai-pal/issues
- **Community Forum**: https://community.ai-pal.dev

---

**Remember**: AI-PAL's goal is to make you more capable, not more dependent. Use it as a partner in growth, not a replacement for thinking.
