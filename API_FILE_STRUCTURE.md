# AI-PAL API - File Structure & Key Locations

## Main API Files

### `/src/ai_pal/api/` - API Layer (Main Entry Point)

```
src/ai_pal/api/
├── main.py                    # Main FastAPI application (37KB, 1223 lines)
│   ├── app = FastAPI()        # Application instance
│   ├── get_ac_system()        # Singleton AC system
│   ├── get_current_user()     # Bearer token authentication
│   ├── ChatRequest/ChatResponse# Pydantic models
│   ├── /health                # Health check endpoint
│   ├── /metrics               # Prometheus metrics
│   ├── /api/chat              # Main AC processing
│   ├── /api/users             # User profiles
│   ├── /api/ffe               # FFE goals & planning
│   ├── /api/social            # Social sharing
│   ├── /api/personality       # Strength discovery
│   ├── /api/teaching          # Teaching mode
│   ├── /api/patch-requests    # AI self-improvement
│   ├── Error handlers         # Custom exception handling
│   └── Startup/Shutdown       # Lifecycle management
│
├── aho_tribunal.py            # Appeals & Humanity Override (13KB, 505 lines)
│   ├── app = FastAPI()        # Separate Tribunal app (port 8001)
│   ├── Appeal, OverrideAction, RestoreAction
│   ├── RepairTicket, AHODatabase
│   ├── /api/appeals           # Appeal management
│   ├── /api/appeals/{id}/override
│   ├── /api/appeals/{id}/restore
│   ├── /api/appeals/{id}/repair
│   ├── /api/repair-tickets    # Engineering tickets
│   ├── /api/audit-log         # Audit trail
│   └── Submit appeals helper
│
├── __init__.py
└── templates/
    └── dashboard.html         # AHO dashboard (HTML template)
```

## Monitoring & Metrics

### `/src/ai_pal/monitoring/` - Health, Metrics, ARI

```
src/ai_pal/monitoring/
├── health.py                  # Health checking (15KB)
│   ├── HealthStatus enum
│   ├── ComponentHealth dataclass
│   ├── SystemHealth dataclass
│   ├── HealthChecker class
│   ├── _check_database()
│   ├── _check_redis()
│   ├── _check_models()
│   ├── _check_plugins()
│   ├── _check_filesystem()
│   ├── _check_gates()
│   └── get_health_checker() singleton
│
├── metrics.py                 # Prometheus metrics (16KB)
│   ├── MetricValue dataclass
│   ├── MetricsCollector class
│   ├── Counters, Gauges, Histograms
│   ├── record_request()
│   ├── record_gate_result()
│   ├── record_ari_update()
│   ├── record_edm_analysis()
│   ├── record_ffe_goal()
│   ├── record_model_usage()
│   ├── export_prometheus()
│   ├── export_json()
│   └── get_metrics() singleton
│
├── ari_engine.py              # ARI Monitoring (85KB)
│   ├── ARISignalLevel enum
│   ├── UCCResponseType enum
│   ├── LexicalMetrics dataclass
│   ├── UnassistedCapabilityCheckpoint
│   ├── ARIBaseline dataclass
│   ├── ARIScore dataclass
│   ├── PassiveLexicalAnalyzer class
│   │   ├── analyze_text()
│   │   ├── _calculate_lexical_diversity()
│   │   ├── _calculate_vocabulary_richness()
│   │   ├── _calculate_avg_sentence_length()
│   │   ├── _calculate_syntactic_complexity()
│   │   └── calculate_lexical_ari()
│   ├── SocraticCopilot class
│   │   ├── identify_uccs()
│   │   ├── log_response()
│   │   └── calculate_interaction_ari()
│   ├── DeepDiveMode class
│   │   ├── start_deep_dive()
│   │   ├── record_deep_dive_response()
│   │   └── finalize_baseline()
│   └── ARIEngine class (orchestrator)
│       ├── analyze_user_text()
│       ├── intercept_task_delegation()
│       ├── calculate_comprehensive_ari()
│       └── get_ari_history()
│
├── ari_monitor.py
├── edm_monitor.py
├── rdi_monitor.py
├── logger.py
├── tracer.py
└── __init__.py
```

## Security & Auditing

