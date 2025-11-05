# AI-PAL Backend API Documentation

## Overview
AI-PAL is a Privacy-First Autonomous Cognitive Partner system built with FastAPI. The backend implements an advanced cognitive architecture with the Four Gates framework, ARI monitoring, FFE (Fractal Flow Engine), and comprehensive security/audit features.

---

## 1. API ENDPOINTS STRUCTURE & ROUTING

### Application Configuration
- **Framework**: FastAPI (Python)
- **Location**: `/src/ai_pal/api/main.py`
- **Main App**: `app = FastAPI(title="AI-PAL API", version="1.0.0")`
- **Docs URL**: `/docs` (Swagger UI)
- **ReDoc URL**: `/redoc`

### CORS Configuration
```python
CORSMiddleware enabled with configurable origins (default: "*")
Allow credentials: True
Allow methods: ["*"]
Allow headers: ["*"]
```

### Endpoint Categories

#### 1.1 System Endpoints
```
GET /health                    - System health check
GET /metrics                   - Prometheus metrics (text format)
```

#### 1.2 Core AC System
```
POST /api/chat                 - Main entry point for AC processing
  - Requires: Bearer token auth
  - Body: ChatRequest (query, session_id, context)
  - Returns: ChatResponse with gate results, ARI snapshot, EDM analysis
```

#### 1.3 User Management
```
GET /api/users/{user_id}/profile    - Get user profile with ARI history
  - Requires: Bearer token (must match user_id)
  - Returns: User profile with ARI snapshots
```

#### 1.4 FFE (Fractal Flow Engine) Goals
```
POST /api/ffe/goals            - Create FFE goal
GET /api/ffe/goals/{goal_id}   - Get goal details
POST /api/ffe/goals/{goal_id}/plan  - Create 5-block plan
```

#### 1.5 Social Features
```
POST /api/social/groups                    - Create sharing group
POST /api/social/groups/{group_id}/join    - Join group
POST /api/social/groups/{group_id}/leave   - Leave group
GET /api/social/groups                     - List user's groups
GET /api/social/feed/{group_id}            - View group feed
POST /api/social/share                     - Share win with groups
POST /api/social/encourage/{share_id}      - Send encouragement
```

#### 1.6 Personality Discovery
```
POST /api/personality/discover/start          - Start discovery session
GET /api/personality/discover/{session_id}/question  - Get next question
POST /api/personality/discover/{session_id}/answer/{question_id}  - Record answer
POST /api/personality/discover/{session_id}/complete  - Complete session
GET /api/personality/strengths                - Get current strengths
GET /api/personality/insights                 - Get personality insights
```

#### 1.7 Teaching/Protégé Pipeline
```
POST /api/teaching/start              - Start teaching mode
POST /api/teaching/submit             - Submit teaching content
GET /api/teaching/taught-topics       - Get teaching history
```

#### 1.8 Patch Requests (AI Self-Improvement)
```
GET /api/patch-requests                - Get all patch requests
GET /api/patch-requests/pending        - Get pending approvals
GET /api/patch-requests/{request_id}   - Get patch details
POST /api/patch-requests/{request_id}/approve  - Approve/deny patch
GET /api/patch-requests/protected-files - Get protected files list
```

#### 1.9 AHO Tribunal (Appeals & Humanity Override)
**Separate app on port 8001**: `/src/ai_pal/api/aho_tribunal.py`

```
GET /                          - Dashboard (HTML)
GET /api/appeals               - List appeals
GET /api/appeals/{appeal_id}   - Get appeal details
POST /api/appeals/{appeal_id}/override  - Execute override
POST /api/appeals/{appeal_id}/restore   - Restore user
POST /api/appeals/{appeal_id}/repair    - Create repair ticket
GET /api/repair-tickets        - List repair tickets
GET /api/audit-log             - Get audit trail
GET /health                    - Health check
```

---

## 2. AUTHENTICATION MECHANISM

### JWT/Bearer Token Authentication

**Implementation Location**: `get_current_user()` dependency in `/src/ai_pal/api/main.py`

```python
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user from authorization header
    Format: "Bearer <token>"
    """
```

### Authentication Flow
1. All protected endpoints require `Authorization` header
2. Format: `Authorization: Bearer <token>`
3. Token is extracted and used as `user_id`
4. In production: JWT validation and signature verification (to be implemented)
5. Currently: Bearer token used directly as user identifier

### Error Codes
- **401 Unauthorized**: Missing or invalid auth header
- **403 Forbidden**: User accessing other user's data

### Dependency Injection
```python
@app.post("/api/chat")
async def process_chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    # user_id is automatically extracted and injected
```

---

## 3. DATA MODELS & RESPONSE FORMATS

### 3.1 User Profiles

**Request Model**: None (GET endpoint)

