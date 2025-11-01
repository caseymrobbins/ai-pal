# AI-PAL Architecture Overview

This document provides a comprehensive overview of the AI-PAL system architecture, component interactions, and design principles.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   CLI    │  │ Web API  │  │Dashboard │  │  Plugins │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Core Integration Layer                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           IntegratedACSystem (Entry Point)               │  │
│  │  - Request routing                                       │  │
│  │  - Component coordination                                │  │
│  │  - Response aggregation                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Gate System   │  │  Orchestration  │  │  Monitoring     │
│  (Phase 1)     │  │  (Phase 3)      │  │  (Phase 2)      │
│                │  │                 │  │                 │
│ • Net Agency   │  │ • Multi-Model   │  │ • ARI Monitor   │
│ • Extraction   │  │ • Task Routing  │  │ • EDM Monitor   │
│ • Override     │  │ • Cost Tracking │  │ • Dashboards    │
│ • Performance  │  │ • Streaming     │  │ • Alerts        │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   FFE Engine      │
                    │   (Phase 5)       │
                    │                   │
                    │ • Goal Ingestor   │
                    │ • Scoping Agent   │
                    │ • Time Blocks     │
                    │ • Strength Amp    │
                    │ • Rewards         │
                    │ • Growth Scaffold │
                    │ • Momentum Loop   │
                    └───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   Security     │  │    Storage      │  │   Providers     │
│                │  │                 │  │                 │
│ • Secret Scan  │  │ • JSON Files    │  │ • Anthropic     │
│ • Sanitization │  │ • SQLite        │  │ • OpenAI        │
│ • Audit Log    │  │ • Vector DB     │  │ • Local/Ollama  │
│ • Credentials  │  │ • Cache         │  │ • Custom        │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

## Core Components

### 1. IntegratedACSystem (Core Integration Layer)

**Location**: `src/ai_pal/core/integrated_system.py`

**Purpose**: Central orchestrator that coordinates all system components.

**Key Responsibilities**:
- Request routing and validation
- Gate enforcement
- Model orchestration
- Monitoring integration
- Response aggregation

**Request Flow**:
```python
async def process_request(
    user_id: str,
    query: str,
    session_id: str
) -> ACResponse:
    # 1. Pre-flight checks
    user_context = await self._build_user_context(user_id)

    # 2. Gate validation (Phase 1)
    gate_results = await self._run_gates(query, user_context)
    if not all(gate_results.values()):
        return ACResponse(blocked=True, gate_results=gate_results)

    # 3. Model orchestration (Phase 3)
    llm_response = await self.orchestrator.route_request(
        prompt=query,
        optimization_goal="balanced"
    )

    # 4. Response validation
    validation = self._validate_response(llm_response)

    # 5. Monitoring (Phase 2)
    ari_snapshot = await self._record_ari_snapshot(user_id, llm_response)
    edm_debts = await self._check_epistemic_debt(llm_response.text)

    # 6. Return aggregated response
    return ACResponse(
        model_response=llm_response.text,
        metadata={
            'gate_results': gate_results,
            'ari_snapshot': ari_snapshot,
            'epistemic_debts': edm_debts,
            'validation': validation
        }
    )
```

### 2. Gate System (Phase 1)

**Location**: `src/ai_pal/gates/`

**Components**:
- `agency_validator.py`: Gate 1 - Net Agency
- `extraction_analyzer.py`: Gate 2 - Extraction Static Analysis
- `override_checker.py`: Gate 3 - Humanity Override
- `performance_validator.py`: Gate 4 - Performance Parity
- `enhanced_tribunal.py`: Multi-stakeholder appeals

**Gate 1: Net Agency**
```python
class AgencyValidator:
    async def validate(self, context: Dict[str, Any]) -> GateResult:
        # Check if interaction enhances user capability
        ari_data = context.get('ari_snapshot')

        if ari_data.delta_agency < 0:
            return GateResult(
                passed=False,
                reason="Negative agency delta detected",
                severity="high"
            )

        if ari_data.skill_development < 0.05:
            return GateResult(
                passed=False,
                reason="Insufficient skill development",
                severity="medium"
            )

        return GateResult(passed=True)
```

