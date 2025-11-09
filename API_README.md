# AI-PAL Backend API Documentation

Comprehensive documentation for the AI-PAL FastAPI backend system.

## Documentation Files

This repository contains three complementary documentation files:

### 1. **API_QUICK_REFERENCE.md** (6KB, 242 lines)
**Start here for a quick overview**
- Architecture at a glance
- HTTP status codes
- Key data models
- Example curl requests
- Configuration essentials
- Running the API

**Best for**: Getting started quickly, quick lookups, example requests

### 2. **API_DOCUMENTATION.md** (18KB, 729 lines)
**Complete API reference**
- Detailed endpoint listings (40+ endpoints across 9 categories)
- Authentication mechanism (Bearer token, JWT)
- Data models for:
  - User profiles
  - ARI metrics (Autonomy Retention Index)
  - FFE goals and tasks
  - System health
  - Audit logs
  - Chat requests/responses
- WebSocket recommendations
- Error handling and codes
- Metrics and monitoring (Prometheus)
- System initialization and configuration
- Running instructions (dev/production)
- Notable features and integrations

**Best for**: Building client applications, understanding the complete API surface, integration details

### 3. **API_FILE_STRUCTURE.md** (12KB, 374 lines)
**Complete codebase architecture**
- File locations and structure
- Key classes and methods in each file
- Component breakdown:
  - API Layer (`/src/ai_pal/api/`)
  - Monitoring & Metrics (`/src/ai_pal/monitoring/`)
  - Security & Auditing (`/src/ai_pal/security/`)
  - FFE Engine (`/src/ai_pal/ffe/`)
  - Core System (`/src/ai_pal/core/`)
  - Additional modules
- Data flow diagrams
- Configuration and ports
- Integration points

**Best for**: Understanding the codebase, contributing to development, system architecture

## Quick Navigation

### For API Users
1. Start with **API_QUICK_REFERENCE.md**
2. Reference **API_DOCUMENTATION.md** for details
3. Use **API_DOCUMENTATION.md** examples for integration

### For Developers
1. Read **API_FILE_STRUCTURE.md** for architecture
2. Review **API_DOCUMENTATION.md** for endpoint details
3. Check **API_QUICK_REFERENCE.md** for key patterns

### For DevOps/System Administrators
1. See **API_QUICK_REFERENCE.md** for running the API
2. Reference **API_DOCUMENTATION.md** for configuration
3. Check **API_FILE_STRUCTURE.md** for component dependencies

## Key Highlights

### API Features
- **40+ REST endpoints** across 9 major categories
- **Bearer token authentication** (JWT-ready)
- **Prometheus metrics** for monitoring
- **Comprehensive health checks** (6 component checks)
- **Extensive audit logging** (structured JSON events)
- **Error handling** with detailed codes and messages

### Core Systems
- **Four Gates Framework**: Privacy and autonomy protection
- **ARI Monitoring**: Autonomy Retention Index (3-layer measurement)
- **FFE Engine**: Fractal Flow Engine for goal management
- **AHO Tribunal**: Appeals and Humanity Override system
- **Security**: Secret detection, sanitization, audit trails
- **Multi-model support**: Claude, OpenAI, Google, Cohere, Mistral, Groq

### Data Models
- **User Profiles** with ARI history
- **Goal Management** (atomic to mega complexity)
- **Personality Strengths** (8 core types)
- **Time Blocks** (15-120 minute durations)
- **Momentum States** for goal completion
- **Bottleneck Detection** and resolution
- **Social Features** for win sharing

## Running the API