**Response Format**:
```json
{
  "user_id": "user-123",
  "ari_score": 0.75,
  "ari_history": [
    {
      "timestamp": "2024-11-04T10:00:00Z",
      "score": 0.75,
      "trend": "improving"
    }
  ],
  "skills": ["python", "writing"],
  "total_interactions": 150,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 3.2 ARI Metrics (Autonomy Retention Index)

**Data Model**: `ARIScore` in `/src/ai_pal/monitoring/ari_engine.py`

```python
@dataclass
class ARIScore:
    user_id: str
    timestamp: datetime
    overall_ari: float              # 0-1, higher is better
    signal_level: ARISignalLevel    # HIGH, MEDIUM, LOW, CRITICAL
    lexical_ari: float              # From passive text analysis
    interaction_ari: float          # From Socratic co-pilot
    baseline_deviation: float       # Deviation from deep dive baseline
    trend_direction: str            # "improving", "stable", "declining"
    days_in_trend: int
    alerts: List[str]               # Alert messages
    confidence: float               # 0-1 confidence score
```

**Measurement Methods**:
1. **Passive Lexical Analysis**: Continuous background measurement
   - Lexical diversity
   - Syntactic complexity
   - Domain-specific terminology

2. **Socratic Co-pilot**: Unassisted Capability Checkpoints (UCCs)
   - Embedded interaction measurement
   - Response type classification
   - Capability demonstration scoring

3. **Deep Dive Mode**: Opt-in baseline establishment
   - Knowledge topics
   - Synthesis quality
   - Reasoning depth

### 3.3 FFE Goals & Tasks

**Goal Creation Response**:
```json
{
  "goal_id": "goal-abc123",
  "description": "Learn Python",
  "clarity_score": 0.85,
  "estimated_difficulty": 0.65,
  "status": "pending"
}
```

**Goal Details Response**:
```json
{
  "goal_id": "goal-abc123",
  "description": "Learn Python",
  "clarity_score": 0.85,
  "estimated_difficulty": 0.65,
  "status": "pending",
  "category": "learning",
  "deadline": "2024-12-31T00:00:00Z",
  "priority": "high"
}
```

**5-Block Plan Response**:
```json
{
  "goal_id": "goal-abc123",
  "blocks": [
    {
      "block_number": 1,
      "duration_minutes": 300,
      "task": "Tiny: Variables & Data Types",
      "status": "pending"
    },
    {
      "block_number": 2,
      "duration_minutes": 600,
      "task": "Small: Control Flow",
      "status": "pending"
    },
    {
      "block_number": 3,
      "duration_minutes": 1200,
      "task": "Medium: Functions & Modules",
      "status": "pending"
    },
    {
      "block_number": 4,
      "duration_minutes": 2400,
      "task": "Large: OOP & Projects",
      "status": "pending"
    },
    {
      "block_number": 5,
      "duration_minutes": 0,
      "task": "STOP: Reassess & Review",
      "status": "pending"
    }
  ],
  "total_estimated_time_minutes": 4500,
  "created_at": "2024-11-04T10:00:00Z"
}
```

**FFE Data Models** (`/src/ai_pal/ffe/models.py`):
```python
@dataclass
class GoalPacket:
    goal_id: str
    user_id: str
    description: str
    complexity_level: TaskComplexityLevel  # ATOMIC, MICRO, MINI, MACRO, MEGA
    status: GoalStatus  # PENDING, IN_PROGRESS, COMPLETED, SCOPED, etc.
    linked_strength: Optional[StrengthType]
    metadata: Dict[str, Any]

@dataclass
class AtomicBlock:
    block_id: str
    user_id: str
    goal_id: str
    title: str
    description: str
    time_block_size: TimeBlockSize  # 15, 30, 60, 90, 120 minutes
    using_strength: Optional[StrengthType]
    reward_text: Optional[str]
    pride_hit_intensity: float  # 0-1
```

### 3.4 System Health

**Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-04T10:00:00Z",
  "uptime_seconds": 3600.0,
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful",
      "response_time_ms": 2.5
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful",
      "response_time_ms": 1.0
    },
    "models": {
      "status": "healthy",
      "message": "At least one model provider available",
      "details": {
        "anthropic": "configured",
        "openai": "configured",
        "local": "available"
      }
    },
    "gates": {
      "status": "healthy",
      "message": "All Four Gates operational"
    }
  }
}
```

**Health Status Values**: HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN

### 3.5 Audit Logs