### `/src/ai_pal/security/` - Audit Logs, Sanitization, Secrets

```
src/ai_pal/security/
├── audit_log.py               # Audit logging (16KB)
│   ├── AuditEventType enum
│   │   ├── LOGIN, LOGOUT, AUTH_FAILURE
│   │   ├── GATE_EVALUATION, GATE_PASSED, GATE_FAILED
│   │   ├── SECRET_DETECTED, SANITIZATION_APPLIED
│   │   ├── DATA_ACCESS, DATA_MODIFIED, DATA_DELETED
│   │   ├── MODEL_REQUEST, HIGH_COST_REQUEST
│   │   ├── ARI_SNAPSHOT, EDM_DEBT_DETECTED
│   │   └── SYSTEM_START, SYSTEM_STOP, ERROR
│   ├── AuditSeverity enum (DEBUG, INFO, WARNING, ERROR, CRITICAL)
│   ├── AuditEvent dataclass
│   ├── AuditLogger class
│   │   ├── log_event()
│   │   ├── log_gate_evaluation()
│   │   ├── log_plugin_event()
│   │   ├── log_security_event()
│   │   ├── log_model_request()
│   │   ├── log_data_access()
│   │   ├── query_events()
│   │   ├── cleanup_old_logs()
│   │   └── Features:
│   │       ├── JSON JSONL format
│   │       ├── Async queue-based
│   │       ├── 100MB file rotation
│   │       ├── 10 backup files
│   │       └── 90-day retention
│   └── get_audit_logger() singleton
│
├── credential_manager.py
├── sanitization.py
├── secret_scanner.py
└── __init__.py
```

## FFE (Fractal Flow Engine)

### `/src/ai_pal/ffe/` - Goal Management & Momentum

```
src/ai_pal/ffe/
├── models.py                  # FFE data models (20KB)
│   ├── StrengthType enum (ANALYTICAL, CREATIVE, SOCIAL, PRACTICAL, etc.)
│   ├── TaskComplexityLevel enum (ATOMIC, MICRO, MINI, MACRO, MEGA)
│   ├── TimeBlockSize enum (15, 30, 60, 90, 120 minutes)
│   ├── MomentumState enum (IDLE, WIN_STRENGTH, AFFIRM_PRIDE, PIVOT_DETECT, etc.)
│   ├── BottleneckReason enum (AVOIDED, DIFFICULT, BORING, ANXIETY_INDUCING, etc.)
│   ├── BottleneckType enum (CLARITY, SKILL, MOTIVATION, ANXIETY, COMPLEXITY)
│   ├── GoalStatus enum (PENDING, IN_PROGRESS, COMPLETED, SCOPED, etc.)
│   ├── SignatureStrength dataclass
│   ├── PersonalityProfile dataclass
│   ├── GoalPacket dataclass
│   ├── AtomicBlock dataclass
│   ├── MicroBottleneck dataclass
│   ├── BottleneckTask dataclass
│   ├── MomentumLoopState dataclass
│   ├── RewardMessage dataclass
│   ├── FiveBlockPlan dataclass
│   ├── ScopingSession dataclass
│   ├── SharedWin dataclass
│   ├── CreativeSandboxBlock dataclass
│   ├── MeaningNarrative dataclass
│   └── FFEMetrics dataclass
│
├── engine.py                  # FFE orchestrator
├── integration.py
├── component_interfaces.py
├── components/
│   ├── goal_ingestor.py
│   ├── scoping_agent.py
│   ├── strength_amplifier.py
│   ├── momentum_loop.py
│   ├── growth_scaffold.py
│   ├── reward_emitter.py
│   └── time_block_manager.py
├── interfaces/
│   ├── strength_interface.py
│   ├── progress_tapestry.py
│   ├── social_interface.py
│   ├── socratic_copilot.py
│   ├── curiosity_compass.py
│   ├── learn_about_me.py
│   └── teaching_interface.py
├── connectors/
│   └── personality_connector.py
├── modules/
│   ├── personality_discovery.py
│   ├── epic_meaning.py
│   ├── protege_pipeline.py
│   └── social/
└── __init__.py
```

## Core System

### `/src/ai_pal/core/` - Integrated AC System