### Quick Start
```bash
# Install dependencies
pip install fastapi uvicorn

# Development server
python -m uvicorn ai_pal.api.main:app --reload --port 8000

# Access documentation
# Swagger: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Production
```bash
uvicorn ai_pal.api.main:app --workers 4 --port 8000
```

## API Endpoints Summary

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Chat & Users
- `POST /api/chat` - Main AI processing
- `GET /api/users/{user_id}/profile` - User profile

### FFE (Goals)
- `POST /api/ffe/goals` - Create goal
- `GET /api/ffe/goals/{goal_id}` - Get goal
- `POST /api/ffe/goals/{goal_id}/plan` - Create 5-block plan

### Social
- `POST /api/social/groups` - Create group
- `GET /api/social/groups` - List groups
- `POST /api/social/share` - Share win

### Personality
- `POST /api/personality/discover/start` - Start discovery
- `GET /api/personality/strengths` - Get strengths

### Teaching
- `POST /api/teaching/start` - Start teaching
- `POST /api/teaching/submit` - Submit content

### Patches (AI Self-Improvement)
- `GET /api/patch-requests` - List patches
- `POST /api/patch-requests/{id}/approve` - Approve patch

### Appeals (AHO Tribunal, port 8001)
- `GET /api/appeals` - List appeals
- `POST /api/appeals/{id}/override` - Override decision

## Key Concepts

### Authentication
- **Type**: Bearer token (JWT-ready)
- **Header**: `Authorization: Bearer <user_id>`
- **Protected**: All endpoints except /health and /metrics

### ARI (Autonomy Retention Index)
Three-layer non-invasive measurement:
1. **Passive Lexical Analysis** - Continuous background
2. **Socratic Co-pilot** - Embedded checkpoints
3. **Deep Dive Mode** - Opt-in baseline

### FFE (Fractal Flow Engine)
Goal management with:
- Atomic task scoping
- 5-Block planning
- Momentum loops
- Strength reframing
- Social sharing

### Four Gates
Validation on every request:
1. Gate 1: Net Agency (user control)
2. Gate 2: Extraction (ability drain detection)
3. Gate 3: Humanity (appeals system)
4. Gate 4: Parity (no deskilling)

## File Locations

```
Repository Root/
├── API_README.md                    (this file)
├── API_QUICK_REFERENCE.md           (start here)
├── API_DOCUMENTATION.md             (complete reference)
├── API_FILE_STRUCTURE.md            (code architecture)
└── src/ai_pal/
    ├── api/
    │   ├── main.py                  (FastAPI app)
    │   └── aho_tribunal.py          (Appeals system)
    ├── monitoring/
    │   ├── health.py                (Health checks)
    │   ├── metrics.py               (Prometheus)
    │   └── ari_engine.py            (ARI monitoring)
    ├── security/
    │   ├── audit_log.py             (Audit logging)
    │   ├── credential_manager.py
    │   ├── sanitization.py
    │   └── secret_scanner.py
    ├── ffe/
    │   ├── models.py                (Data structures)
    │   ├── engine.py
    │   ├── components/
    │   ├── interfaces/
    │   └── ...
    └── ... (other modules)
```

## Support & Resources

### Documentation
1. Swagger UI: http://localhost:8000/docs
2. ReDoc: http://localhost:8000/redoc
3. This README and associated docs

### Key Classes to Know
- `IntegratedACSystem` - Main orchestrator
- `ARIEngine` - Autonomy monitoring
- `FFEEngine` - Goal management
- `HealthChecker` - System diagnostics
- `MetricsCollector` - Prometheus metrics
- `AuditLogger` - Event logging

### Important Endpoints for Monitoring
- `GET /health` - Component status
- `GET /metrics` - Prometheus metrics
- Audit logs in JSON format

## Conclusion

The AI-PAL backend is a comprehensive, privacy-first cognitive system with robust monitoring, security, and goal management capabilities. Use these documentation files to understand and integrate with the system.

Start with **API_QUICK_REFERENCE.md** for a quick overview, then dive into **API_DOCUMENTATION.md** for detailed specifications.

---

**Documentation Generated**: November 4, 2024
**FastAPI Version**: 0.100+
**Python Version**: 3.10+