**Event Types**:
```python
class AuditEventType(Enum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAILURE = "auth_failure"
    
    # Gates
    GATE_EVALUATION = "gate_evaluation"
    GATE_PASSED = "gate_passed"
    GATE_FAILED = "gate_failed"
    
    # Security
    SECRET_DETECTED = "secret_detected"
    VALIDATION_FAILED = "validation_failed"
    
    # Data
    DATA_ACCESS = "data_access"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    
    # Models
    MODEL_REQUEST = "model_request"
    HIGH_COST_REQUEST = "high_cost_request"
    
    # ARI/EDM
    ARI_SNAPSHOT = "ari_snapshot"
    EDM_DEBT_DETECTED = "edm_debt_detected"
```

**Audit Event Structure**:
```json
{
  "event_type": "gate_evaluation",
  "severity": "info",
  "timestamp": "2024-11-04T10:00:00Z",
  "user_id": "user-123",
  "session_id": "session-abc",
  "component": "gate_system",
  "action": "evaluate_gate1",
  "details": {
    "gate_name": "gate1_net_agency",
    "score": 0.85
  },
  "result": "success",
  "ip_address": "192.168.1.1",
  "resource": "gate1_net_agency"
}
```

### 3.6 Chat Request/Response

**ChatRequest**:
```python
@dataclass
class ChatRequest(BaseModel):
    query: str                          # User's request
    session_id: str                     # Session identifier
    context: Optional[Dict[str, Any]]   # Optional context
```

**ChatResponse**:
```json
{
  "response": "Here's the answer...",
  "gate_results": {
    "all_passed": true,
    "gate1_passed": true,
    "gate2_passed": true,
    "gate3_passed": true,
    "gate4_passed": true,
    "violations": []
  },
  "ari_snapshot": {
    "autonomy_retention": 0.75,
    "trend": "improving",
    "total_interactions": 150
  },
  "edm_analysis": {
    "debt_score": 0.2,
    "flagged_claims": 2,
    "requires_review": false
  },
  "metadata": {
    "execution_time_ms": 250,
    "model_used": "claude-3-5-sonnet",
    "cost_usd": 0.05
  }
}
```

---

## 4. WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES

**Status**: Not currently implemented in main.py

**Recommended Implementation Locations**:
- Real-time ARI score updates
- Momentum loop state changes
- Goal completion events
- Social feed updates

**Example endpoints to add**:
```python
@app.websocket("/ws/ari/{user_id}")
async def websocket_ari(websocket: WebSocket, user_id: str):
    # Real-time ARI updates
    
@app.websocket("/ws/momentum/{goal_id}")
async def websocket_momentum(websocket: WebSocket, goal_id: str):
    # Real-time momentum loop updates
    
@app.websocket("/ws/feed/{group_id}")
async def websocket_feed(websocket: WebSocket, group_id: str):
    # Real-time social feed updates
```

---

## 5. ERROR HANDLING & RESPONSE CODES

### HTTP Status Codes

**2xx Success**
- **200 OK**: Successful GET/POST request
- **201 Created**: Resource created

**4xx Client Errors**
- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Missing/invalid auth header
- **403 Forbidden**: User lacks permission (e.g., accessing other user's data)
- **404 Not Found**: Resource not found
- **503 Service Unavailable**: Optional feature not available (e.g., FFE disabled)

**5xx Server Errors**
- **500 Internal Server Error**: Unhandled exception

### Error Response Format

**HTTPException Handler**:
```json
{
  "error": {
    "code": 401,
    "message": "Authorization header required",
    "timestamp": "2024-11-04T10:00:00Z"
  }
}
```

**General Exception Handler**:
```json
{
  "error": {
    "code": 500,
    "message": "Internal server error",
    "timestamp": "2024-11-04T10:00:00Z"
  }
}
```

### Common Error Scenarios

```python
# Authentication Errors
HTTPException(status_code=401, detail="Authorization header required")
HTTPException(status_code=401, detail="Invalid authentication scheme")
HTTPException(status_code=401, detail="Invalid authorization header format")

# Authorization Errors
HTTPException(status_code=403, detail="Cannot access other users' profiles")

# Not Found Errors
HTTPException(status_code=404, detail="Goal not found")
HTTPException(status_code=404, detail="Patch request not found")

# Service Unavailable
HTTPException(status_code=503, detail="FFE not available")
HTTPException(status_code=503, detail="Patch request system not available")

# Business Logic Errors
HTTPException(status_code=400, detail="Failed to join group")
HTTPException(status_code=500, detail="Request processing failed: {error}")
```

---

## 6. API DOCUMENTATION & EXAMPLES

### Example Requests

#### 1. Process Chat Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer user-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can I improve my programming skills?",
    "session_id": "session-abc123",
    "context": {
      "domain": "programming",
      "experience_level": "intermediate"
    }
  }'
```

#### 2. Get User Profile
```bash
curl http://localhost:8000/api/users/user-123/profile \
  -H "Authorization: Bearer user-123"
