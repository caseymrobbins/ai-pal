# Socratic Features: Learn About Me & Socratic Co-pilot

**Status:** ✅ Complete (as of 2025-10-26)

## Overview

Two complementary features for accurate ARI (Agency Retention Index) measurement through intelligent user engagement:

1. **Learn About Me (Deep Dive Mode)**: Opt-in Socratic dialogue for deep skill profiling
2. **Socratic Co-pilot**: Embedded capability assessment during normal assistance

Both features measure user capability without deskilling, providing "gold standard" measurements for ARI-Synthesis and ARI-Knowledge while respecting user agency.

---

## Feature 1: Learn About Me (Deep Dive Mode)

### User-Facing Name
"Learn About Me Mode" or "Deep Dive" Mode

### Core Principle (User Value)
**"Your Cognitive Release Valve."**

An opt-in space for users who want to be challenged, understood, and explore complex ideas with a true cognitive partner.

### Primary Function (System Goal)
Build a deep, accurate profile of the user's:
- Knowledge domains
- Synthesis skills
- Logical reasoning style

Provides the "gold standard" measurement for **ARI-Synthesis** and **ARI-Knowledge**.

### Architecture

```
User Opts In
    ↓
Start Deep Dive Session
    ↓
Generate Socratic Question (adapted to level)
    ↓
User Responds
    ↓
Grade Response (Accuracy, Logic, Completeness)
    ↓
┌────────────┴────────────┐
│  Response Quality       │
├─────────────────────────┤
│ Excellent/Proficient    │ → Validate + Increase Difficulty
│ Developing              │ → Feedback + Same Level
│ Struggling              │ → Offer Scaffold/Hint
│ Insufficient            │ → Decrease Difficulty or Exit
└─────────────────────────┘
    ↓
Update Knowledge Profile
    ↓
Record ARI-Synthesis Snapshot
    ↓
Continue or Exit (User Control)
```

### Key Features

#### 1. User-Initiated Opt-In
- Never active by default
- Explicit trigger required (e.g., "Deep Dive" button)
- User must consciously choose to be challenged

#### 2. Adaptive Scaffolding
- Starts at basics, moves toward mastery
- 5 difficulty levels: Basic → Intermediate → Advanced → Expert → Mastery
- Adaptive progression based on performance

#### 3. ARI-Synthesis Grading
Uses three-dimensional rubric:
- **Accuracy** (0-1): Is the reasoning logically correct?
- **Logic** (0-1): Does the chain of reasoning hold up?
- **Completeness** (0-1): Did they address all key aspects?

Overall score = 0.35×Accuracy + 0.35×Logic + 0.30×Completeness

Quality mapping:
- ≥0.85: Excellent
- 0.70-0.84: Proficient
- 0.50-0.69: Developing
- 0.30-0.49: Struggling
- <0.30: Insufficient

#### 4. Rewarding Engagement

**On Success (Excellent/Proficient):**
- AI validates the user's insight
- Presents next, more complex challenge
- Feels highly rewarding

**On Struggle (Developing/Struggling):**
- AI offers scaffold (hint or simpler question)
- Prevents frustration
- Maintains engagement

#### 5. Profile Update
- Validated skill ceiling recorded
- Synthesis metrics tracked over time
- Stored in long-term user model (EnhancedContextManager)
- Adapts to user's level in all future interactions

#### 6. User Control

**Full Opt-In:**
- User never in this mode by default
- Explicit activation required

**Off-Ramp:**
- Persistent "Switch to regular chat" button
- "Just give me the answer" option available anytime
- User can disengage at will

**Humanity Override:**
- User can appeal AI's grade
- Prevents "AI-as-grader" chokepoints
- Re-evaluation with human oversight flag

### Usage Example