**Gate 2: Extraction Static Analysis**
- Scans for dark patterns
- Detects manipulation techniques
- Validates ethical design

**Gate 3: Humanity Override**
- Ensures user control
- Validates stop mechanisms
- Checks override capabilities

**Gate 4: Performance Parity**
- Measures response latency
- Compares to human baseline
- Validates resource usage

### 3. Multi-Model Orchestrator (Phase 3)

**Location**: `src/ai_pal/orchestration/multi_model.py`

**Purpose**: Intelligent model selection and execution

**Model Selection Algorithm**:
```python
def select_model(self, requirements: TaskRequirements) -> ModelConfig:
    # Score each model based on requirements
    scores = {}
    for model_name, model_config in self.models.items():
        score = self._calculate_model_score(
            model_config,
            requirements
        )
        scores[model_name] = score

    # Select highest-scoring model
    best_model = max(scores, key=scores.get)
    return self.models[best_model]

def _calculate_model_score(
    self,
    model: ModelConfig,
    requirements: TaskRequirements
) -> float:
    # Weighted scoring
    cost_score = (requirements.max_cost_usd - model.cost_per_1k_tokens) / requirements.max_cost_usd
    speed_score = (requirements.max_latency_ms - model.avg_latency_ms) / requirements.max_latency_ms
    quality_score = model.quality_score

    # Apply weights based on optimization goal
    if requirements.optimization_goal == OptimizationGoal.COST:
        weights = {'cost': 0.6, 'speed': 0.2, 'quality': 0.2}
    elif requirements.optimization_goal == OptimizationGoal.SPEED:
        weights = {'cost': 0.2, 'speed': 0.6, 'quality': 0.2}
    elif requirements.optimization_goal == OptimizationGoal.QUALITY:
        weights = {'cost': 0.2, 'speed': 0.2, 'quality': 0.6}
    else:  # BALANCED
        weights = {'cost': 0.33, 'speed': 0.33, 'quality': 0.34}

    total_score = (
        cost_score * weights['cost'] +
        speed_score * weights['speed'] +
        quality_score * weights['quality']
    )

    return total_score
```

**Supported Providers**:
- **Anthropic**: Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku)
- **OpenAI**: GPT models (gpt-4, gpt-3.5-turbo)
- **Local**: Ollama models (phi-2, llama2, mistral)

**Features**:
- Automatic model selection
- Cost tracking
- Token counting
- Streaming responses
- Error handling and retries

### 4. Monitoring System (Phase 2)

**Location**: `src/ai_pal/monitoring/`

#### 4.1 ARI Monitor

**Purpose**: Track agency retention and skill development

**Key Metrics**:
```python
@dataclass
class AgencySnapshot:
    timestamp: datetime
    task_id: str
    task_type: str

    # Core metrics
    delta_agency: float          # -1.0 to 1.0
    bhir: float                  # Bottleneck-to-Human-Intervention Ratio
    task_efficacy: float         # 0.0 to 1.0

    # Skill metrics
    user_skill_before: float     # 0.0 to 1.0
    user_skill_after: float      # 0.0 to 1.0
    skill_development: float     # Difference

    # Agency metrics
    ai_reliance: float           # 0.0 to 1.0
    autonomy_retention: float    # 0.0 to 1.0

    user_id: str
    session_id: str
```

**Alert System**:
```python
class ARIAlert:
    DESKILLING_THRESHOLD = -0.1  # Negative delta_agency
    HIGH_RELIANCE_THRESHOLD = 0.8  # Too much AI use
    LOW_SKILL_DEV_THRESHOLD = 0.05  # Not learning enough

    async def check_alerts(self, user_id: str) -> List[Alert]:
        snapshots = await self.get_recent_snapshots(user_id, days=7)

        # Check for deskilling trend
        if self._has_negative_trend(snapshots):
            yield Alert(
                type="deskilling_detected",
                severity="high",
                message="Agency declining over 7 days"
            )

        # Check for high AI reliance
        avg_reliance = sum(s.ai_reliance for s in snapshots) / len(snapshots)
        if avg_reliance > self.HIGH_RELIANCE_THRESHOLD:
            yield Alert(
                type="high_ai_reliance",
                severity="medium",
                message=f"AI reliance at {avg_reliance:.0%}"
            )
```

