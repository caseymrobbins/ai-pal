# AI-PAL API Reference

Complete API reference for AI-PAL system components.

## Table of Contents

1. [Core System API](#core-system-api)
2. [Fractal Flow Engine (FFE) API](#fractal-flow-engine-ffe-api)
3. [Agency Retention Index (ARI) API](#agency-retention-index-ari-api)
4. [Epistemic Debt Management (EDM) API](#epistemic-debt-management-edm-api)
5. [Four Gates API](#four-gates-api)
6. [Plugin System API](#plugin-system-api)
7. [Model Orchestration API](#model-orchestration-api)
8. [Security API](#security-api)
9. [Monitoring & Metrics API](#monitoring--metrics-api)
10. [HTTP REST API](#http-rest-api)

---

## Core System API

### IntegratedACSystem

The main orchestrator for all AI-PAL functionality.

#### Class: `IntegratedACSystem`

```python
from ai_pal.core.integrated_system import IntegratedACSystem, ACConfig

class IntegratedACSystem:
    """
    Integrated Agency Calculus System.

    Coordinates all components: Gates, ARI, EDM, FFE, Model Orchestration.
    """
```

#### Configuration

```python
@dataclass
class ACConfig:
    """Configuration for IntegratedACSystem"""

    # Four Gates Configuration
    enable_four_gates: bool = True
    min_agency_delta: float = 0.0
    max_epistemic_debt: float = 0.3
    min_bhir: float = 1.0
    max_goodhart_divergence: float = 0.2

    # Component Enablement
    enable_ari_monitoring: bool = True
    enable_edm_monitoring: bool = True
    enable_ffe: bool = True

    # Model Configuration
    default_model: str = "anthropic/claude-3-5-sonnet"
    enable_multi_model: bool = True

    # Security
    enable_pii_scrubbing: bool = True
    enable_audit_logging: bool = True

    # Plugin System
    enable_plugins: bool = True
    plugin_directory: str = "./plugins"
```

#### Methods

##### `process_request()`

Process a user request through the full AC-AI pipeline.

```python
async def process_request(
    self,
    user_id: str,
    query: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None,
    preferences: Optional[UserPreferences] = None
) -> ACResult:
    """
    Process a request through the full Agency Calculus pipeline.

    Args:
        user_id: Unique user identifier
        query: User's request/question
        session_id: Current session identifier
        context: Optional context dictionary
        preferences: Optional user preferences

    Returns:
        ACResult with response, metadata, gate results, and metrics

    Raises:
        GateViolationError: If any gate check fails
        PluginExecutionError: If plugin execution fails
        ModelExecutionError: If model invocation fails
    """
```

**Example:**

```python
config = ACConfig(
    enable_four_gates=True,
    enable_ari_monitoring=True,
    enable_edm_monitoring=True
)

system = IntegratedACSystem(config=config)

result = await system.process_request(
    user_id="user-123",
    query="Help me learn how to implement binary search",
    session_id="session-1",
    context={"skill_level": "intermediate"}
)

print(f"Response: {result.response}")
print(f"Agency Score: {result.metadata['ari_snapshot'].autonomy_retention}")
print(f"Gates Passed: {result.gate_results.all_passed}")
```

##### `get_user_profile()`

Retrieve user's agency profile.

```python
async def get_user_profile(
    self,
    user_id: str
) -> UserProfile:
    """
    Get comprehensive user profile including ARI history, skills, preferences.

    Args:
        user_id: Unique user identifier

    Returns:
        UserProfile with ARI data, skill tracking, preferences
    """
```

##### `appeal_decision()`

Appeal a gate violation decision.

```python
async def appeal_decision(
    self,
    user_id: str,
    session_id: str,
    appeal_reason: str,
    context: Optional[Dict[str, Any]] = None
) -> AppealResult:
    """
    Appeal a blocked request to the AHO Tribunal.

    Args:
        user_id: User identifier
        session_id: Session with blocked request
        appeal_reason: Reason for appeal
        context: Additional context

    Returns:
        AppealResult with tribunal decision and reasoning
    """
```

#### Return Types

```python
@dataclass
class ACResult:
    """Result from IntegratedACSystem.process_request()"""

    response: str                      # Generated response
    gate_results: GateResults          # Results from all 4 gates
    ari_snapshot: ARISnapshot          # Current ARI metrics
    edm_analysis: EDMAnalysis          # Epistemic debt analysis
    metadata: Dict[str, Any]           # Additional metadata
    execution_time_ms: float           # Total execution time
    model_used: str                    # Which model was used
    cost_usd: float                   # Cost of request

@dataclass
class GateResults:
    """Results from Four Gates validation"""

    gate1_passed: bool                 # Net Agency
    gate2_passed: bool                 # Extraction Static Analysis
    gate3_passed: bool                 # Humanity Override
    gate4_passed: bool                 # Performance Parity
    all_passed: bool                   # All gates passed
    violations: List[GateViolation]    # Any violations found

@dataclass
class UserProfile:
    """User's agency profile"""

    user_id: str
    ari_score: float                   # Current ARI score
    ari_history: List[ARISnapshot]     # Historical ARI data
    skills: Dict[str, SkillLevel]      # Tracked skills
    preferences: UserPreferences       # User preferences
    total_interactions: int
    created_at: datetime
    updated_at: datetime
```

---

## Fractal Flow Engine (FFE) API

Goal-oriented growth scaffolding system.

### Class: `FractalFlowEngine`

```python
from ai_pal.ffe.engine import FractalFlowEngine, FFEConfig
```

#### Configuration

```python
@dataclass
class FFEConfig:
    """Configuration for Fractal Flow Engine"""

    # Momentum Loop
    enable_momentum_loop: bool = True
    friction_threshold: float = 0.3
    flow_threshold: float = 0.7

    # 5-Block System
    enable_5_block_rule: bool = True
    block_sizes: List[int] = field(default_factory=lambda: [15, 30, 60, 90, 0])

    # Scoping
    enable_80_20_scoping: bool = True
    max_scope_iterations: int = 5

    # Rewards
    enable_reward_system: bool = True
    reward_types: List[str] = field(default_factory=lambda: [
        "verbal_praise", "progress_visualization", "achievement_unlock"
    ])
```

#### Methods

##### `ingest_goal()`

Convert user goal into structured format.

```python
async def ingest_goal(
    self,
    user_id: str,
    goal_description: str,
    context: Optional[Dict[str, Any]] = None
) -> Goal:
    """
    Ingest and structure a user goal.

    Args:
        user_id: User identifier
        goal_description: Natural language goal
        context: Optional context (deadline, priority, etc.)

    Returns:
        Structured Goal object
    """
```

**Example:**

```python
ffe = FractalFlowEngine(config=FFEConfig())

goal = await ffe.ingest_goal(
    user_id="user-123",
    goal_description="Learn machine learning fundamentals",
    context={"deadline": "2024-03-01", "priority": "high"}
)

print(f"Goal ID: {goal.goal_id}")
print(f"Clarity Score: {goal.clarity_score}")
```

##### `scope_goal()`

Apply 80/20 fractal scoping to break down goal.

```python
async def scope_goal(
    self,
    goal: Goal,
    target_clarity: float = 0.8
) -> ScopingResult:
    """
    Apply fractal 80/20 scoping to goal.

    Iteratively identifies the 20% of effort that produces 80% of value.

    Args:
        goal: Goal to scope
        target_clarity: Target clarity score (0-1)

    Returns:
        ScopingResult with scoped tasks, clarity metrics
    """
```

##### `create_5_block_plan()`

Create a 5-block plan for a goal.

```python
async def create_5_block_plan(
    self,
    goal_id: str,
    user_id: str,
    scoping_result: Optional[ScopingResult] = None
) -> BlockPlan:
    """
    Create 5-block plan: Tiny → Small → Medium → Large → STOP

    Args:
        goal_id: Goal identifier
        user_id: User identifier
        scoping_result: Optional pre-scoped result

    Returns:
        BlockPlan with 5 time blocks
    """
```

##### `track_momentum()`

Track user's momentum state.

```python
async def track_momentum(
    self,
    user_id: str,
    goal_id: str,
    completion_data: CompletionData
) -> MomentumState:
    """
    Track momentum through states: Friction → Flow → Win → Pride

    Args:
        user_id: User identifier
        goal_id: Goal identifier
        completion_data: Data about completed blocks

    Returns:
        Current MomentumState
    """
```

##### `emit_reward()`

Emit reward for milestone completion.

```python
async def emit_reward(
    self,
    user_id: str,
    milestone_id: str,
    reward_type: Optional[str] = None
) -> Reward:
    """
    Emit contextual reward for milestone.

    Args:
        user_id: User identifier
        milestone_id: Completed milestone
        reward_type: Optional specific reward type

    Returns:
        Reward object
    """
```

#### Return Types

```python
@dataclass
class Goal:
    """Structured goal"""

    goal_id: str
    user_id: str
    description: str
    clarity_score: float               # 0-1, higher = clearer
    estimated_difficulty: float        # 0-1
    category: str                      # learning, productivity, creative, etc.
    deadline: Optional[datetime]
    priority: str                      # low, medium, high
    status: str                        # active, completed, abandoned
    created_at: datetime

@dataclass
class ScopingResult:
    """Result from 80/20 fractal scoping"""

    goal_id: str
    scoped_tasks: List[Task]           # Ordered by 80/20 priority
    clarity_achieved: float            # Final clarity score
    iterations_performed: int
    high_value_tasks: List[Task]       # The critical 20%
    supporting_tasks: List[Task]       # The remaining 80%

@dataclass
class BlockPlan:
    """5-block plan"""

    goal_id: str
    blocks: List[TimeBlock]            # 5 blocks
    total_estimated_time_minutes: int
    created_at: datetime

@dataclass
class TimeBlock:
    """Single time block"""

    block_number: int                  # 1-5
    duration_minutes: int              # 15, 30, 60, 90, or 0 (STOP)
    task: Optional[Task]
    status: str                        # pending, in_progress, completed
    momentum_state: Optional[str]      # friction, flow, win, pride

@dataclass
class MomentumState:
    """User's current momentum"""

    state: str                         # friction, flow, win, pride
    score: float                       # 0-1 momentum score
    consecutive_completions: int
    last_block_completed: Optional[datetime]
    next_recommended_block: Optional[TimeBlock]
```

---

## Agency Retention Index (ARI) API

Track user skill development and autonomy.

### Class: `AgencyRetentionIndex`

```python
from ai_pal.ari.tracker import AgencyRetentionIndex, ARIConfig
```

#### Methods

##### `track_interaction()`

Track a single interaction for ARI calculation.

```python
async def track_interaction(
    self,
    user_id: str,
    session_id: str,
    interaction_type: str,
    skill_category: str,
    ai_reliance_score: float,
    user_autonomy_score: float,
    metadata: Optional[Dict[str, Any]] = None
) -> ARISnapshot:
    """
    Track an interaction and update ARI.

    Args:
        user_id: User identifier
        session_id: Session identifier
        interaction_type: Type of interaction
        skill_category: Skill being exercised
        ai_reliance_score: How much user relied on AI (0-1)
        user_autonomy_score: User's demonstrated autonomy (0-1)
        metadata: Additional metadata

    Returns:
        Updated ARISnapshot
    """
```

**Example:**

```python
from ai_pal.ari.tracker import AgencyRetentionIndex

ari = AgencyRetentionIndex()

snapshot = await ari.track_interaction(
    user_id="user-123",
    session_id="session-1",
    interaction_type="code_assistance",
    skill_category="python_programming",
    ai_reliance_score=0.4,    # Low reliance = good
    user_autonomy_score=0.7,  # High autonomy = good
    metadata={"task": "implement_binary_search"}
)

print(f"Current ARI: {snapshot.autonomy_retention}")
print(f"Trend: {snapshot.trend}")  # improving, stable, declining
```

##### `get_skill_trajectory()`

Get trajectory for a specific skill.

```python
async def get_skill_trajectory(
    self,
    user_id: str,
    skill_category: str,
    time_window_days: int = 30
) -> SkillTrajectory:
    """
    Get skill development trajectory.

    Args:
        user_id: User identifier
        skill_category: Skill to analyze
        time_window_days: Days to look back

    Returns:
        SkillTrajectory with historical data
    """
```

##### `detect_deskilling()`

Detect if user is being deskilled.

```python
async def detect_deskilling(
    self,
    user_id: str,
    threshold: float = 0.1
) -> DeskillingAlert:
    """
    Detect deskilling patterns.

    Args:
        user_id: User identifier
        threshold: ARI decrease threshold to trigger alert

    Returns:
        DeskillingAlert with severity and recommendations
    """
```

#### Return Types

```python
@dataclass
class ARISnapshot:
    """Snapshot of ARI at a point in time"""

    user_id: str
    autonomy_retention: float          # 0-1, current ARI score
    trend: str                         # improving, stable, declining
    skill_breakdown: Dict[str, float]  # Per-skill ARI scores
    total_interactions: int
    timestamp: datetime

@dataclass
class SkillTrajectory:
    """Trajectory for a specific skill"""

    skill_category: str
    data_points: List[Tuple[datetime, float]]  # (timestamp, score)
    trend_line: List[float]            # Fitted trend
    velocity: float                    # Rate of change
    projected_mastery_date: Optional[datetime]

@dataclass
class DeskillingAlert:
    """Alert for detected deskilling"""

    severity: str                      # low, medium, high, critical
    affected_skills: List[str]
    ari_delta: float                   # How much ARI dropped
    recommendations: List[str]         # Actionable recommendations
    timestamp: datetime
```

---

## Epistemic Debt Management (EDM) API

Detect and manage questionable claims in AI responses.

### Class: `EpistemicDebtManager`

```python
from ai_pal.edm.manager import EpistemicDebtManager, EDMConfig
```

#### Methods

##### `analyze_response()`

Analyze an AI response for epistemic debt.

```python
async def analyze_response(
    self,
    response: str,
    context: Optional[Dict[str, Any]] = None
) -> EDMAnalysis:
    """
    Analyze response for questionable claims.

    Detects:
    - Hallucinations
    - Overconfident claims
    - Missing citations
    - Outdated information
    - Logical inconsistencies

    Args:
        response: AI-generated response
        context: Optional context (domain, user expertise, etc.)

    Returns:
        EDMAnalysis with flagged claims and debt score
    """
```

**Example:**

```python
from ai_pal.edm.manager import EpistemicDebtManager

edm = EpistemicDebtManager()

response = "Python 4.0 was released in 2023 with revolutionary features."

analysis = await edm.analyze_response(
    response=response,
    context={"domain": "programming", "check_factuality": True}
)

print(f"Debt Score: {analysis.debt_score}")
print(f"Flagged Claims: {len(analysis.flagged_claims)}")

for claim in analysis.flagged_claims:
    print(f"  - {claim.text}")
    print(f"    Issue: {claim.issue_type}")
    print(f"    Confidence: {claim.confidence}")
```

##### `suggest_corrections()`

Suggest corrections for flagged claims.

```python
async def suggest_corrections(
    self,
    analysis: EDMAnalysis,
    user_id: str
) -> List[Correction]:
    """
    Suggest corrections for flagged claims.

    Args:
        analysis: EDM analysis with flagged claims
        user_id: User identifier (for personalization)

    Returns:
        List of suggested corrections
    """
```

##### `get_citation_suggestions()`

Get citation suggestions for uncited claims.

```python
async def get_citation_suggestions(
    self,
    claim: str,
    domain: Optional[str] = None
) -> List[Citation]:
    """
    Get citation suggestions for a claim.

    Args:
        claim: The claim needing citation
        domain: Optional domain for focused search

    Returns:
        List of relevant citations
    """
```

#### Return Types

```python
@dataclass
class EDMAnalysis:
    """Analysis of epistemic debt in response"""

    debt_score: float                  # 0-1, higher = more debt
    flagged_claims: List[FlaggedClaim]
    confidence_level: str              # high, medium, low
    requires_review: bool              # Human review needed?
    timestamp: datetime

@dataclass
class FlaggedClaim:
    """A single flagged claim"""

    text: str                          # The claim text
    issue_type: str                    # hallucination, overconfident, etc.
    severity: str                      # low, medium, high
    confidence: float                  # 0-1, confidence in flagging
    suggested_action: str              # verify, remove, soften, cite
    evidence_against: Optional[List[str]]

@dataclass
class Correction:
    """Suggested correction"""

    original_text: str
    corrected_text: str
    reasoning: str
    confidence: float
    citation: Optional[Citation]

@dataclass
class Citation:
    """Citation for a claim"""

    source: str                        # URL, paper ID, book, etc.
    title: str
    relevance_score: float
    publication_date: Optional[datetime]
    snippet: str
```

---

## Four Gates API

The four gates that all requests must pass.

### Gate 1: Net Agency Validator

```python
from ai_pal.gates.agency_validator import AgencyValidator

class AgencyValidator:
    async def validate(
        self,
        request: Request,
        ari_snapshot: ARISnapshot
    ) -> GateResult:
        """
        Validate that response promotes skill development over deskilling.

        Args:
            request: The user request
            ari_snapshot: Current ARI snapshot

        Returns:
            GateResult (passed/failed with reasoning)
        """
```

### Gate 2: Extraction Analyzer

```python
from ai_pal.gates.extraction_analyzer import ExtractionAnalyzer

class ExtractionAnalyzer:
    async def validate(
        self,
        request: Request,
        response_plan: ResponsePlan
    ) -> GateResult:
        """
        Static analysis for dark patterns and extractive behavior.

        Checks for:
        - Data harvesting
        - Dark UX patterns
        - Manipulative language
        - Hidden costs

        Args:
            request: The user request
            response_plan: Planned response

        Returns:
            GateResult with any violations found
        """
```

### Gate 3: Override Checker

```python
from ai_pal.gates.override_checker import OverrideChecker

class OverrideChecker:
    async def validate(
        self,
        request: Request,
        autonomous_actions: List[Action]
    ) -> GateResult:
        """
        Ensure user can stop/modify any autonomous actions.

        Args:
            request: The user request
            autonomous_actions: Any autonomous actions planned

        Returns:
            GateResult (fails if override not possible)
        """
```

### Gate 4: Performance Validator

```python
from ai_pal.gates.performance_validator import PerformanceValidator

class PerformanceValidator:
    async def validate(
        self,
        request: Request,
        estimated_latency_ms: float,
        human_baseline_ms: float
    ) -> GateResult:
        """
        Ensure AI response is comparable to human speed.

        Args:
            request: The user request
            estimated_latency_ms: Estimated AI response time
            human_baseline_ms: Comparable human time

        Returns:
            GateResult (fails if AI is significantly slower)
        """
```

### Return Type

```python
@dataclass
class GateResult:
    """Result from a single gate"""

    gate_name: str                     # gate1_net_agency, etc.
    passed: bool
    score: float                       # 0-1
    violations: List[Violation]
    reasoning: str
    timestamp: datetime

@dataclass
class Violation:
    """A gate violation"""

    violation_type: str
    severity: str                      # low, medium, high, critical
    description: str
    suggested_fix: Optional[str]
```

---

## Plugin System API

Extensible plugin architecture.

### Class: `PluginManager`

```python
from ai_pal.plugins.manager import PluginManager, PluginConfig
```

#### Methods

##### `load_plugin()`

Load a plugin.

```python
async def load_plugin(
    self,
    plugin_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Plugin:
    """
    Load and initialize a plugin.

    Validates plugin signature, dependencies, and security.

    Args:
        plugin_path: Path to plugin directory
        config: Optional plugin configuration

    Returns:
        Loaded Plugin

    Raises:
        PluginValidationError: If plugin is invalid
        PluginSecurityError: If plugin fails security checks
    """
```

##### `execute_plugin()`

Execute a plugin.

```python
async def execute_plugin(
    self,
    plugin_id: str,
    input_data: Dict[str, Any],
    sandbox: bool = True
) -> PluginResult:
    """
    Execute a plugin in sandboxed environment.

    Args:
        plugin_id: Plugin identifier
        input_data: Input data for plugin
        sandbox: Execute in sandbox (recommended)

    Returns:
        PluginResult with output and metadata
    """
```

##### `list_plugins()`

List all loaded plugins.

```python
async def list_plugins(
    self,
    category: Optional[str] = None
) -> List[PluginInfo]:
    """
    List loaded plugins.

    Args:
        category: Optional category filter

    Returns:
        List of PluginInfo
    """
```

#### Plugin Interface

Plugins must implement this interface:

```python
from ai_pal.plugins.base import PluginBase

class MyPlugin(PluginBase):
    """Custom plugin"""

    # Metadata
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"
    author = "Your Name"
    category = "utility"

    # Dependencies
    dependencies = ["numpy>=1.20.0"]

    # Capabilities
    capabilities = ["data_processing", "api_integration"]

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with config"""
        pass

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution logic"""
        # Your plugin logic here
        return {"result": "success"}

    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
```

#### Return Types

```python
@dataclass
class PluginResult:
    """Result from plugin execution"""

    plugin_id: str
    output: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class PluginInfo:
    """Plugin information"""

    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    capabilities: List[str]
    status: str                        # active, inactive, error
    loaded_at: datetime
```

---

## Model Orchestration API

Multi-model routing and execution.

### Class: `ModelOrchestrator`

```python
from ai_pal.models.orchestrator import ModelOrchestrator, OrchestratorConfig
```

#### Methods

##### `select_model()`

Select optimal model for a task.

```python
async def select_model(
    self,
    task_requirements: TaskRequirements,
    user_preferences: Optional[UserPreferences] = None
) -> ModelConfig:
    """
    Select optimal model based on requirements.

    Considers:
    - Task complexity
    - Cost constraints
    - Latency requirements
    - Quality needs
    - User preferences

    Args:
        task_requirements: Task requirements
        user_preferences: Optional user preferences

    Returns:
        Selected ModelConfig
    """
```

**Example:**

```python
from ai_pal.models.orchestrator import ModelOrchestrator, TaskRequirements

orchestrator = ModelOrchestrator()

requirements = TaskRequirements(
    complexity=0.8,                    # High complexity
    max_latency_ms=5000,              # 5 second max
    max_cost_usd=0.01,                # 1 cent max
    optimization_goal="quality"        # Optimize for quality
)

model = await orchestrator.select_model(requirements)

print(f"Selected: {model.model_name}")
print(f"Provider: {model.provider}")
print(f"Cost: ${model.cost_per_1k_tokens}")
```

##### `execute_with_model()`

Execute a task with a specific model.

```python
async def execute_with_model(
    self,
    model_config: ModelConfig,
    prompt: str,
    system_prompt: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> ModelResponse:
    """
    Execute prompt with specified model.

    Args:
        model_config: Model to use
        prompt: User prompt
        system_prompt: Optional system prompt
        parameters: Optional model parameters

    Returns:
        ModelResponse with output and metadata
    """
```

##### `execute_with_fallback()`

Execute with automatic fallback on failure.

```python
async def execute_with_fallback(
    self,
    primary_model: ModelConfig,
    fallback_models: List[ModelConfig],
    prompt: str,
    max_retries: int = 3
) -> ModelResponse:
    """
    Execute with automatic fallback to alternative models.

    Args:
        primary_model: First model to try
        fallback_models: Models to try if primary fails
        prompt: User prompt
        max_retries: Max retries per model

    Returns:
        ModelResponse from first successful execution
    """
```

#### Return Types

```python
@dataclass
class TaskRequirements:
    """Requirements for a task"""

    complexity: float                  # 0-1
    max_latency_ms: float
    max_cost_usd: float
    min_quality_score: float = 0.7
    optimization_goal: str = "balanced"  # cost, quality, speed, balanced
    required_capabilities: List[str] = field(default_factory=list)

@dataclass
class ModelConfig:
    """Configuration for a model"""

    model_name: str
    provider: str                      # anthropic, openai, local
    model_type: str                    # chat, completion, embedding
    cost_per_1k_tokens: float
    avg_latency_ms: float
    quality_score: float               # 0-1
    context_window: int
    capabilities: List[str]

@dataclass
class ModelResponse:
    """Response from model execution"""

    content: str
    model_used: str
    tokens_used: int
    cost_usd: float
    latency_ms: float
    finish_reason: str
    metadata: Dict[str, Any]
```

---

## Security API

### Input Sanitization

```python
from ai_pal.security.sanitizer import InputSanitizer

sanitizer = InputSanitizer()

# Sanitize user input
clean_input = await sanitizer.sanitize(
    user_input=raw_input,
    context_type="chat_message"
)

# Check for PII
pii_detected = await sanitizer.detect_pii(text)
if pii_detected:
    scrubbed_text = await sanitizer.scrub_pii(text)
```

### Secret Scanning

```python
from ai_pal.security.scanner import SecretScanner

scanner = SecretScanner()

# Scan for secrets
secrets = await scanner.scan_text(content)
if secrets:
    print(f"Found {len(secrets)} secrets!")
    for secret in secrets:
        print(f"  Type: {secret.secret_type}")
        print(f"  Location: {secret.location}")
```

### Audit Logging

```python
from ai_pal.security.audit import AuditLogger

logger = AuditLogger()

# Log security event
await logger.log_event(
    event_type="unauthorized_access",
    user_id="user-123",
    details={"resource": "/admin", "ip": "1.2.3.4"},
    severity="high"
)

# Query audit log
events = await logger.query_events(
    start_date=datetime.now() - timedelta(days=7),
    event_types=["unauthorized_access", "data_export"],
    min_severity="medium"
)
```

---

## Monitoring & Metrics API

### Prometheus Metrics

```python
from ai_pal.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

# Record metrics
metrics.record_request(
    endpoint="/api/chat",
    status_code=200,
    latency_ms=250.5,
    model_used="claude-3-5-sonnet"
)

metrics.record_gate_result(
    gate_name="gate1_net_agency",
    passed=True,
    score=0.85
)

metrics.record_ari_update(
    user_id="user-123",
    ari_score=0.75,
    trend="improving"
)

# Export for Prometheus
prometheus_metrics = metrics.export_prometheus()
```

### Health Checks

```python
from ai_pal.monitoring.health import HealthChecker

health = HealthChecker()

# Get system health
status = await health.check_health()

print(f"Status: {status.status}")  # healthy, degraded, unhealthy
print(f"Database: {status.components['database']}")
print(f"Redis: {status.components['redis']}")
print(f"Models: {status.components['models']}")
```

---

## HTTP REST API

FastAPI-based REST API for web/mobile clients.

### Base URL

```
http://localhost:8000
```

### Authentication

```http
POST /api/auth/token

Content-Type: application/json
{
  "username": "user@example.com",
  "password": "your-password"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Use token in subsequent requests:

```http
Authorization: Bearer eyJ...
```

### Endpoints

#### Process Chat Request

```http
POST /api/chat

Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "Help me learn binary search",
  "session_id": "session-123",
  "context": {
    "skill_level": "intermediate"
  }
}

Response:
{
  "response": "Let's learn binary search step by step...",
  "gate_results": {
    "all_passed": true,
    "gate1_passed": true,
    "gate2_passed": true,
    "gate3_passed": true,
    "gate4_passed": true
  },
  "ari_snapshot": {
    "autonomy_retention": 0.75,
    "trend": "improving"
  },
  "metadata": {
    "execution_time_ms": 1250.5,
    "model_used": "anthropic/claude-3-5-sonnet",
    "cost_usd": 0.0042
  }
}
```

#### Get User Profile

```http
GET /api/users/{user_id}/profile

Authorization: Bearer {token}

Response:
{
  "user_id": "user-123",
  "ari_score": 0.75,
  "skills": {
    "python_programming": 0.8,
    "machine_learning": 0.6
  },
  "total_interactions": 1523,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### FFE: Create Goal

```http
POST /api/ffe/goals

Authorization: Bearer {token}
Content-Type: application/json

{
  "description": "Learn machine learning fundamentals",
  "deadline": "2024-03-01",
  "priority": "high"
}

Response:
{
  "goal_id": "goal-456",
  "clarity_score": 0.85,
  "estimated_difficulty": 0.7,
  "status": "active"
}
```

#### FFE: Create 5-Block Plan

```http
POST /api/ffe/goals/{goal_id}/plan

Authorization: Bearer {token}

Response:
{
  "goal_id": "goal-456",
  "blocks": [
    {
      "block_number": 1,
      "duration_minutes": 15,
      "task": "Read overview of supervised learning",
      "status": "pending"
    },
    {
      "block_number": 2,
      "duration_minutes": 30,
      "task": "Complete linear regression tutorial",
      "status": "pending"
    },
    // ... blocks 3-4 ...
    {
      "block_number": 5,
      "duration_minutes": 0,
      "task": null,
      "status": "pending"  // STOP block
    }
  ]
}
```

#### Appeal Gate Violation

```http
POST /api/appeals

Authorization: Bearer {token}
Content-Type: application/json

{
  "session_id": "session-123",
  "appeal_reason": "I believe this helps my learning because..."
}

Response:
{
  "appeal_id": "appeal-789",
  "decision": "approved",
  "reasoning": "The tribunal found...",
  "decided_at": "2024-01-20T15:45:00Z"
}
```

#### Health Check

```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-20T16:00:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "models": "healthy"
  }
}
```

#### Metrics (Prometheus)

```http
GET /metrics

Response: (Prometheus format)
# HELP ai_pal_requests_total Total requests
# TYPE ai_pal_requests_total counter
ai_pal_requests_total{endpoint="/api/chat",status="200"} 1523

# HELP ai_pal_request_duration_seconds Request duration
# TYPE ai_pal_request_duration_seconds histogram
ai_pal_request_duration_seconds_bucket{le="0.5"} 1245
...
```

---

## Error Handling

All APIs use consistent error types:

```python
class AIpalError(Exception):
    """Base exception for AI-PAL"""
    pass

class GateViolationError(AIpalError):
    """Raised when a gate check fails"""

    def __init__(self, gate_name: str, violation: Violation):
        self.gate_name = gate_name
        self.violation = violation

class PluginExecutionError(AIpalError):
    """Raised when plugin execution fails"""
    pass

class ModelExecutionError(AIpalError):
    """Raised when model invocation fails"""
    pass

class ValidationError(AIpalError):
    """Raised when input validation fails"""
    pass
```

HTTP API errors:

```json
{
  "error": {
    "code": "gate_violation",
    "message": "Request blocked by Gate 1: Net Agency",
    "details": {
      "gate": "gate1_net_agency",
      "violation_type": "potential_deskilling",
      "severity": "high",
      "can_appeal": true
    }
  }
}
```

---

## Rate Limiting

Default rate limits:

- **Chat API**: 60 requests/minute per user
- **FFE API**: 30 requests/minute per user
- **Appeals**: 10 requests/hour per user

Headers returned:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705766400
```

---

## Webhooks

Subscribe to events:

```python
from ai_pal.webhooks import WebhookManager

webhook = WebhookManager()

# Register webhook
await webhook.register(
    url="https://your-app.com/webhooks/aipal",
    events=["ari.deskilling_detected", "ffe.goal_completed"],
    secret="your-webhook-secret"
)
```

Webhook payload:

```json
{
  "event": "ari.deskilling_detected",
  "timestamp": "2024-01-20T16:00:00Z",
  "data": {
    "user_id": "user-123",
    "severity": "high",
    "ari_delta": -0.15,
    "affected_skills": ["python_programming"]
  },
  "signature": "sha256=..."
}
```

---

## SDK Examples

### Python SDK

```python
from ai_pal_sdk import AIpal

# Initialize
aipal = AIpal(api_key="your-api-key")

# Chat
response = await aipal.chat(
    query="Help me learn binary search",
    session_id="session-1"
)

# Check ARI
profile = await aipal.get_profile()
print(f"ARI: {profile.ari_score}")

# Create FFE goal
goal = await aipal.ffe.create_goal(
    description="Learn ML fundamentals"
)

# Create plan
plan = await aipal.ffe.create_plan(goal.goal_id)
```

### JavaScript SDK

```javascript
import { AIpal } from '@ai-pal/sdk';

const aipal = new AIpal({ apiKey: 'your-api-key' });

// Chat
const response = await aipal.chat({
  query: 'Help me learn binary search',
  sessionId: 'session-1'
});

// Check ARI
const profile = await aipal.getProfile();
console.log(`ARI: ${profile.ariScore}`);

// FFE
const goal = await aipal.ffe.createGoal({
  description: 'Learn ML fundamentals'
});
```

---

## Versioning

API uses semantic versioning: `v{major}.{minor}.{patch}`

Current version: **v1.0.0**

Breaking changes increment major version.

---

## Support

For API questions:
- Documentation: https://docs.ai-pal.dev
- GitHub Issues: https://github.com/ai-pal/ai-pal/issues
- API Status: https://status.ai-pal.dev

---

*Last updated: 2024-01-20*