```python
from ai_pal.ffe.interfaces import LearnAboutMeInterface

# Initialize interface
learn_about_me = LearnAboutMeInterface(
    ari_monitor=ari_monitor,
    context_manager=context_manager,
    orchestrator=orchestrator,
)

# User opts in
session = await learn_about_me.start_deep_dive(
    user_id="user123",
    domain="machine_learning"
)

# Get Socratic question
question = await learn_about_me.get_next_question("user123")
print(question.question_text)
# "What are the fundamental principles that make gradient descent work?"

# User responds
response = await learn_about_me.submit_response(
    user_id="user123",
    question_id=question.question_id,
    response_text="Gradient descent works by iteratively moving in the direction..."
)

# Check assessment
print(f"Quality: {response.rubric.quality.value}")
print(f"Overall score: {response.rubric.overall_score:.2f}")
print(f"Feedback: {response.ai_feedback}")
print(f"Validation: {response.validation}")

# If struggling, request scaffold
if response.rubric.quality == ResponseQuality.STRUGGLING:
    scaffold = await learn_about_me.request_scaffold("user123", question.question_id)
    print(f"Hint: {scaffold['hint']}")

# Exit when done
summary = await learn_about_me.exit_deep_dive(
    user_id="user123",
    reason="User requested exit"
)
print(f"Skill ceiling: {summary['skill_ceiling_score']:.2f}")
print(f"Highest difficulty: {summary['highest_difficulty_reached']}")
```

### Data Models

#### DeepDiveSession
```python
@dataclass
class DeepDiveSession:
    session_id: str
    user_id: str
    domain: str  # "machine_learning", "philosophy", etc.

    current_difficulty: DifficultyLevel
    questions_asked: List[SocraticQuestion]
    responses_given: List[SocraticResponse]

    highest_difficulty_achieved: DifficultyLevel
    skill_ceiling_score: float  # 0-1

    active: bool
    user_requested_exit: bool
```

#### SynthesisRubric
```python
@dataclass
class SynthesisRubric:
    accuracy_score: float  # 0-1
    logic_score: float     # 0-1
    completeness_score: float  # 0-1

    @property
    def overall_score(self) -> float

    @property
    def quality(self) -> ResponseQuality
```

#### KnowledgeProfile
```python
@dataclass
class KnowledgeProfile:
    user_id: str
    domain: str

    validated_difficulty_level: DifficultyLevel
    skill_ceiling: float

    # Synthesis metrics
    synthesis_avg_accuracy: float
    synthesis_avg_logic: float
    synthesis_avg_completeness: float

    # Engagement
    total_sessions: int
    total_questions_answered: int
    confidence_score: float  # 0-1, increases with more data
```

---

## Feature 2: Socratic Co-pilot (Embedded Assessment)

### User-Facing Name
"Socratic Co-pilot" or "Embedded Assessment"

### Core Principle (User Value)
**"Assistance without Deskilling."**

The AI acts as a "co-pilot" that helps complete tasks without deskilling the user by doing everything for them.

### Primary Function (System Goal)
Accurately measure **ARI-Capability** during standard assistive requests by identifying **Unassisted Capability Checkpoints (UCCs)** and probing user knowledge at delegation points.

Solves the "Convenience vs. Capability" problem by forcing user to reveal unassisted skill at the moment of delegation.

### Architecture

```
User Makes Request
    ↓
Identify Task Category (code/writing/analysis/etc.)
    ↓
Identify Unassisted Capability Checkpoints (UCCs)
    ↓
For Each Checkpoint:
    ↓
Generate Probe (clarifying question)
    ↓
Present to User
    ↓
User Response
    ↓
┌────────────────┴────────────────┐
│   Response Type                 │
├─────────────────────────────────┤
│ Provided Answer                 │ → HIGH ARI (has capability)
│ "Just guess" / "I don't know"   │ → LOW ARI (capability gap)
│ Asked for clarification         │ → PARTIAL (some capability)
└─────────────────────────────────┘
    ↓
Record Checkpoint Response
    ↓
Complete Task Using:
- User's provided answers
- AI's best guesses for delegated parts
    ↓
Record ARI-Capability Snapshot
    ↓
Track Capability Gaps in Context
```

### Key Features

#### 1. Standard Request Flow
- Integrates seamlessly into normal assistance
- No special mode activation needed
- Feels like helpful clarification, not a test

#### 2. Unassisted Capability Checkpoints (UCCs)
Identifies "fundamental parts" or key variables:

**For coding tasks:**
- Function/variable names
- Core algorithm logic
- Data structure choices

**For writing tasks:**
- Key points to communicate
- Target audience
- Tone/style

**For analysis tasks:**
- Methodology choices
- Key metrics to track
- Interpretation approach

#### 3. Embedded Probes
Low-friction clarifying questions:

Example (Code):
- "What should I name the main function?"
- "What's the specific logic for the if statement?"

