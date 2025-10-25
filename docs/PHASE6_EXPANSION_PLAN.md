# Phase 6: User-Facing "Light Pattern" Interfaces

**Status:** Planning
**FFE Version:** V3.0
**Phase:** Expansion (Post-MVP)
**Owner:** FFE Core Team

---

## Overview

Phase 6 implements the **user-facing "light pattern" interfaces** that sit on top of the FFE V3.0 backend engine (completed in Phase 5). These interfaces replace "dark patterns" with psychology-based engagement systems that build genuine competence, autonomy, and meaning.

**Backend (Phase 5):** ✅ Complete
- All 7 core modules operational
- Momentum Loop functioning
- 80/20 Scoping working
- 5-Block Stop enforced

**Frontend (Phase 6):** 🔨 This Phase
- 5 user-facing interfaces
- Visualization and interaction layer
- Non-extractive engagement patterns

---

## Architecture: Backend Powers Frontend

The V3.0 spec clarifies that **user-facing interfaces are powered by backend modules**. Each interface is a view/interaction layer over the existing engine components.

| Frontend Interface | Backend Modules That Power It |
|-------------------|-------------------------------|
| **1. Signature Strength Amplifier** | StrengthAmplifier (engine) + RewardEmitter |
| **2. Progress Tapestry** | RewardEmitter + TimeBlockManager |
| **3. Narrative Arc Engine** | GoalIngestor + PersonalityModule + Epic Meaning Module (new) |
| **4. Protégé Pipeline** | GoalIngestor + ScopingAgent + GrowthScaffold |
| **5. Curiosity Compass** | GrowthScaffold + ScopingAgent |
| **6. Social Relatedness** *(expansion)* | RewardEmitter + Social Module (new) |

---

## Phase 6 Components

### 6.1 Signature Strength Amplifier (Interface Layer)

**Status:** Partially Complete (backend exists, needs UI)

**Purpose:** User-facing reframing tool and reward display

**Backend (✅ Complete):**
- `strength_amplifier.py` - Task reframing logic
- `reward_emitter.py` - Identity-affirming rewards
- 10 strength types with templates

**Frontend (🔨 New Work):**
- Interactive reframing UI
- Reward message display
- Strength selection/confirmation

**Files to Create:**
```
src/ai_pal/ffe/interfaces/
├── strength_interface.py      # User interaction layer
└── __init__.py
```

**API Methods:**
```python
async def present_task_reframe(user_id: str, task: str, strengths: List[SignatureStrength]) -> str:
    """Show user how their strength reframes a task"""

async def display_reward(user_id: str, reward: RewardMessage) -> None:
    """Display identity-affirming reward to user"""

async def select_strength(user_id: str, task: str) -> SignatureStrength:
    """Let user choose which strength to apply"""
```

**Estimated Effort:** 150 lines

---

### 6.2 Progress Tapestry

**Status:** New Component

**Purpose:** Visualize earned wins (not a to-do list!)

**Backend Powered By:**
- `reward_emitter.py` - Provides the "wins" to visualize
- `time_block_manager.py` - Provides atomic block structure
- `momentum_loop.py` - Tracks cycle completions

**Frontend (🔨 New Work):**
- Visual timeline of completed blocks
- Pride intensity visualization
- Cycle/loop completion tracking
- "Tapestry" metaphor: each win is a thread

**Files to Create:**
```
src/ai_pal/ffe/interfaces/
├── progress_tapestry.py       # Visualization engine
└── models/tapestry.py         # Data structures
```

**Data Model:**
```python
@dataclass
class TapestryView:
    """Visual representation of user's earned wins"""
    user_id: str
    completed_blocks: List[AtomicBlock]  # All completed blocks
    reward_messages: List[RewardMessage]  # All rewards earned
    momentum_cycles: List[MomentumLoopState]  # All completed loops

    # Visualization data
    timeline_data: Dict[str, Any]  # Time-series of wins
    strength_distribution: Dict[StrengthType, int]  # Which strengths used most
    pride_trend: List[float]  # Pride intensity over time
```