#### 4.2 EDM Monitor

**Purpose**: Detect epistemic debt in AI responses

**Debt Types**:
```python
class EpistemicDebtType(Enum):
    UNFALSIFIABLE_CLAIM = "unfalsifiable"
    UNVERIFIED_ASSERTION = "unverified"
    VAGUE_CLAIM = "vague"
    MISSING_CITATION = "missing_citation"
    CHERRY_PICKING = "cherry_picking"
    CORRELATION_CAUSATION = "correlation_causation"
```

**Detection Patterns**:
```python
PATTERNS = {
    'unfalsifiable': [
        r'everyone knows',
        r'it\'s obvious that',
        r'clearly',
        r'undoubtedly'
    ],
    'unverified': [
        r'studies show',
        r'research indicates',
        r'experts say',
        r'it has been proven'
    ],
    'vague': [
        r'some people',
        r'many believe',
        r'often',
        r'sometimes'
    ]
}
```

**Severity Classification**:
- **Critical**: Claims that could cause harm if false
- **High**: Important decisions depend on accuracy
- **Medium**: Could mislead but low immediate risk
- **Low**: Minor imprecision

### 5. Fractal Flow Engine (Phase 5)

**Location**: `src/ai_pal/ffe/`

**Architecture**:
```
FractalFlowEngine
├── GoalIngestor (goal capture)
├── ScopingAgent (80/20 analysis)
├── TimeBlockManager (5-block rule)
├── StrengthAmplifier (task reframing)
├── RewardEmitter (celebration)
├── GrowthScaffold (bottleneck detection)
└── MomentumLoop (state machine)
```

**Momentum State Machine**:
```python
class MomentumState(Enum):
    FRICTION = "friction"  # Haven't started
    FLOW = "flow"          # Actively working
    WIN = "win"            # Just completed
    PRIDE = "pride"        # Celebrating

# Transitions
ALLOWED_TRANSITIONS = {
    FRICTION: [FLOW],                    # Start working
    FLOW: [WIN, FRICTION],               # Complete or stop
    WIN: [PRIDE],                        # Celebrate
    PRIDE: [FRICTION, FLOW]              # Start next task
}
```

**5-Block Stop Rule Implementation**:
```python
class TimeBlockManager:
    BLOCK_SIZES = {
        BlockSize.TINY: 15,    # minutes
        BlockSize.SMALL: 30,
        BlockSize.MEDIUM: 60,
        BlockSize.LARGE: 90
    }

    async def create_5_block_plan(self, goal_id: str) -> BlockPlan:
        blocks = [
            Block(size=BlockSize.TINY, can_stop_after=True),
            Block(size=BlockSize.SMALL, can_stop_after=True),
            Block(size=BlockSize.MEDIUM, can_stop_after=True),
            Block(size=BlockSize.LARGE, can_stop_after=True),
            Block(size=BlockSize.STOP, mandatory=True)  # Break
        ]

        return BlockPlan(blocks=blocks, total_duration=195)
```

### 6. Security Infrastructure

**Location**: `src/ai_pal/security/`

#### 6.1 Secret Scanner

**Patterns**: 15+ secret types
- API keys (Anthropic, OpenAI, AWS, GitHub)
- Private keys (RSA, SSH, PGP)
- Database URLs
- JWT tokens
- Passwords

**Entropy Analysis**:
```python
def _calculate_entropy(self, text: str) -> float:
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1

    length = len(text)
    entropy = 0.0

    for count in char_counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy  # Higher = more random = likely real secret
```

#### 6.2 Input Sanitization

**Sanitization Levels**:
- **Strict**: Maximum security, may break functionality
- **Moderate**: Balanced security and usability (default)
- **Lenient**: Minimal sanitization