```

#### 3. Create FFE Goal
```bash
curl -X POST http://localhost:8000/api/ffe/goals \
  -H "Authorization: Bearer user-123" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Learn Python fundamentals",
    "deadline": "2024-12-31",
    "priority": "high"
  }'
```

#### 4. Get Health Status
```bash
curl http://localhost:8000/health
```

#### 5. Get Metrics
```bash
curl http://localhost:8000/metrics
```

#### 6. Approve Patch Request
```bash
curl -X POST http://localhost:8000/api/patch-requests/patch-123/approve \
  -H "Authorization: Bearer admin-user" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "review_comment": "Looks good, approved for implementation"
  }'
```

### Swagger Documentation
- Access Swagger UI: `http://localhost:8000/docs`
- Interactive API testing available
- Schema definitions auto-generated from Pydantic models

---

## 7. METRICS & MONITORING

### Prometheus Metrics Endpoint
```
GET /metrics
```

Returns metrics in Prometheus text format.

### Metric Types

**Counters** (monotonically increasing):
- `ai_pal_requests_total`: Total API requests
- `ai_pal_request_errors_total`: Total request errors
- `ai_pal_gate_checks_total`: Total gate evaluations
- `ai_pal_gate_failures_total`: Total gate failures
- `ai_pal_ari_updates_total`: Total ARI updates
- `ai_pal_model_calls_total`: Total model calls
- `ai_pal_model_tokens_total`: Total tokens used
- `ai_pal_model_cost_usd_total`: Total model costs

**Gauges** (can increase/decrease):
- `ai_pal_ari_score`: Current ARI score
- `ai_pal_edm_debt_score`: Epistemic debt score
- `ai_pal_ffe_goal_clarity`: Goal clarity score
- `ai_pal_ffe_goal_completion`: Goal completion percentage
- `ai_pal_system_resources`: System resource usage

**Histograms** (distributions):
- `ai_pal_request_duration_seconds`: Request latency
- `ai_pal_model_latency_seconds`: Model response latency
- `ai_pal_plugin_execution_seconds`: Plugin execution time

### Metric Labels
```
{endpoint="/api/chat", method="POST", status="200"}
{gate="gate1_net_agency", result="passed"}
{user_id="user-123", skill="python_programming"}
{model="claude-3-5-sonnet", provider="anthropic"}
```

---

## 8. SYSTEM INITIALIZATION & CONFIGURATION

### Startup Process
```python
@app.on_event("startup")
async def startup_event():
    logger.info("AI-PAL API starting up")
    get_ac_system()  # Initialize AC system
    logger.info("AI-PAL API ready")
```

### AC System Configuration
```python
config = SystemConfig(
    data_dir=data_dir,
    credentials_path=credentials_path,
    enable_gates=True,
    enable_tribunal=True,
    enable_ari_monitoring=True,
    enable_edm_monitoring=True,
    enable_self_improvement=True,
    enable_privacy_protection=True,
    enable_context_management=True,
    enable_model_orchestration=True,
    enable_dashboard=True,
    enable_ffe=True,
    enable_social_features=True,
    enable_personality_discovery=True,
    enable_teaching_mode=True,
)
```

### Environment Variables
```
AI_PAL_DATA_DIR         # Data directory path
AI_PAL_CREDENTIALS      # Credentials file path
CORS_ORIGINS           # CORS allowed origins
REDIS_URL              # Redis connection URL
ANTHROPIC_API_KEY      # Anthropic API key
OPENAI_API_KEY         # OpenAI API key
```

---

## 9. RUNNING THE API

### Development Server
```bash
python -m uvicorn ai_pal.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Server
```bash
uvicorn ai_pal.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### AHO Tribunal Service (separate)
```bash
python -m uvicorn ai_pal.api.aho_tribunal:app --host 0.0.0.0 --port 8001
```

---

## 10. NOTABLE FEATURES & INTEGRATIONS

### Four Gates Framework
All chat requests pass through:
1. **Gate 1: Net Agency** - Ensures user retains agency
2. **Gate 2: Extraction Analysis** - Detects ability extraction
3. **Gate 3: Humanity Override** - Allows human review/appeals
4. **Gate 4: Performance Parity** - Ensures no deskilling

### ARI Monitoring
Non-invasive measurement of autonomy retention through:
- Passive lexical analysis (continuous)
- Socratic co-pilot checkpoints (embedded)
- Deep dive mode (opt-in baseline)

### FFE Integration
Fractal Flow Engine for goal management:
- Atomic task scoping
- 5-Block planning
- Momentum loops with strength reframing
- Social sharing of wins

### Security & Auditing
- Comprehensive audit logging
- Secret detection
- Sanitization controls
- Patch request review workflow

### Appeal & Override System
Separate AHO Tribunal service for:
- User appeals
- Humanity override execution
- User restoration
- Repair ticket generation