```
src/ai_pal/core/
├── integrated_system.py       # Main AC system orchestrator
│   ├── IntegratedACSystem class
│   ├── SystemConfig dataclass
│   ├── process_request()
│   ├── get_user_profile()
│   └── All system initialization
│
├── config.py
├── orchestrator.py
├── credentials.py
├── hardware.py
├── privacy.py
├── plugin_manager.py
└── __init__.py
```

## Additional Components

### `/src/ai_pal/gates/` - Four Gates Framework
```
gates/
├── gate_system.py            # Gate orchestration
├── aho_tribunal.py           # Gate 3: Humanity Override
├── enhanced_tribunal.py
└── __init__.py
```

### `/src/ai_pal/improvement/` - AI Self-Improvement
```
improvement/
├── patch_manager.py          # Patch request workflow
├── self_improvement.py
├── lora_tuning.py
└── __init__.py
```

### `/src/ai_pal/models/` - LLM Providers
```
models/
├── base.py                   # Base model interface
├── anthropic_provider.py     # Claude API
├── openai_provider.py        # OpenAI API
├── google_provider.py        # Google Gemini
├── cohere_provider.py        # Cohere API
├── mistral_provider.py       # Mistral API
├── groq_provider.py          # Groq API
├── local.py                  # Local models
└── router.py                 # Model selection
```

### `/src/ai_pal/context/` - Context Management
```
context/
├── enhanced_context.py       # Personality/context storage
└── __init__.py
```

### `/src/ai_pal/storage/` - Data Persistence
```
storage/
└── database.py               # Database layer
```

### `/src/ai_pal/plugins/` - Plugin System
```
plugins/
├── base.py
├── manager.py
├── loader.py
├── registry.py
├── discovery.py
├── dependencies.py
├── sandbox.py
└── __init__.py
```

### `/src/ai_pal/modules/` - Feature Modules
```
modules/
├── base.py
├── learning.py
├── dream.py
├── ethics.py
├── echo_chamber_buster.py
├── personal_data.py
└── __init__.py
```

### `/src/ai_pal/ui/` - Dashboards & Visualization
```
ui/
├── agency_dashboard.py
├── ffe_dashboard.py
├── predictive_analytics.py
├── visualizations.py
└── __init__.py
```

## Data Flow

```
User Request
    ↓
GET_CURRENT_USER (authentication)
    ↓
POST /api/chat (main entry point)
    ↓
IntegratedACSystem.process_request()
    ↓
├─ ARI Monitor (check autonomy)
├─ Four Gates (validation)
├─ EDM Monitor (epistemic debt)
├─ Model Router (select LLM)
└─ FFE Engine (goal management)
    ↓
Record Metrics
Record Audit Log
    ↓
Return ChatResponse
```

## Configuration Files

Key environment configuration:
- `AI_PAL_DATA_DIR`: Data storage location
- `AI_PAL_CREDENTIALS`: Credentials path
- `CORS_ORIGINS`: CORS allowed origins
- `REDIS_URL`: Redis connection
- `ANTHROPIC_API_KEY`: Claude API
- `OPENAI_API_KEY`: OpenAI API

## Port Configuration

- **8000**: Main API (FastAPI)
- **8001**: AHO Tribunal (Separate service)
- **6379**: Redis (cache)
- **5432**: PostgreSQL (optional database)

## Key Statistics

- **Total API Files**: 3 (main.py, aho_tribunal.py, __init__.py)
- **Total Lines of API Code**: ~2,000
- **Monitoring Files**: 7 (health, metrics, ari_engine, monitors, logger, tracer)
- **Security Files**: 4 (audit_log, credentials, sanitization, secrets)
- **FFE Files**: 20+ (models, components, interfaces, modules, connectors)
- **Total Backend Files**: 173 across 47 directories

## Key Integration Points

1. **Authentication**: `get_current_user()` dependency
2. **AC System**: `get_ac_system()` singleton
3. **Metrics**: `get_metrics()` singleton + middleware
4. **Health**: `get_health_checker()` singleton
5. **Audit**: `get_audit_logger()` singleton
6. **ARI**: `ARIEngine` with three measurement methods
7. **FFE**: `FFEEngine` with momentum loops
8. **Gates**: Four-gate framework on every request
9. **Models**: Pluggable model router
10. **Tribunal**: Separate service for appeals
