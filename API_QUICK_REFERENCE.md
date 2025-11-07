# AI-PAL Backend API - Quick Reference Summary

## Key Files
- **Main API**: `/src/ai_pal/api/main.py` (37KB, ~1200 lines)
- **AHO Tribunal**: `/src/ai_pal/api/aho_tribunal.py` (13KB, ~500 lines)
- **Metrics**: `/src/ai_pal/monitoring/metrics.py` (16KB)
- **Health Checker**: `/src/ai_pal/monitoring/health.py` (15KB)
- **ARI Engine**: `/src/ai_pal/monitoring/ari_engine.py` (85KB)
- **Audit Logger**: `/src/ai_pal/security/audit_log.py` (16KB)
- **FFE Models**: `/src/ai_pal/ffe/models.py` (20KB)

## API Structure at a Glance

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints (except /health, /metrics) require:
```
Authorization: Bearer <user_id>
```

### Core Endpoints (9 categories, 40+ endpoints)

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| **System** | /health, /metrics | Monitoring & diagnostics |
| **Chat** | POST /api/chat | Main AC system processing |
| **Users** | GET /api/users/{id}/profile | User profile & ARI history |
| **FFE Goals** | POST/GET /api/ffe/goals/* | Goal creation & planning |
| **Social** | POST/GET /api/social/* | Group & win sharing |
| **Personality** | POST/GET /api/personality/* | Strength discovery |
| **Teaching** | POST/GET /api/teaching/* | Knowledge capture |
| **Patches** | GET/POST /api/patch-requests/* | AI self-improvement review |
| **Appeals** | GET/POST /api/appeals/* | AHO Tribunal (port 8001) |

## Authentication & Error Handling

### Status Codes
- **200**: Success
- **400**: Bad request
- **401**: Unauthorized (missing/invalid auth)
- **403**: Forbidden (access denied)
- **404**: Not found
- **500**: Server error
- **503**: Service unavailable

### Error Response
```json
{
  "error": {
    "code": 401,
    "message": "Authorization header required",
    "timestamp": "2024-11-04T10:00:00Z"
  }
}
```

## Key Data Models

### ChatRequest/Response
```
Request: query, session_id, context
Response: response, gate_results, ari_snapshot, edm_analysis, metadata
```

### ARI Metrics
- **overall_ari**: 0-1 score
- **signal_level**: HIGH, MEDIUM, LOW, CRITICAL
- **trend**: improving, stable, declining
- **confidence**: 0-1 measurement confidence

### FFE Goal
- **complexity_level**: ATOMIC, MICRO, MINI, MACRO, MEGA
- **status**: PENDING, IN_PROGRESS, COMPLETED, SCOPED
- **clarity_score**: 0-1
- **linked_strength**: User strength type

### Health Status
- **status**: HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN
- **components**: database, redis, models, gates, filesystem

## Monitoring & Metrics

### Prometheus Endpoint
```
GET /metrics
```

Provides 20+ metrics including:
- Request counts & latency
- Gate evaluation results
- ARI score tracking
- Model usage & costs
- FFE goal progress

## Security Features

### Audit Logging
- Event types: LOGIN, LOGOUT, GATE_EVALUATION, SECRET_DETECTED, etc.
- Severity levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Auto-rotation: 100MB files, 10 backups, 90-day retention

### Four Gates Framework
All requests pass through:
1. Gate 1: Net Agency (user retains control)
2. Gate 2: Extraction Analysis (detects ability drain)
3. Gate 3: Humanity Override (appeals system)
4. Gate 4: Performance Parity (prevents deskilling)

## Real-Time Features

### Current Implementation
- HTTP polling via REST endpoints
- Prometheus push/pull model

### Recommended WebSocket Additions
```
/ws/ari/{user_id}        - Real-time ARI updates
/ws/momentum/{goal_id}   - Momentum loop state
/ws/feed/{group_id}      - Social feed
```

## Running the API

### Development
```bash
uvicorn ai_pal.api.main:app --reload --port 8000
```

### Production
```bash
uvicorn ai_pal.api.main:app --workers 4 --port 8000
```

### AHO Tribunal (separate service)
```bash
uvicorn ai_pal.api.aho_tribunal:app --port 8001
```

### Access Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Integration Points

### ARI Engine (Monitoring)
- Passive lexical analysis
- Socratic co-pilot checkpoints
- Deep dive baseline mode
- Three-layer measurement system

### FFE (Goal Management)
- Atomic task scoping (15-90 min blocks)
- 5-Block planning rule
- Momentum loops
- Strength-based reframing
- Social win sharing

### Security Systems
- Audit logging (JSON-based)
- Secret detection & sanitization
- Patch request workflow
- Protected files list

### Health Checks
Monitors:
- Database connectivity
- Redis cache
- Model provider availability
- Plugin system
- File system (disk space)
- Four Gates functionality

## Example Requests

### Chat Processing
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer user-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I improve my skills?",
    "session_id": "session-123"
  }'
```

### Create Goal
```bash
curl -X POST http://localhost:8000/api/ffe/goals \
  -H "Authorization: Bearer user-123" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Learn Python",
    "priority": "high"
  }'
```

### Approve Patch
```bash
curl -X POST http://localhost:8000/api/patch-requests/patch-123/approve \
  -H "Authorization: Bearer user-123" \
  -d '{
    "approved": true,
    "review_comment": "Approved"
  }'
```

## Configuration

### Environment Variables
```
AI_PAL_DATA_DIR=./data
AI_PAL_CREDENTIALS=./credentials.json
CORS_ORIGINS=*
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx
```

### System Initialization
All systems enabled by default:
- gates, tribunal, ari_monitoring, edm_monitoring
- self_improvement, privacy_protection
- context_management, model_orchestration
- dashboard, ffe, social_features
- personality_discovery, teaching_mode

## Notable Design Patterns

1. **Singleton Pattern**: AC system, metrics, health checker
2. **Dependency Injection**: FastAPI Depends() for auth
3. **Dataclass Models**: Pydantic for request/response validation
4. **Async Operations**: async/await throughout
5. **Thread-Safe Metrics**: Lock-protected metric updates
6. **Exception Handlers**: Custom HTTPException & general handlers

---

**Full Documentation**: See API_DOCUMENTATION.md for comprehensive details
