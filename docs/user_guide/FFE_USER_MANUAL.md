# Fractal Flow Engine (FFE) User Manual

The Fractal Flow Engine (FFE) is AI-PAL's growth scaffolding system. It helps you build momentum, overcome bottlenecks, and achieve goals while developing your capabilities.

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Components](#components)
4. [Workflows](#workflows)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Overview

FFE is based on motivation science and implements seven core components:

1. **Goal Ingestor**: Captures and structures your goals
2. **Scoping Agent**: Uses 80/20 analysis to find high-value work
3. **Time Block Manager**: Creates focused work sessions (5-Block Stop Rule)
4. **Strength Amplifier**: Frames tasks to leverage your strengths
5. **Reward Emitter**: Celebrates wins to build intrinsic motivation
6. **Growth Scaffold**: Detects and helps overcome bottlenecks
7. **Momentum Loop**: Tracks your flow state and productivity

## Core Concepts

### The Momentum Loop

FFE tracks your progression through four states:

```
Friction → Flow → Win → Pride
   ↓                      ↑
   └──────────────────────┘
```

- **Friction**: Initial resistance to starting
- **Flow**: Engaged, productive work state
- **Win**: Task completion
- **Pride**: Celebration and reinforcement

**Goal**: Minimize time in Friction, maximize time in Flow, and always celebrate Wins to generate Pride.

### Task Complexity Levels

FFE classifies tasks by complexity:

- **Atomic**: Single, focused task (15-30 min)
- **Simple**: Small multi-step task (30-90 min)
- **Multi-Step**: Larger task requiring planning (2-4 hours)
- **Multi-Phase**: Major project (days to weeks)
- **Long-Term**: Strategic goal (months)

### 80/20 Fractal Scoping

The Scoping Agent applies the Pareto Principle recursively:

1. Identify the 20% of work that yields 80% of value
2. Break that 20% into smaller pieces
3. Repeat until you have atomic tasks
4. Start with the highest-value atomic task

### 5-Block Stop Rule

Work is structured into five time blocks:

1. **Tiny Block** (15 min): Overcome friction, build momentum
2. **Small Block** (30 min): Focused work session
3. **Medium Block** (60 min): Deep work
4. **Large Block** (90 min): Extended focus
5. **Stop**: Mandatory break

**Rule**: After any block, you can stop. No obligation to continue reduces friction.

## Components

### 1. Goal Ingestor

**Purpose**: Capture and structure your goals

**API**:

```python
from ai_pal.ffe.engine import FractalFlowEngine
from ai_pal.ffe.models import TaskComplexityLevel

ffe = FractalFlowEngine()

# Ingest a goal
goal = await ffe.ingest_goal(
    user_id="user-123",
    description="Build a personal website with blog",
    complexity_level=TaskComplexityLevel.MULTI_PHASE,
    target_date=datetime.now() + timedelta(days=30),
    metadata={
        "motivation": "Share my knowledge",
        "stakes": "medium"
    }
)
```

**Best Practices**:
- Be specific: "Build a responsive blog with React" not "Make a website"
- Include why: Motivation increases follow-through
- Set realistic deadlines: Creates healthy pressure

**Output**:
```python
{
    "goal_id": "goal-abc123",
    "description": "Build a personal website with blog",
    "complexity_level": "multi_phase",
    "estimated_blocks": 24,  # 24 work sessions
    "target_completion": "2024-12-31",
    "status": "active"
}
```

### 2. Scoping Agent

**Purpose**: Apply 80/20 analysis to find high-value work

**API**:

```python
# Scope a goal
scoping = await ffe.scoping_agent.scope_goal(
    goal=goal,
    personality=user_personality  # Uses your signature strengths
)
```

**What It Does**:
1. Analyzes the goal
2. Identifies the 20% that delivers 80% of value
3. Breaks into atomic tasks
4. Prioritizes by value/effort ratio

**Output**:
```python
{
    "eighty_win": "Get blog displaying posts from Markdown files",
    "atomic_tasks": [
        {
            "description": "Set up Next.js project",
            "value_score": 0.9,
            "effort_score": 0.2,
            "priority": 1
        },
        {
            "description": "Create Markdown parser",
            "value_score": 0.8,
            "effort_score": 0.3,
            "priority": 2
        },
        ...
    ],
    "deferred_tasks": [...]  # The 80% that gives 20% value
}
```

**Best Practices**:
- Trust the 80/20 analysis - resist scope creep
- Work on atomic tasks in priority order
- Defer the 80% until you've completed the 20%

### 3. Time Block Manager

**Purpose**: Create focused work sessions using the 5-Block Stop Rule

**API**:

```python
# Create a 5-block plan
plan = await ffe.create_5_block_plan(
    goal_id=goal.goal_id,
    user_id="user-123"
)

# Start a block
block = plan.blocks[0]  # Tiny block (15 min)
start_time = datetime.now()

# ... do the work ...

# Complete the block
await ffe.complete_block(
    block_id=block.block_id,
    user_id="user-123",
    completed=True
)
```

**Block Sizing Logic**:

The system automatically sizes blocks based on:
- Task complexity
- Your current momentum state
- Time of day
- Recent performance

**5-Block Progression**:

```
Block 1: Tiny (15 min)  ← Overcome friction
  ↓ (can stop or continue)
Block 2: Small (30 min) ← Build momentum
  ↓ (can stop or continue)
Block 3: Medium (60 min) ← Enter flow
  ↓ (can stop or continue)
Block 4: Large (90 min) ← Deep work
  ↓ (can stop or continue)
Block 5: STOP ← Mandatory break
```

**Output**:
```python
{
    "plan_id": "plan-xyz789",
    "blocks": [
        {
            "block_id": "block-1",
            "size": "tiny",
            "duration_minutes": 15,
            "task": "Set up development environment",
            "status": "pending"
        },
        ...
    ],
    "total_duration_minutes": 195,  # 15+30+60+90
    "estimated_completion": "2024-01-15 14:30:00"
}
```

**Best Practices**:
- Always start with the Tiny Block
- Use the "can stop" option - it reduces friction
- Take the mandatory break after Block 5
- If you stop early, that's fine! Celebrate what you did complete.

### 4. Strength Amplifier

**Purpose**: Reframe tasks to leverage your signature strengths

**API**:

```python
# Get task reframing
reframing = await ffe.strength_amplifier.reframe_task(
    task="Debug authentication bug",
    personality=user_personality  # Knows your strengths
)
```

**How It Works**:

If your signature strengths are "curiosity" and "perseverance":

```python
# Original task
"Debug authentication bug"

# Reframed
"Investigate the authentication mystery - follow the clues until you solve it"
```

The reframing makes the task intrinsically motivating by connecting it to what you naturally enjoy.

**Output**:
```python
{
    "original_task": "Debug authentication bug",
    "reframed_task": "Investigate the authentication mystery...",
    "strengths_used": ["curiosity", "perseverance"],
    "identity_language": "detective",  # You're a detective, not just a debugger
    "motivational_boost": 0.75  # 75% increase in intrinsic motivation
}
```

**Best Practices**:
- Set up your personality profile accurately
- Update it as you discover new strengths
- Use reframed language when starting tasks

### 5. Reward Emitter

**Purpose**: Celebrate wins to build intrinsic motivation and momentum

**API**:

```python
# Emit a reward after completing a task
reward = await ffe.reward_emitter.emit_reward(
    win="Completed user authentication",
    personality=user_personality
)
```

**Reward Types**:

1. **Progress Recognition**: "You've completed 3/10 tasks"
2. **Skill Development**: "You learned JWT authentication"
3. **Momentum Building**: "That's your 3rd win today!"
4. **Personal Pride**: "This showcases your problem-solving strength"

**Output**:
```python
{
    "reward_text": "Excellent work! You solved that authentication challenge using your analytical strength. You're building real security expertise.",
    "reward_type": "skill_development",
    "pride_level": "high",
    "momentum_boost": 0.8
}
```

**Best Practices**:
- Celebrate every win, no matter how small
- Read the reward - it's personalized to you
- Share wins with others to amplify pride

### 6. Growth Scaffold

**Purpose**: Detect and help overcome bottlenecks

**API**:

```python
# Check for bottlenecks
bottlenecks = await ffe.growth_scaffold.detect_bottlenecks(
    user_id="user-123",
    days=7  # Look at last 7 days
)

# Get help with a bottleneck
resolution = await ffe.growth_scaffold.suggest_resolution(
    bottleneck=bottlenecks[0]
)
```

**Bottleneck Types**:

1. **Knowledge Gap**: Missing information/skills
2. **Resource Gap**: Lacking tools/access
3. **Decision Paralysis**: Overwhelmed by choices
4. **Motivation Dip**: Lost momentum
5. **Scope Creep**: Goal became too large

**Detection**:

The scaffold detects bottlenecks by analyzing:
- Tasks stuck for >2 days
- Multiple failed attempts
- Declining momentum scores
- Increasing friction times

**Resolution Strategies**:

```python
{
    "bottleneck_type": "knowledge_gap",
    "description": "Don't know how to implement OAuth",
    "suggested_resolutions": [
        {
            "strategy": "learn_then_do",
            "actions": [
                "Find OAuth tutorial (15 min)",
                "Build simple OAuth demo (60 min)",
                "Apply to your project (30 min)"
            ]
        },
        {
            "strategy": "ask_for_help",
            "actions": [
                "Post specific question on Stack Overflow",
                "Join OAuth Discord community"
            ]
        },
        {
            "strategy": "scope_down",
            "actions": [
                "Start with simpler auth (username/password)",
                "Add OAuth in version 2"
            ]
        }
    ],
    "recommended_strategy": "learn_then_do"
}
```

**Best Practices**:
- Check for bottlenecks weekly
- Address bottlenecks before they cause long delays
- Use scaffold suggestions as starting points
- Sometimes the best resolution is scope reduction

### 7. Momentum Loop

**Purpose**: Track your flow state and productivity

**API**:

```python
# Get current momentum state
state = await ffe.get_momentum_state(user_id="user-123")

# Record state transition
await ffe.record_transition(
    user_id="user-123",
    from_state="friction",
    to_state="flow",
    trigger="started_tiny_block"
)
```

**States**:

- **Friction**: Haven't started yet (high resistance)
- **Flow**: Actively working (low resistance, high focus)
- **Win**: Just completed something
- **Pride**: Celebrating the accomplishment

**Metrics**:

```python
{
    "current_state": "flow",
    "time_in_state_minutes": 45,
    "todays_states": {
        "friction": 20,  # minutes
        "flow": 180,
        "win": 5,
        "pride": 10
    },
    "momentum_score": 0.85,  # 0-1, higher is better
    "flow_efficiency": 0.82,  # % of work time in flow
    "friction_to_flow_time": 8  # avg minutes to overcome friction
}
```

**Best Practices**:
- Minimize friction time with Tiny Blocks
- Maximize flow time with appropriate block sizing
- Always celebrate wins to generate pride
- Track trends to optimize your productivity

## Workflows

### Starting a New Project

1. **Ingest the goal**:
```python
goal = await ffe.ingest_goal(
    user_id="user",
    description="Build project management app",
    complexity_level=TaskComplexityLevel.MULTI_PHASE
)
```

2. **Get 80/20 scoping**:
```python
scoping = await ffe.scoping_agent.scope_goal(goal, personality)
```

3. **Create first 5-block plan**:
```python
plan = await ffe.create_5_block_plan(goal.goal_id, "user")
```

4. **Start with Tiny Block**:
```python
# Just 15 minutes to overcome friction
await work_on_block(plan.blocks[0])
```

5. **Celebrate and iterate**:
```python
reward = await ffe.reward_emitter.emit_reward(
    win="Completed first block",
    personality=personality
)
```

### Overcoming a Bottleneck

1. **Detect bottleneck**:
```python
bottlenecks = await ffe.growth_scaffold.detect_bottlenecks("user", days=7)
```

2. **Analyze**:
```python
for b in bottlenecks:
    print(f"Stuck on: {b.task_description}")
    print(f"Type: {b.bottleneck_type}")
    print(f"Duration: {b.days_stuck} days")
```

3. **Get resolution suggestions**:
```python
resolution = await ffe.growth_scaffold.suggest_resolution(bottlenecks[0])
```

4. **Apply strategy**:
```python
chosen_strategy = resolution.suggested_resolutions[0]
for action in chosen_strategy.actions:
    # Create atomic task for each action
    task = await ffe.create_atomic_task(action)
```

5. **Track progress**:
```python
# Mark original bottleneck as resolved when done
await ffe.growth_scaffold.mark_resolved(bottlenecks[0].bottleneck_id)
```

### Daily Productivity Routine

**Morning** (5 min):
```python
# Review momentum from yesterday
yesterday = await ffe.get_momentum_summary("user", days=1)

# Check active goals
goals = await ffe.get_active_goals("user")

# Plan first 5-block session
plan = await ffe.create_5_block_plan(goals[0].goal_id, "user")
```

**Work Session**:
```python
# Start with Tiny Block (15 min)
await work_on_block(plan.blocks[0])

# Can stop or continue to Small Block (30 min)
if feeling_good:
    await work_on_block(plan.blocks[1])

# Continue or stop
# ... progress through blocks as energy allows ...

# Mandatory break after Block 5
```

**End of Day** (5 min):
```python
# Celebrate today's wins
wins = await ffe.get_todays_wins("user")
for win in wins:
    reward = await ffe.reward_emitter.emit_reward(win, personality)

# Check momentum metrics
metrics = await ffe.get_momentum_state("user")
print(f"Flow efficiency: {metrics.flow_efficiency:.0%}")

# Identify any new bottlenecks
bottlenecks = await ffe.growth_scaffold.detect_bottlenecks("user", days=1)
if bottlenecks:
    # Address tomorrow
    pass
```

## Advanced Features

### Custom Personality Profiles

Define your signature strengths for better task reframing:

```python
from ai_pal.personality.profile import PersonalityProfile, Strength

personality = PersonalityProfile(
    user_id="user",
    signature_strengths=[
        Strength.CURIOSITY,
        Strength.CREATIVITY,
        Strength.PERSEVERANCE,
        Strength.LOVE_OF_LEARNING,
        Strength.PERSPECTIVE
    ],
    values=["autonomy", "mastery", "purpose"],
    identity_labels=["builder", "problem-solver", "learner"]
)

await personality.save()
```

### Adaptive Difficulty Scaling

FFE automatically adjusts task difficulty based on your ARI metrics:

```python
# If ARI shows you're developing skills well
# → FFE increases challenge level

# If ARI shows high AI reliance
# → FFE reduces assistance, adds scaffolding

# Automatic "Goldilocks difficulty" - not too hard, not too easy
```

### Skill Atrophy Prevention

FFE detects when you haven't used a skill recently:

```python
# If you haven't written SQL in 14 days
# → FFE suggests a small SQL task to maintain skill

warnings = await ffe.get_skill_atrophy_warnings("user")
for warning in warnings:
    print(f"⚠️ Skill '{warning.skill}' not used in {warning.days} days")
    print(f"Suggested task: {warning.practice_task}")
```

## Best Practices

### 1. Start Small

Use Tiny Blocks to overcome initial resistance:
- 15 minutes is psychologically manageable
- Builds momentum
- Often leads to continued work

### 2. Celebrate Everything

Every win matters:
- Completed a Tiny Block? Celebrate.
- Fixed a bug? Celebrate.
- Made progress on learning? Celebrate.

Pride is the fuel for continued momentum.

### 3. Trust the 80/20

Resist perfectionism:
- The 80% can wait
- Ship the 20% first
- Iterate based on feedback

### 4. Use Stop Points

The 5-Block Stop Rule reduces friction:
- Knowing you can stop after any block makes starting easier
- Sometimes stopping is the right choice
- Avoid burnout

### 5. Address Bottlenecks Quickly

Don't let bottlenecks linger:
- Check weekly
- Apply suggested resolutions
- Ask for help if needed

### 6. Track Your Metrics

Monitor your momentum:
- Flow efficiency >70% is excellent
- Friction-to-flow time <10 min is good
- Review weekly trends

## Troubleshooting

### "I can't get started (stuck in Friction)"

**Solution**: Use the Tiny Block
```python
# Just commit to 15 minutes
plan = await ffe.create_5_block_plan(goal_id, user_id)
# Work on plan.blocks[0] only
# You can stop after 15 min, no obligation to continue
```

### "I lose momentum quickly"

**Solution**: Check block sizing
```python
# You might be starting with blocks that are too large
# Try:
plan = await ffe.create_5_block_plan(
    goal_id,
    user_id,
    start_small=True  # Forces Tiny → Small progression
)
```

### "Tasks feel demotivating"

**Solution**: Use Strength Amplifier
```python
# Ensure personality profile is set
reframing = await ffe.strength_amplifier.reframe_task(task, personality)

# Use the reframed version
print(reframing.reframed_task)
```

### "I have too many bottlenecks"

**Solution**: Scope down
```python
# Your goals might be too ambitious
# Use 80/20 scoping more aggressively
scoping = await ffe.scoping_agent.scope_goal(goal, personality)

# Work only on the identified 80/20 win
# Defer everything else
```

### "Rewards feel generic"

**Solution**: Improve personality profile
```python
# Add more specific strengths and values
personality.signature_strengths.extend([
    Strength.HUMOR,
    Strength.SOCIAL_INTELLIGENCE
])

personality.identity_labels.append("creative problem-solver")

await personality.save()

# Rewards will now be more personalized
```

## API Reference

See [API_REFERENCE.md](./API_REFERENCE.md) for complete FFE API documentation.

## Further Reading

- **Motivation Science**: Flow (Csikszentmihalyi), Drive (Pink)
- **Productivity**: Getting Things Done (Allen), Deep Work (Newport)
- **Habit Formation**: Atomic Habits (Clear), Tiny Habits (Fogg)

---

**Remember**: FFE is designed to work *with* your natural motivation, not against it. Trust the system, celebrate your wins, and watch your momentum build.
