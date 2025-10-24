# Phase 5: Fractal Flow Engine (FFE) V3.0 - Architecture

## Overview

The Fractal Flow Engine (FFE) is a non-extractive user engagement system that generates sustained motivation through the **Momentum Loop** - a psychology-driven cycle that builds competence and autonomy using signature strengths.

**Core Algorithm**: `WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN`

## Why FFE Helps Gate #2 (Humanity Gate)

FFE is specifically designed to pass the Humanity Gate by demonstrating:

✅ **Non-exploitative design** - Pride-based (not shame/fear) motivation
✅ **Autonomy respect** - 5-Block Stop rule, user-driven goals
✅ **Genuine competence building** - Not artificial dependency
✅ **User-centric alignment** - Leverages signature strengths
✅ **Transparency** - Clear task reframing, explicit rewards

**Expected Humanity Gate Boost**: +20-30 points (from FFE metrics)

---

## Phase 5.1 Status: ARCHITECTURE COMPLETE ✅

### Deliverables:

| Component | Status | File | Lines |
|-----------|--------|------|-------|
| **Data Models** | ✅ Complete | `src/ai_pal/ffe/models.py` | 700+ |
| **Module Exports** | ✅ Complete | `src/ai_pal/ffe/__init__.py` | 100 |
| **Component Interfaces** | ✅ Complete | `src/ai_pal/ffe/interfaces.py` | 650+ |
| **Integration Layer** | ✅ Complete | `src/ai_pal/ffe/integration.py` | 550+ |

**Total**: ~2,000 lines of architecture code

---

## Core Data Models

### 1. Personality & Identity

**PersonalityProfile**
- User's "config file" for the FFE
- Stores: signature strengths, core values, life goals, priorities
- **Integration**: Stored as memories in `EnhancedContextManager` (Phase 3)

**SignatureStrength**
- User's core identity-based talent (e.g., "Visual Thinker", "Empathetic Writer")
- Used by Signature Strength Amplifier to reframe tasks
- Tracks: usage count, confidence score, compatible task types

```python
# Example
strength = SignatureStrength(
    strength_type=StrengthType.VISUAL_THINKING,
    identity_label="Strong Visual Thinker",
    compatible_task_types={"design", "mapping", "visualization"}
)
```

### 2. Goals & Tasks

**GoalPacket**
- A goal at any scoping level (MEGA → MACRO → MINI → MICRO → ATOMIC)
- Flows through Fractal 80/20 Scoping Agent
- Tracks: parent/child hierarchy, value/effort ratios, status

**AtomicBlock**
- Final output of scoping: indivisible, time-boxed work unit (15-90 min)
- Clear success criteria, achievable "Earned Win"
- Tracks: strength reframing, completion quality, pride hit intensity

```python
# Example
block = AtomicBlock(
    title="Master Python Lists",
    description="Complete 5 list exercises in Python tutorial",
    time_block_size=TimeBlockSize.BLOCK_30,  # 30 minutes
    using_strength=StrengthType.ANALYTICAL,
    completed=True,
    pride_hit_intensity=0.85
)
```

**BottleneckTask**
- Task user avoids or struggles with
- Detected via ARI Monitor integration
- Queued for strength-based reframing during momentum loops

### 3. Momentum Loop

**MomentumLoopState**
- Tracks progress through: WIN_STRENGTH → AFFIRM_PRIDE → PIVOT_DETECT → REFRAME_STRENGTH → LAUNCH_GROWTH → WIN_GROWTH
- Links strength tasks to growth tasks
- Measures success rate and bottleneck resolution

**RewardMessage**
- Identity-affirming reward from Accomplishment Reward Emitter
- Uses explicit strength language
- Example: *"Goal Accomplished! You are a strong visual thinker, and you applied that talent perfectly here."*

### 4. Time Management

**FiveBlockPlan**
- Implements 5-Block Rule (e.g., 5-month project → 5x1-month blocks)
- Enforces autonomy via stop points
- User can reassess and modify plan