**API Methods:**
```python
async def render_tapestry(user_id: str, lookback_days: int = 30) -> TapestryView:
    """Generate tapestry visualization data"""

async def add_win_to_tapestry(user_id: str, block: AtomicBlock, reward: RewardMessage) -> None:
    """Add new win to user's tapestry"""

async def get_tapestry_stats(user_id: str) -> Dict[str, Any]:
    """Get summary statistics for display"""
```

**Estimated Effort:** 200 lines

---

### 6.3 Narrative Arc Engine (Epic Meaning Module)

**Status:** New Component

**Purpose:** Connect small wins to big-picture values and life goals

**Backend Powered By:**
- `goal_ingestor.py` - Defines the quest
- `PersonalityModule` - Provides user's core values
- **Epic Meaning Module** (new) - Links blocks to values

**Frontend (🔨 New Work):**
- Value-to-task connection display
- "Quest narrative" generation
- Progress toward life goals

**Files to Create:**
```
src/ai_pal/ffe/modules/
├── epic_meaning.py            # Epic Meaning Module
└── __init__.py

src/ai_pal/ffe/interfaces/
├── narrative_interface.py     # Narrative display
```

**Data Model:**
```python
@dataclass
class NarrativeArc:
    """Epic narrative connecting wins to values"""
    user_id: str
    core_value: str  # e.g., "Community"
    life_goal: str   # e.g., "Build app for community"

    # Connected wins
    contributing_blocks: List[AtomicBlock]
    narrative_text: str  # Generated story

    # Progress
    progress_toward_goal: float  # 0-1
    meaning_intensity: float     # 0-1
```

**API Methods:**
```python
async def generate_narrative(user_id: str, block: AtomicBlock) -> MeaningNarrative:
    """Generate epic meaning connection for completed block"""

async def show_quest_progress(user_id: str, life_goal: str) -> NarrativeArc:
    """Display progress toward big-picture goal"""

async def link_block_to_value(block: AtomicBlock, value: str) -> str:
    """Create narrative linking atomic win to core value"""
```

**Estimated Effort:** 250 lines (module) + 150 lines (interface) = 400 lines

---

### 6.4 Protégé Pipeline (Learn-by-Teaching Mode)

**Status:** New Component

**Purpose:** Reframe "learning" as "teaching" to boost engagement

**Backend Powered By:**
- `goal_ingestor.py` - Sets task as "Teach me X"
- `scoping_agent.py` - Breaks teaching into atomic explanations
- `growth_scaffold.py` - Detects weak areas, asks user to "teach" them

**Frontend (🔨 New Work):**
- Teaching interface
- Explanation capture
- "Student AI" persona

**Files to Create:**
```
src/ai_pal/ffe/modules/
├── protege_pipeline.py        # Teaching mode logic
└── __init__.py

src/ai_pal/ffe/interfaces/
├── teaching_interface.py      # Teaching UI
```

**Data Model:**
```python
@dataclass
class TeachingSession:
    """Learn-by-teaching session"""
    session_id: str
    user_id: str
    subject: str  # What user is "teaching"

    # Teaching blocks
    explanation_blocks: List[AtomicBlock]
    concepts_explained: List[str]

    # "Student AI" feedback
    understanding_level: float  # How well "student" understood
    follow_up_questions: List[str]
```

**API Methods:**
```python
async def start_teaching_mode(user_id: str, subject: str) -> TeachingSession:
    """Start learn-by-teaching session"""

async def request_explanation(user_id: str, concept: str) -> AtomicBlock:
    """Ask user to teach a concept"""

async def provide_student_feedback(user_id: str, explanation: str) -> str:
    """AI "student" responds to teaching"""
```

**Estimated Effort:** 300 lines (module) + 150 lines (interface) = 450 lines

---

### 6.5 Curiosity Compass (Opportunity Discovery)

**Status:** New Component

**Purpose:** Turn bottleneck queue into "map of curiosities"

**Backend Powered By:**
- `growth_scaffold.py` - Bottleneck queue exposed as curiosities
- `scoping_agent.py` - Reframes bottlenecks as 15-min explorations

**Frontend (🔨 New Work):**
- Exploration mode interface
- Low-stakes framing ("just 15 minutes to explore")
- Discovery tracking

