# Phase 5 Implementation Plan: Fractal Flow Engine (FFE)

**Date**: October 24, 2025
**Status**: 🚧 IN PROGRESS

---

## Overview

The Fractal Flow Engine (FFE) is a non-extractive engagement system that generates sustained user motivation through the "Momentum Loop" - a psychology-driven cycle that builds competence and autonomy using signature strengths.

### Core Algorithm
**WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN**

### Key Principles
- ✅ Non-exploitative design (Gate #2 compliance)
- ✅ User autonomy (5-Block Stop rule)
- ✅ Pride-based (not shame/fear) motivation
- ✅ Builds genuine competence (not dependency)
- ✅ Signature strength amplification

---

## Current Status

### ✅ Already Implemented (2,033 lines)

1. **Models** (`ffe/models.py` - 570 lines)
   - ✅ Enums: StrengthType, TaskComplexityLevel, TimeBlockSize, MomentumState, etc.
   - ✅ Data classes: PersonalityProfile, GoalPacket, AtomicBlock, etc.
   - ✅ Momentum Loop state management
   - ✅ Metrics tracking

2. **Interfaces** (`ffe/interfaces.py` - 763 lines)
   - ✅ 7 core component interfaces
   - ✅ 3 expansion module interfaces
   - ✅ 3 integration connector interfaces
   - ✅ Full API contracts defined

3. **Integration Connectors** (`ffe/integration.py` - 598 lines)
   - ✅ PersonalityModuleConnector (to Context Manager)
   - ✅ ARIConnector (to ARI Monitor)
   - ✅ DashboardConnector (to Agency Dashboard)

### 🚧 To Be Implemented

#### Core Components (7)
1. **GoalIngestor** - Task intake "front door"
2. **ScopingAgent** - 80/20 fractal breakdown
3. **TimeBlockManager** - Time/energy alignment
4. **StrengthAmplifier** - Pride engine
5. **GrowthScaffold** - Bottleneck detection
6. **RewardEmitter** - Accomplishment rewards
7. **MomentumLoopOrchestrator** - Core cycle coordinator

#### Expansion Modules (3)
8. **SocialRelatednessModule** - Non-coercive win sharing
9. **CreativeSandboxModule** - Process-based wins
10. **EpicMeaningModule** - Value-goal connection

#### Main Engine
11. **FractalFlowEngine** - Top-level orchestrator

---

## Implementation Strategy

### Phase 5.1: Core Components (MVP)
**Goal**: Implement minimum viable FFE that can run the Momentum Loop

**Components**:
1. **GoalIngestor** (Simple)
   - Accept macro-goals and ad-hoc tasks
   - Create GoalPackets
   - Basic validation

2. **ScopingAgent** (Simplified)
   - Basic 80/20 breakdown (1-2 levels deep)
   - Create AtomicBlocks
   - No ML/AI complexity initially

3. **TimeBlockManager** (Basic)
   - 5-Block Stop rule enforcement
   - Simple time estimation
   - Energy level tracking (basic)

4. **MomentumLoopOrchestrator** (Core)
   - WIN → AFFIRM → PIVOT → REFRAME → LAUNCH cycle
   - State management
   - Component coordination

5. **RewardEmitter** (Simple)
   - Generate reward messages
   - Track accomplishments
   - Basic identity affirmation

**Defer to Phase 5.2**:
- StrengthAmplifier (can use basic version in Phase 5.1)
- GrowthScaffold (can use basic bottleneck detection)
- Expansion modules (all 3)

### Phase 5.2: Enhancement & Expansion
- Full StrengthAmplifier implementation
- Complete GrowthScaffold with ARI integration
- Add expansion modules
- Advanced AI integration

---

## Architecture

```
FractalFlowEngine
├── Core Components
│   ├── GoalIngestor
│   ├── ScopingAgent
│   ├── TimeBlockManager
│   ├── StrengthAmplifier (basic)
│   ├── GrowthScaffold (basic)
│   ├── RewardEmitter
│   └── MomentumLoopOrchestrator (main coordinator)
│
├── Connectors (✅ Already implemented)
│   ├── PersonalityModuleConnector → Context Manager
│   ├── ARIConnector → ARI Monitor
│   └── DashboardConnector → Agency Dashboard
│
└── Integration with IntegratedACSystem
    - Add FFE as optional Phase 5 component
    - Config flag: enable_ffe
    - Storage: data_dir/ffe/
```

---

## File Structure

```
src/ai_pal/ffe/
├── __init__.py               (✅ Done - exports)
├── models.py                 (✅ Done - data structures)
├── interfaces.py             (✅ Done - contracts)
├── integration.py            (✅ Done - connectors)
├── components/               (🚧 NEW)
│   ├── __init__.py
│   ├── goal_ingestor.py
│   ├── scoping_agent.py
│   ├── time_block_manager.py
│   ├── strength_amplifier.py
│   ├── growth_scaffold.py
│   ├── reward_emitter.py
│   └── momentum_loop.py
├── engine.py                 (🚧 NEW - main FFE class)
└── expansion/                (Phase 5.2)
    ├── __init__.py
    ├── social_relatedness.py
    ├── creative_sandbox.py
    └── epic_meaning.py
```

---

## Implementation Steps (Phase 5.1)

### Step 1: Create Component Implementations Directory
- [ ] Create `src/ai_pal/ffe/components/` directory
- [ ] Create `components/__init__.py`

### Step 2: Implement Core Components (Priority Order)

#### A. GoalIngestor (Simplest - ~100 lines)
- [ ] Implement `ingest_macro_goal()`
- [ ] Implement `ingest_adhoc_task()`
- [ ] Implement `validate_goal()`
- [ ] Basic tests

#### B. RewardEmitter (~80 lines)
- [ ] Implement `emit_win_reward()`
- [ ] Implement `emit_milestone_reward()`
- [ ] Generate identity-affirming messages
- [ ] Basic tests

#### C. TimeBlockManager (~150 lines)
- [ ] Implement `create_five_block_plan()`
- [ ] Implement `enforce_five_block_stop()`
- [ ] Implement `estimate_block_size()`
- [ ] Basic tests

#### D. ScopingAgent (~200 lines)
- [ ] Implement `scope_goal_packet()`
- [ ] Implement `identify_critical_20()`
- [ ] Implement `create_atomic_blocks()`
- [ ] Basic tests

#### E. StrengthAmplifier (Basic - ~100 lines)
- [ ] Implement `identify_strength_opportunities()`
- [ ] Implement `amplify_with_strength()`
- [ ] Basic signature strength matching
- [ ] Basic tests

#### F. GrowthScaffold (Basic - ~120 lines)
- [ ] Implement `detect_bottleneck()`
- [ ] Implement `suggest_scaffold()`
- [ ] Basic ARI integration
- [ ] Basic tests

#### G. MomentumLoopOrchestrator (~250 lines)
- [ ] Implement WIN phase
- [ ] Implement AFFIRM phase
- [ ] Implement PIVOT phase
- [ ] Implement REFRAME phase
- [ ] Implement LAUNCH phase
- [ ] State machine management
- [ ] Coordinate all components
- [ ] Comprehensive tests

### Step 3: Create Main Engine (~150 lines)
- [ ] Implement `FractalFlowEngine` class
- [ ] Initialize all components
- [ ] Connect to Phase 1-3 via connectors
- [ ] Storage management
- [ ] Configuration handling
- [ ] Main API: `start_goal()`, `complete_block()`, `get_momentum_state()`

### Step 4: Integration with IntegratedACSystem
- [ ] Add FFE to `integrated_system.py`
- [ ] Add config flag `enable_ffe`
- [ ] Wire up connectors
- [ ] Storage directory setup

### Step 5: Testing & Validation
- [ ] Unit tests for each component
- [ ] Integration test for Momentum Loop
- [ ] E2E test: Complete goal workflow
- [ ] Validate Gate #2 compliance
- [ ] Validate 5-Block Stop rule

---

## Success Criteria (Phase 5.1 MVP)

1. ✅ **Core Components Implemented**
   - All 7 core components functional
   - Pass unit tests

2. ✅ **Momentum Loop Works**
   - Can run WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN
   - State transitions correctly
   - Generates rewards

3. ✅ **Integration Complete**
   - FFE accessible from IntegratedACSystem
   - Connectors to Phase 1-3 working
   - Gate #2 compliance validated

4. ✅ **User Can Complete Goal**
   - Accept a goal
   - Break down into atomic blocks
   - Create 5-block plan
   - Complete blocks
   - Receive rewards
   - Track momentum

5. ✅ **Non-Exploitative Design**
   - 5-Block Stop rule enforced
   - No dark patterns
   - Pride-based (not fear/shame)
   - Passes Gate #2 validation

---

## Estimated Implementation

**Total Lines**: ~1,500 lines (Phase 5.1 MVP)

| Component | Lines | Complexity |
|-----------|-------|------------|
| GoalIngestor | 100 | Low |
| ScopingAgent | 200 | Medium |
| TimeBlockManager | 150 | Medium |
| StrengthAmplifier (basic) | 100 | Low |
| GrowthScaffold (basic) | 120 | Medium |
| RewardEmitter | 80 | Low |
| MomentumLoopOrchestrator | 250 | High |
| FractalFlowEngine | 150 | Medium |
| Integration | 100 | Low |
| Tests | 250 | Medium |
| **Total** | **~1,500** | |

**Estimated Time**: 4-6 hours for MVP (with AI assistance)

---

## Next Steps

1. ✅ Review this plan
2. 🚧 Create `components/` directory
3. 🚧 Implement GoalIngestor (start simple)
4. Continue with priority order above

---

**Plan Status**: READY FOR IMPLEMENTATION