Example (Writing):
- "What are the 3 key bullet points you want to communicate?"
- "Who is the target audience?"

#### 4. ARI Measurement

**High ARI (Convenience):**
- User provides answers quickly and accurately
- Logs as HIGH ARI data point
- User has the skill

**Low ARI (Inability):**
- User says "I don't know", "Just guess", "You do it"
- Logs as LOW ARI data point
- Capability gap detected

#### 5. Low Friction
- Not a "test" - feels like normal workflow
- Clarifying questions are genuinely helpful
- AI completes task either way

#### 6. Implicit Override
- User's "just guess" response IS the override
- Respects agency to prioritize convenience
- Still provides vital LOW ARI signal to system

### Usage Example

```python
from ai_pal.ffe.interfaces import SocraticCopilotInterface

# Initialize interface
copilot = SocraticCopilotInterface(
    ari_monitor=ari_monitor,
    context_manager=context_manager,
    orchestrator=orchestrator,
)

# User makes normal request
copilot_request = await copilot.process_request(
    user_id="user123",
    request="Write a Python script to parse this CSV file",
    session_id="session_abc"
)

print(f"Identified {len(copilot_request.checkpoints)} checkpoints")

# Get probes for user
probe = await copilot.get_next_probe(copilot_request.request_id)
print(f"Question: {probe.question}")
# "What should I name the main function?"

# User responds
response = await copilot.submit_checkpoint_response(
    request_id=copilot_request.request_id,
    checkpoint_id=probe.checkpoint_id,
    response_text="parse_csv_file"
)

# Check capability
if response.demonstrated_capability:
    print("HIGH ARI: User has capability")
else:
    print("LOW ARI: Capability gap")

# Get next probe
probe2 = await copilot.get_next_probe(copilot_request.request_id)
print(f"Question: {probe2.question}")
# "What's the specific logic for filtering the data?"

# User delegates
response2 = await copilot.submit_checkpoint_response(
    request_id=copilot_request.request_id,
    checkpoint_id=probe2.checkpoint_id,
    response_text="I don't know, just guess"
)
print(f"Delegated: {not response2.demonstrated_capability}")

# Complete task
result = await copilot.complete_request(copilot_request.request_id)
print(f"Final output:\n{result['final_output']}")
print(f"ARI score: {result['ari_score']:.2f}")
print(f"High ARI count: {result['high_ari_count']}")
print(f"Low ARI count: {result['low_ari_count']}")
```

### Data Models

#### CopilotRequest
```python
@dataclass
class CopilotRequest:
    request_id: str
    user_id: str
    original_request: str
    task_category: str  # "code", "writing", "analysis"

    checkpoints: List[UnassistedCapabilityCheckpoint]
    responses: List[CheckpointResponseData]
    current_checkpoint_index: int

    # ARI measurement
    high_ari_count: int  # Number of provided answers
    low_ari_count: int   # Number of delegated answers
    overall_ari_score: float  # 0-1

    final_output: Optional[str]
    completed: bool
```

#### UnassistedCapabilityCheckpoint
```python
@dataclass
class UnassistedCapabilityCheckpoint:
    checkpoint_id: str
    checkpoint_type: CheckpointType  # PARAMETER, LOGIC, STRUCTURE, CONTENT, DESIGN
    probe_question: str
    context: Optional[str]
    expected_knowledge_level: float  # 0-1
```

#### CheckpointResponseData
```python
@dataclass
class CheckpointResponseData:
    checkpoint_id: str
    response_type: CheckpointResponse  # PROVIDED, DELEGATED, PARTIAL, CLARIFIED
    response_text: Optional[str]

    demonstrated_capability: bool
    capability_score: float  # 0-1
```

---

## Integration with ARI Monitoring

### ARI Snapshot Recording

Both features record ARI snapshots with specialized metadata:

#### Learn About Me (ARI-Synthesis):
```python
AgencySnapshot(
    task_type="deep_dive_{domain}",
    delta_agency=0.1,  # Positive if excellent/proficient
    skill_development=max(0, new_score - previous_ceiling),
    ai_reliance=0.2,  # Low - user doing synthesis themselves
    autonomy_retention=0.95,  # High - full user control
    metadata={
        "mode": "deep_dive",
        "domain": domain,
        "difficulty": difficulty_level,
        "synthesis_accuracy": rubric.accuracy_score,
        "synthesis_logic": rubric.logic_score,
        "synthesis_completeness": rubric.completeness_score,
    }
)
```