**Context-Aware Sanitization**:
```python
def sanitize_string(self, input_str: str, context: str) -> SanitizationResult:
    if context == "path":
        return self._sanitize_path(input_str)
    elif context == "sql":
        return self._sanitize_sql(input_str)
    elif context == "html":
        return self._sanitize_html(input_str)
    elif context == "command":
        return self._sanitize_command(input_str)
    else:
        return self._sanitize_general(input_str)
```

#### 6.3 Audit Logging

**Event Types** (25+):
- Authentication & Authorization
- Gate Events
- Plugin Events
- Security Events
- Data Events
- Model Events
- ARI/EDM Events
- System Events

**Async Logging**:
```python
class AuditLogger:
    def __init__(self):
        self._event_queue = Queue()
        self._worker_thread = threading.Thread(
            target=self._process_events,
            daemon=True
        )
        self._worker_thread.start()

    def log_event(self, event: AuditEvent):
        self._event_queue.put(event)  # Non-blocking

    def _process_events(self):
        while True:
            event = self._event_queue.get()
            self._write_event(event)  # Write to file
            self._event_queue.task_done()
```

### 7. Plugin System

**Location**: `src/ai_pal/plugins/`

**Plugin Types**:
- `model_provider`: Custom LLM providers
- `monitoring`: Custom monitoring systems
- `gate`: Custom validation gates
- `ffe_component`: FFE extensions
- `interface`: UI extensions
- `integration`: Third-party integrations
- `utility`: General utilities

**Plugin Lifecycle**:
```
Discovered → Loaded → Initialized → Running → Stopped → Unloaded
```

**Sandboxed Execution**:
```python
class PluginSandbox:
    def __init__(self, limits: SandboxLimits):
        self.limits = limits  # Memory, CPU, time limits

    async def execute_async(self, coro, *args, **kwargs):
        # Apply resource limits
        self._apply_limits()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                coro(*args, **kwargs),
                timeout=self.limits.max_execution_time_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise SandboxTimeoutError()
        finally:
            self._restore_limits()
```

## Data Flow

### Request Processing Flow

```
1. User Request
   ↓
2. IntegratedACSystem.process_request()
   ↓
3. Build User Context
   ├── Load personality profile
   ├── Get recent ARI snapshots
   └── Retrieve session history
   ↓
4. Gate Validation (Parallel)
   ├── Gate 1: Net Agency ✓
   ├── Gate 2: Extraction ✓
   ├── Gate 3: Override ✓
   └── Gate 4: Performance ✓
   ↓
5. Model Orchestration
   ├── Select optimal model
   ├── Execute request
   └── Stream response
   ↓
6. Response Validation
   ├── Check for secrets
   ├── Sanitize output
   └── Validate quality
   ↓
7. Monitoring
   ├── Record ARI snapshot
   ├── Detect epistemic debt
   └── Update dashboards
   ↓
8. Return ACResponse
   ├── Model response
   ├── Gate results
   ├── ARI snapshot
   ├── Epistemic debts
   └── Metadata
```

### FFE Goal Processing Flow

```
1. Goal Ingestion
   ↓
2. 80/20 Scoping
   ├── Identify high-value 20%
   ├── Break into atomic tasks
   └── Defer low-value 80%
   ↓
3. Create 5-Block Plan
   ├── Tiny (15 min)
   ├── Small (30 min)
   ├── Medium (60 min)
   ├── Large (90 min)
   └── STOP (break)
   ↓
4. Task Reframing
   └── Apply signature strengths
   ↓
5. Execution
   ├── Track momentum state
   ├── Detect bottlenecks
   └── Monitor progress
   ↓
6. Completion & Reward
   ├── Emit personalized reward
   ├── Record win
   └── Update momentum
```

## Design Principles

### 1. Agency First

Every component prioritizes user capability development:
- Gates block deskilling interactions
- ARI tracks skill growth
- FFE scaffolds learning
- No black-box decisions

### 2. Transparency

All decisions are explainable:
- Gate results include reasoning
- ARI shows skill deltas
- EDM flags questionable claims
- Audit logs record everything