**ScopingSession**
- Documents a single 80/20 scoping decision
- Identifies the 20% that delivers 80% value
- Reframes as new 100% goal

---

## Component Interfaces

All FFE components implement well-defined interfaces for clean integration:

### Core Components

1. **IGoalIngestor** - Task intake (macro-goals + ad-hoc tasks)
2. **IScopingAgent** - Fractal 80/20 scoping algorithm
3. **ITimeBlockManager** - Time/energy alignment (5-Block + Atomic)
4. **IStrengthAmplifier** - Task reframing via signature strengths
5. **IGrowthScaffold** - Bottleneck detection and queueing
6. **IRewardEmitter** - Identity-affirming accomplishment rewards
7. **IMomentumLoopOrchestrator** - Core WIN → AFFIRM → PIVOT → ... cycle

### Expansion Modules

8. **ISocialRelatednessModule** - Non-coercive win sharing
9. **ICreativeSandboxModule** - Process-based creative wins
10. **IEpicMeaningModule** - Value-goal narrative connection

### Integration Connectors

11. **IPersonalityModuleConnector** - Links to `EnhancedContextManager`
12. **IARIConnector** - Links to `ARIMonitor` for bottleneck detection
13. **IDashboardConnector** - Links to `AgencyDashboard` for metrics

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│      AC-AI Framework (Phases 1-3) - EXISTING           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Gate System  │  │ ARI Monitor  │  │   Context    │ │
│  │  (Phase 1)   │  │  (Phase 2)   │  │   Manager    │ │
│  │              │  │              │  │  (Phase 3)   │ │
│  │ - Autonomy   │  │ - Skill      │  │ - Memories   │ │
│  │ - Humanity ✨│  │   Atrophy    │  │ - Search     │ │
│  │ - Oversight  │  │ - Agency     │  │ - Storage    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │         │
│         └─────────────────┼──────────────────┘         │
│                           │                            │
└───────────────────────────┼────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Integration   │
                    │   Connectors   │
                    └───────┬────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼──────────────────────────────────────▼───────┐
│   Fractal Flow Engine (FFE) - Phase 5 - NEW         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │     Momentum Loop Orchestrator (Core)          │ │
│  │  WIN → AFFIRM → PIVOT → REFRAME → LAUNCH       │ │
│  └──────┬─────────────┬────────────┬──────────────┘ │
│         │             │            │                │
│  ┌──────▼─────┐ ┌────▼────┐ ┌─────▼──────┐        │
│  │  Scoping   │ │ Strength│ │  Growth    │        │
│  │   Agent    │ │Amplifier│ │  Scaffold  │        │
│  │  (80/20)   │ │ (Pride) │ │(Bottleneck)│        │
│  └────────────┘ └─────────┘ └────────────┘        │
│                                                     │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐    │
│  │    Goal    │ │Time-Block│ │   Reward     │    │
│  │  Ingestor  │ │ Manager  │ │   Emitter    │    │
│  └────────────┘ └──────────┘ └──────────────┘    │
│                                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │       Expansion Modules (Optional)           │ │
│  │  • Social Relatedness  • Creative Sandbox    │ │
│  │  • Epic Meaning                              │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Gate #2 ✅    │
                    │  (Humanity)    │
                    │  Score +25     │
                    └────────────────┘