#### Socratic Co-pilot (ARI-Capability):
```python
AgencySnapshot(
    task_type="copilot_{task_category}",
    delta_agency=ari_score - 0.5,  # Positive if demonstrated capability
    ai_reliance=1.0 - ari_score,  # High ARI = low reliance
    autonomy_retention=ari_score,  # High if user provided answers
    metadata={
        "mode": "copilot",
        "task_category": task_category,
        "high_ari_count": high_count,
        "low_ari_count": low_count,
        "total_checkpoints": total,
    }
)
```

---

## Synergies Between Features

### 1. Deep Dive → Co-pilot
**Flow**: Establish baseline → Measure application

1. User does Deep Dive in "Python" domain
2. System records skill ceiling: 0.85 (Advanced level)
3. Later, user requests Python assistance via Co-pilot
4. Co-pilot can adjust checkpoint difficulty based on known skill ceiling
5. Measures whether user can apply their knowledge in practice

### 2. Co-pilot → Deep Dive
**Flow**: Identify gaps → Fill gaps

1. User requests coding assistance
2. Co-pilot detects capability gaps (multiple "just guess" responses)
3. System suggests: "Want to learn this? Try Deep Dive mode"
4. User opts into Deep Dive for targeted learning
5. Gaps get filled through Socratic dialogue

### 3. Continuous Feedback Loop

```
Co-pilot identifies gaps
    ↓
System recommends Deep Dive
    ↓
User builds skills in Deep Dive
    ↓
Co-pilot measures improved capability
    ↓
Repeat
```

---

## Configuration

### Deep Dive Settings

```python
learn_about_me = LearnAboutMeInterface(
    ari_monitor=ari_monitor,
    context_manager=context_manager,
    orchestrator=orchestrator,
)

# Difficulty progression thresholds
# (built into assessment logic)
EXCELLENT_THRESHOLD = 0.85  # Advance to next level
PROFICIENT_THRESHOLD = 0.70  # Maintain level
DEVELOPING_THRESHOLD = 0.50  # Provide scaffolding
STRUGGLING_THRESHOLD = 0.30  # Simplify or offer exit
```

### Co-pilot Settings

```python
copilot = SocraticCopilotInterface(
    ari_monitor=ari_monitor,
    context_manager=context_manager,
    orchestrator=orchestrator,
)

# Checkpoint identification
# - 2-4 checkpoints per request (typical)
# - Focuses on "fundamental parts" not trivial details

# Delegation detection phrases
DELEGATION_PHRASES = [
    "just guess",
    "you decide",
    "you do it",
    "i don't know",
    "not sure",
    "whatever you think",
    "up to you",
]
```

---

## Testing

Comprehensive tests available in `tests/integration/test_socratic_features.py`:

```bash
# Run all Socratic feature tests
pytest tests/integration/test_socratic_features.py -v

# Test Learn About Me only
pytest tests/integration/test_socratic_features.py -k "deep_dive" -v

# Test Socratic Co-pilot only
pytest tests/integration/test_socratic_features.py -k "copilot" -v

# Test integration between both
pytest tests/integration/test_socratic_features.py::test_deep_dive_then_copilot -v
```

### Test Coverage:
- ✅ Learn About Me: 10 tests
  - Session lifecycle
  - Question generation
  - Response grading
  - Difficulty progression
  - Scaffolding
  - Profile storage
  - ARI recording
  - Grade appeals
- ✅ Socratic Co-pilot: 10 tests
  - Request processing
  - Checkpoint probes
  - High/Low ARI responses
  - Mixed responses
  - Completion workflow
  - ARI recording
  - Gap tracking
  - Capability profiles
- ✅ Integration: 2 tests
  - Deep Dive → Co-pilot flow
  - Co-pilot → Deep Dive flow

---

## Performance Considerations

### Learn About Me
- **Frequency**: Opt-in only (low frequency)
- **Cost**: Moderate (AI question generation + grading)
- **Latency**: ~2-3 seconds per question/response cycle
- **Storage**: Knowledge profiles stored as MemoryEntry in context manager

### Socratic Co-pilot
- **Frequency**: Every assistive request (high frequency)
- **Cost**: Moderate (checkpoint identification + completion)
- **Latency**: +5-10 seconds total (distributed across probes)
- **User perception**: Feels like normal clarification workflow