### 3. User Sovereignty

Users maintain ultimate control:
- Override any AI decision via AHO Tribunal
- Configure all thresholds
- Opt out of any feature
- Export all personal data

### 4. Ethical by Design

Ethics embedded in architecture:
- 4-Gate System enforces boundaries
- Dark pattern detection
- Privacy-first data handling
- Multi-stakeholder oversight

### 5. Performance

Fast enough to not hinder productivity:
- <5s response times
- Async/parallel processing
- Streaming responses
- Efficient caching

## Technology Stack

**Backend**:
- Python 3.11+
- FastAPI (web framework)
- Pydantic (data validation)
- asyncio (async/await)

**Storage**:
- JSON files (development)
- SQLite (production option)
- Redis (caching)

**ML/AI**:
- Anthropic Claude API
- OpenAI GPT API
- Ollama (local models)

**Security**:
- Pattern-based secret detection
- Entropy analysis
- Input sanitization
- Audit logging

**Testing**:
- pytest (unit tests)
- pytest-asyncio (async tests)
- unittest.mock (mocking)

**CI/CD**:
- GitHub Actions
- Pre-commit hooks
- Automated gate validation

## Performance Characteristics

### Latency Targets

- **Total request latency**: <5s (Gate 4)
- **ARI snapshot recording**: <50ms
- **EDM analysis**: <100ms
- **Model selection**: <1ms
- **FFE goal ingestion**: <50ms

### Throughput

- **Sustained throughput**: >5 req/s
- **Concurrent requests**: 100+ supported
- **Plugin execution**: Resource-limited

### Resource Usage

- **Memory per request**: <100MB
- **Memory for 100 requests**: <200MB
- **Plugin memory limit**: 512MB (configurable)
- **Plugin CPU limit**: 30s (configurable)

## Extension Points

### Adding a New Gate

```python
# 1. Create gate class
class CustomGate:
    async def validate(self, context: Dict[str, Any]) -> GateResult:
        # Your validation logic
        if not meets_criteria(context):
            return GateResult(passed=False, reason="...")
        return GateResult(passed=True)

# 2. Register in IntegratedACSystem
self.gates['custom_gate'] = CustomGate()
```

### Adding a New Model Provider

```python
# 1. Implement ModelProvider interface
class CustomProvider(BaseModelProvider):
    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Call your model API
        response = await self.api_client.generate(request.prompt)
        return LLMResponse(...)

    def calculate_cost(self, prompt_tokens, completion_tokens):
        return (prompt_tokens + completion_tokens) * self.price_per_token

# 2. Register with orchestrator
orchestrator.register_model("custom-model", CustomProvider())
```

### Adding a New FFE Component

```python
# 1. Create component
class CustomFFEComponent:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    async def process(self, goal, user):
        # Your logic here
        pass

# 2. Integrate into FFE engine
ffe_engine.custom_component = CustomFFEComponent(orchestrator)
```

## Testing Strategy

### Unit Tests

- All components have >80% coverage
- Mock external dependencies
- Test edge cases and error paths

### Integration Tests

- Cross-phase component interaction
- End-to-end request flows
- Multi-user isolation

### Performance Tests

- Load testing (10, 50, 100 concurrent)
- Latency benchmarks
- Memory profiling
- Stress testing

### Security Tests

- Secret detection validation
- Input sanitization effectiveness
- Injection attack prevention
- Access control verification

## Deployment Architecture

### Development

```
Local Machine
├── Python 3.11+
├── SQLite database
├── JSON file storage
└── Ollama (local models)
```

### Production

```
Cloud Environment
├── Application Servers (FastAPI)
├── PostgreSQL (persistent storage)
├── Redis (caching)
├── Model APIs (Anthropic, OpenAI)
└── Monitoring (Prometheus, Grafana)
```

## Further Reading

- [API Reference](./API_REFERENCE.md)
- [Plugin Development Guide](./PLUGIN_GUIDE.md)
- [Security Architecture](./SECURITY.md)
- [Performance Tuning](./PERFORMANCE.md)