```

---

## Integration Details

### 1. Context Manager Integration (Personality Module)

**Purpose**: Store personality profiles as memories

**Mapping**:
- Core Values → `MemoryType.PREFERENCE` + tag `"core_value"`
- Life Goals → `MemoryType.GOAL` + tag `"life_goal"`
- Priorities → `MemoryType.GOAL` + tag `"current_priority"`
- Strengths → `MemoryType.SKILL` + tag `"signature_strength"`

**Implementation**: `PersonalityModuleConnector` in `integration.py`

**Methods**:
```python
async def load_personality_profile(user_id: str) -> PersonalityProfile
async def save_personality_profile(profile: PersonalityProfile) -> bool
async def update_strength(user_id: str, strength: SignatureStrength) -> bool
```

### 2. ARI Monitor Integration (Bottleneck Detection)

**Purpose**: Detect tasks user avoids for Growth Scaffold

**Data Sources**:
- ARI alerts (skill atrophy warnings)
- ARI trends (declining skill_development)
- Snapshot history (task frequency analysis)

**Implementation**: `ARIConnector` in `integration.py`

**Methods**:
```python
async def detect_skill_atrophy(user_id: str, lookback_days: int = 30) -> List[str]
async def get_avoided_tasks(user_id: str) -> List[Dict[str, Any]]
```

**Logic**:
1. Check ARI report for skill atrophy alerts
2. Analyze snapshots for negative skill_development
3. Identify tasks not done in 14+ days
4. Create `BottleneckTask` objects

### 3. Multi-Model Orchestrator Integration (AI Responses)

**Purpose**: Use AI for scoping, reframing, reward generation

**FFE Task Requirements**:
- Complexity: `MODERATE` (need good reasoning)
- Min Reasoning: `0.75`
- Max Cost: `$0.005` per 1K tokens (high frequency)
- Max Latency: `2000ms` (responsive UX)
- Local: `False` (can use cloud models)

**Use Cases**:
- Scoping Agent: 80/20 analysis
- Strength Amplifier: Task reframing
- Reward Emitter: Message generation
- Growth Scaffold: Bottleneck analysis

### 4. Dashboard Integration (FFE Metrics)

**Purpose**: Display FFE performance in Agency Dashboard

**Metrics Displayed**:
- Momentum loop statistics (total, successful, success rate)
- Atomic blocks completed (strength vs growth)
- Bottleneck resolution progress
- Pride hit metrics (count, average intensity)
- Autonomy respect (5-Block Stops, user modifications)
- **Humanity Gate contribution** (+20-30 points)

**Implementation**: `DashboardConnector` in `integration.py`

---

## Humanity Gate Scoring

FFE contributes to Gate #2 (Humanity Gate) scoring:

```python
async def calculate_ffe_humanity_gate_contribution(
    ffe_metrics: FFEMetrics
) -> float:
    """
    Calculate FFE's contribution to Humanity Gate score (0-30 points)

    Breakdown:
    - Non-exploitative design: 0-10 points (pride hits, positive loops)
    - Autonomy respect: 0-10 points (5-Block Stops, user modifications)
    - Competence building: 0-10 points (bottleneck resolution rate)
    """