**Files to Create:**
```
src/ai_pal/ffe/interfaces/
├── curiosity_compass.py       # Exploration interface
└── models/compass.py          # Data structures
```

**Data Model:**
```python
@dataclass
class CuriosityMap:
    """Map of exploration opportunities"""
    user_id: str

    # Opportunities (bottlenecks reframed)
    unexplored_areas: List[BottleneckTask]
    exploration_suggestions: List[Dict[str, Any]]

    # Low-stakes framing
    fifteen_min_explorations: List[AtomicBlock]

    # Discovery tracking
    explored_count: int
    discoveries_made: List[str]
```

**API Methods:**
```python
async def show_curiosity_map(user_id: str) -> CuriosityMap:
    """Display map of unexplored opportunities"""

async def suggest_exploration(user_id: str) -> AtomicBlock:
    """Suggest low-stakes 15-min exploration"""

async def record_discovery(user_id: str, bottleneck_id: str, discovery: str) -> None:
    """User made a discovery during exploration"""
```

**Estimated Effort:** 250 lines

---

### 6.6 Social Relatedness (Expansion Module)

**Status:** New Component (Optional Expansion)

**Purpose:** Share earned wins with user-defined groups

**Backend Powered By:**
- `reward_emitter.py` - Provides wins to share
- **Social Relatedness Module** (new) - Handles group connections

**Frontend (🔨 New Work):**
- Win sharing interface
- Group management
- Privacy controls

**Files to Create:**
```
src/ai_pal/ffe/modules/
├── social_relatedness.py      # Social module
└── __init__.py

src/ai_pal/ffe/interfaces/
├── social_interface.py        # Sharing UI
```

**Data Model:**
```python
@dataclass
class SocialGroup:
    """User-defined social group"""
    group_id: str
    group_name: str
    members: List[str]  # User-controlled membership

@dataclass
class WinShare:
    """Shared win"""
    share_id: str
    user_id: str
    block_id: str
    shared_with: List[str]  # Group IDs

    # Non-coercive requirement
    user_initiated: bool = True
    privacy_level: str = "group_only"
```

**API Methods:**
```python
async def share_win(user_id: str, block: AtomicBlock, groups: List[str]) -> WinShare:
    """Share earned win with groups (user-initiated only!)"""

async def create_group(user_id: str, group_name: str, members: List[str]) -> SocialGroup:
    """Create user-defined social group"""

async def get_group_feed(group_id: str) -> List[WinShare]:
    """Get shared wins for a group"""
```

**Estimated Effort:** 300 lines (module) + 200 lines (interface) = 500 lines

---

## Implementation Strategy

### Phase 6.1: Core Interfaces (Priority 1)

**Implement first (required for basic UX):**
1. ✅ Signature Strength Amplifier (interface layer)
2. ✅ Progress Tapestry
3. ✅ Narrative Arc Engine

**Estimated:** ~750 lines
**Timeline:** Implement alongside Tasks 1-2 (integration & testing)

### Phase 6.2: Advanced Modes (Priority 2)

**Implement second (enhance engagement):**
4. ✅ Protégé Pipeline
5. ✅ Curiosity Compass

**Estimated:** ~700 lines
**Timeline:** After basic integration testing

### Phase 6.3: Social Expansion (Priority 3)

**Implement last (optional expansion):**
6. ✅ Social Relatedness

**Estimated:** ~500 lines
**Timeline:** Optional post-MVP

---

## File Structure (Phase 6)