### Optimizations
1. **Cache common checkpoints** for similar requests
2. **Batch probe generation** when multiple similar requests detected
3. **Use faster models** for checkpoint identification (TaskComplexity.TRIVIAL)
4. **Parallel processing** of probe generation and grading

---

## Privacy & Ethics

### Consent
- **Deep Dive**: Explicit opt-in required
- **Co-pilot**: Implicit consent (part of normal workflow)
- Both features log ARI data with user's knowledge

### Humanity Override
- **Deep Dive**: Users can appeal grades
- **Co-pilot**: "Just guess" IS the override
- No AI chokepoints - user always has final say

### Data Retention
- Knowledge profiles: Stored indefinitely (user benefit)
- Capability gaps: Stored for improvement suggestions
- ARI snapshots: Standard ARI retention policy (90 days)

### Transparency
- Users always know when in Deep Dive mode
- Co-pilot probes clearly framed as clarifying questions
- ARI measurement disclosed in system documentation

---

## Future Enhancements

### Planned Features

1. **Domain Recommendations**
   - AI suggests domains for Deep Dive based on Co-pilot gaps
   - "You've delegated 5 SQL tasks - want to learn SQL?"

2. **Difficulty Auto-Adjustment**
   - Co-pilot adjusts checkpoint difficulty based on Deep Dive profile
   - Personalized probe complexity

3. **Progress Visualization**
   - Dashboard showing skill ceilings across domains
   - Capability gap heat map
   - Learning trajectory over time

4. **Social Learning**
   - Compare skill profiles with peers (anonymized)
   - Group Deep Dive sessions
   - Collaborative problem-solving

5. **Micro-Learning Integration**
   - Generate micro-lessons for identified gaps
   - Bite-sized Deep Dive sessions (5-10 min)
   - Mobile-optimized interface

---

## Troubleshooting

### Common Issues

**Q: Deep Dive not progressing difficulty?**

A: Check that:
1. Response quality consistently excellent (≥0.85 score)
2. Multiple responses submitted (need pattern of excellence)
3. User hasn't already reached Mastery level

**Q: Co-pilot creating too many checkpoints?**

A: Adjust checkpoint identification prompt to focus on "fundamental parts" only. Typical: 2-4 checkpoints per request.

**Q: Users feel like they're being "tested"?**

A: Ensure:
1. Probe language is friendly and curious, not evaluative
2. "Just guess" option clearly presented
3. Task completed regardless of responses
4. Frame as "clarification" not "assessment"

**Q: ARI snapshots not recording?**

A: Verify:
1. ARI monitor properly initialized
2. Sessions completed (not abandoned mid-stream)
3. Response assessment completing without errors

---

## API Reference

### LearnAboutMeInterface

```python
async def start_deep_dive(user_id: str, domain: str) -> DeepDiveSession
async def get_next_question(user_id: str) -> SocraticQuestion
async def submit_response(user_id: str, question_id: str, response_text: str) -> SocraticResponse
async def request_scaffold(user_id: str, question_id: str) -> Dict[str, Any]
async def exit_deep_dive(user_id: str, reason: Optional[str] = None) -> Dict[str, Any]
async def appeal_grade(user_id: str, response_id: str, appeal_reason: str) -> Dict[str, Any]
async def get_knowledge_profile(user_id: str, domain: str) -> Optional[KnowledgeProfile]
```

### SocraticCopilotInterface

```python
async def process_request(user_id: str, request: str, session_id: str) -> CopilotRequest
async def get_next_probe(request_id: str) -> Optional[CopilotProbe]
async def submit_checkpoint_response(request_id: str, checkpoint_id: str, response_text: str) -> CheckpointResponseData
async def complete_request(request_id: str) -> Dict[str, Any]
async def get_capability_profile(user_id: str, task_category: str) -> Dict[str, Any]
```

---

## Contributing

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

When contributing to Socratic features:
- Maintain low-friction UX for Co-pilot
- Preserve user agency (opt-in, overrides)
- Add tests for new question types or checkpoint logic
- Update this documentation
- Consider privacy implications

---

## License

See [LICENSE](../LICENSE)

---

**Last Updated:** 2025-10-26
**Version:** 1.0.0
**Status:** Production Ready