```

**Example Scoring**:
- User completes 50 atomic blocks → 50 pride hits → +8 points (non-exploitative)
- User exercises 5-Block Stop 3 times → +5 points (autonomy)
- User modifies plans 10 times → +5 points (autonomy)
- Resolves 15/20 bottlenecks (75% rate) → +7.5 points (competence)

**Total**: +25.5 points to Humanity Gate

---

## Next Steps (Phase 5.2-5.7)

### Phase 5.2: Goal Processing Pipeline (2 days)
- Implement `GoalIngestor`
- Implement `Fractal80/20ScopingAgent`
- Implement `TimeBlockManager`
- **Deliverable**: Goal → Atomic Block pipeline

### Phase 5.3: Signature Strength Amplifier (1 day)
- Implement strength identification
- Implement task reframing
- Implement reward language generation
- **Deliverable**: Strength-based personalization

### Phase 5.4: Momentum Loop Core (2 days)
- Implement `RewardEmitter`
- Implement `GrowthScaffold`
- Implement `MomentumLoopOrchestrator`
- **Deliverable**: Complete WIN → ... → WIN cycle

### Phase 5.5: Expansion Modules (2 days)
- Implement Social Relatedness Module
- Implement Creative Sandbox Module
- Implement Epic Meaning Module
- **Deliverable**: Three optional plugins

### Phase 5.6: AC-AI Integration (1 day)
- Wire up all integration connectors
- Test end-to-end with Gate System
- Validate Humanity Gate boost
- **Deliverable**: FFE fully integrated

### Phase 5.7: Testing & Validation (1 day)
- Write 50+ FFE component tests
- Write Momentum Loop integration tests
- Write Humanity Gate validation tests
- **Deliverable**: Complete test coverage

---

## Design Decisions & Rationale

### 1. Why Store Personality in Context Manager?

**Decision**: Use `EnhancedContextManager` (Phase 3) instead of separate database

**Rationale**:
- Reuse existing memory search/embedding infrastructure
- Leverage semantic search for strength matching
- Unified storage layer (all user data in one place)
- Memory consolidation handles profile optimization
- Privacy Manager already protects this data

### 2. Why Integrate with ARI Monitor?

**Decision**: Use ARI for bottleneck detection instead of separate tracking

**Rationale**:
- ARI already tracks skill development and atrophy
- ARI alerts flag declining competence (= bottlenecks)
- Avoids duplicate tracking systems
- Provides validated agency metrics
- Natural integration point for Growth Scaffold

### 3. Why 80/20 Fractal Scoping?

**Decision**: Recursive 80/20 principle vs. fixed task decomposition

**Rationale**:
- Maximizes value/effort ratio at every level
- Self-similar at all scales (fractal property)
- User always works on highest-value 20%
- Remaining 20% becomes next input (continuous flow)
- Prevents overwhelm from large goals

### 4. Why Signature Strengths vs. Generic Skills?

**Decision**: Identity-based strengths vs. skill taxonomy

**Rationale**:
- Taps into pride and self-concept (stronger motivation)
- More stable than skills (strengths are core identity)
- Easier to reframe tasks ("use your visual talent")
- Creates personal connection to work
- Supports non-exploitative design (builds on what they're proud of)

### 5. Why 5-Block Stop Rule?

**Decision**: Mandatory pause points vs. continuous planning

**Rationale**:
- Enforces autonomy (user must choose to continue)
- Prevents sunk cost fallacy
- Allows course correction
- Respects user agency
- Direct Gate #2 (Humanity) compliance signal

---

## File Structure

```
src/ai_pal/ffe/
├── __init__.py              # Module exports
├── models.py                # Data models (700+ lines)
├── interfaces.py            # Component interfaces (650+ lines)
├── integration.py           # AC-AI integration (550+ lines)
│
├── goal_ingestor.py         # [Phase 5.2] Goal intake
├── scoping_agent.py         # [Phase 5.2] 80/20 scoping
├── time_block_manager.py    # [Phase 5.2] Time alignment
├── strength_amplifier.py    # [Phase 5.3] Pride engine
├── growth_scaffold.py       # [Phase 5.4] Bottleneck detection
├── reward_emitter.py        # [Phase 5.4] Accomplishment rewards
├── momentum_loop.py         # [Phase 5.4] Core orchestrator
│
└── expansion/
    ├── social_relatedness.py    # [Phase 5.5] Win sharing
    ├── creative_sandbox.py      # [Phase 5.5] Process wins
    └── epic_meaning.py          # [Phase 5.5] Value connection
```

---

## References

- **FFE Specification**: Original V3.0 module specification (provided)
- **Phase 1**: Gate System, AHO Tribunal, Plugin Architecture
- **Phase 2**: ARI Monitor, EDM, Self-Improvement Loop
- **Phase 3**: Context Manager, Privacy, Multi-Model Orchestrator, Dashboard
- **AC-AI Framework**: Four Gates (Autonomy, Humanity, Oversight, Alignment)

---

**Status**: Phase 5.1 Architecture ✅ Complete
**Next**: Wait for Phase 4 pip install → Begin Phase 5.2 Implementation
**Timeline**: ~10 days for full FFE implementation (Phases 5.2-5.7)