```
src/ai_pal/ffe/
├── engine.py                       # ✅ Phase 5 (complete)
├── components/                     # ✅ Phase 5 (complete)
│   ├── goal_ingestor.py
│   ├── reward_emitter.py
│   ├── time_block_manager.py
│   ├── scoping_agent.py
│   ├── strength_amplifier.py
│   ├── growth_scaffold.py
│   └── momentum_loop.py
├── modules/                        # 🔨 Phase 6 (new)
│   ├── __init__.py
│   ├── epic_meaning.py             # Narrative Arc backend
│   ├── protege_pipeline.py         # Teaching mode backend
│   └── social_relatedness.py       # Social backend
├── interfaces/                     # 🔨 Phase 6 (new)
│   ├── __init__.py
│   ├── strength_interface.py       # Strength UI
│   ├── progress_tapestry.py        # Tapestry visualization
│   ├── narrative_interface.py      # Narrative display
│   ├── teaching_interface.py       # Teaching UI
│   ├── curiosity_compass.py        # Exploration UI
│   └── social_interface.py         # Sharing UI
└── models/                         # 🔨 Phase 6 (extend)
    ├── tapestry.py                 # Tapestry models
    └── compass.py                  # Compass models
```

**Total Estimated Code:** ~1,950 lines (Priority 1-3 combined)

---

## Success Criteria

### Functional Requirements

**Each interface must:**
1. ✅ Connect to existing backend modules (no duplication)
2. ✅ Provide clear user interaction patterns
3. ✅ Display data in non-extractive ways
4. ✅ Build genuine competence/autonomy/meaning
5. ✅ Pass Gate #2 (Humanity Gate) validation

### Non-Extractive Requirements

**Each interface must NOT:**
1. ❌ Use shame/fear/FOMO
2. ❌ Coerce user actions
3. ❌ Hide user control
4. ❌ Extract engagement without building skills
5. ❌ Violate 5-Block Stop rule

### Integration Requirements

1. ✅ Works with IntegratedACSystem
2. ✅ Uses PersonalityModule for personalization
3. ✅ Reports to AgencyDashboard
4. ✅ Respects ARI thresholds
5. ✅ Compatible with Phase 1-3 components

---

## Testing Strategy

### Unit Tests (per interface)

```python
# Example test structure
async def test_progress_tapestry_render():
    """Test tapestry visualization generation"""

async def test_narrative_arc_generation():
    """Test epic meaning connection"""

async def test_protege_teaching_session():
    """Test learn-by-teaching mode"""

async def test_curiosity_compass_suggestions():
    """Test exploration opportunity discovery"""
```

### Integration Tests

```python
async def test_strength_interface_with_ffe():
    """Test strength interface integrated with full FFE"""

async def test_tapestry_with_real_workflow():
    """Test tapestry with actual momentum loop"""
```

### E2E Tests

```python
async def test_complete_user_journey():
    """
    Full user journey:
    1. Start goal
    2. Complete blocks
    3. View tapestry
    4. See narrative arc
    5. Enter teaching mode
    6. Explore curiosity
    """
```

---

## Dependencies

### Internal (AC-AI Framework)

- ✅ Phase 1: Gateway System (Gate #2 validation)
- ✅ Phase 2: ARI Monitor (Bottleneck detection)
- ✅ Phase 3: Personality Module (Values, strengths)
- ✅ Phase 5: FFE Backend (All 7 core modules)

### External Libraries

- `matplotlib` or `plotly` (for Progress Tapestry visualization)
- `rich` (for CLI visualization)
- Standard library only for other interfaces

---

## Next Steps

**Immediate (with Task 1-2):**
1. Create `interfaces/` directory structure
2. Implement Priority 1 interfaces (Strength, Tapestry, Narrative)
3. Test alongside FFE integration

**After Integration (Task 4):**
4. Implement Priority 2 interfaces (Protégé, Compass)
5. Add E2E tests
6. Performance optimization

**Optional Expansion:**
7. Implement Social Relatedness module
8. Add advanced visualizations
9. Mobile/web interface layers

---

## Notes

**Key Insight from V3.0 Spec:**

The user-facing interfaces are NOT separate systems. They are **views and interaction layers** powered by the existing backend modules. This means:

- No duplicated logic
- Clean separation of concerns
- Easy to add new interfaces later
- Backend changes automatically propagate

**Architecture Pattern:**

```
User <--> Interface Layer <--> Backend Modules <--> Data Storage
         (Phase 6)           (Phase 5)
```

This design ensures the FFE remains maintainable, testable, and extensible.

---

**Document Version:** 1.0
**Last Updated:** Phase 6 Planning (Post Phase 5 MVP Completion)
**Status:** Ready for Implementation
