# Background Job Queue System Implementation

## Overview

A production-ready background job queue system has been implemented for AI-Pal using Celery with Redis broker. This system enables asynchronous execution of long-running and scheduled tasks without blocking API responses.

## Architecture

### Components

1. **Celery Application** (`src/ai_pal/tasks/celery_app.py`)
   - Redis-based message broker and result backend
   - 6 task queues with priority support
   - Task routing by type
   - Auto-discovery of task modules

2. **Database Integration** (`src/ai_pal/storage/database.py`)
   - `BackgroundTaskDB` model for persistent task tracking
   - `BackgroundTaskRepository` for data access
   - Task metadata: status, timestamps, results, errors
   - Async-first design with SQLAlchemy

3. **Task Base Class** (`src/ai_pal/tasks/base_task.py`)
   - `AIpalTask` base class for all Celery tasks
   - Automatic retry with exponential backoff
   - Database persistence hooks
   - Error tracking and logging

4. **Task Modules** (5 implementations)
   - `ari_tasks.py`: ARI snapshot aggregation and trend analysis
   - `ffe_tasks.py`: FFE goal planning and progress tracking
   - `edm_tasks.py`: EDM batch analysis and misinformation detection
   - `model_tasks.py`: Model fine-tuning, evaluation, and benchmarking
   - `maintenance_tasks.py`: Audit log archival, database maintenance, cache cleanup

5. **REST API** (`src/ai_pal/api/tasks.py`)
   - Task submission endpoints
   - Status monitoring endpoints
   - Task management (cancel, retry)
   - Health check endpoint

6. **Main API Integration** (`src/ai_pal/api/main.py`)
   - Startup/shutdown events
   - Database initialization
   - Task system setup
   - Router registration

## Task Types Implemented

### 1. ARI Tasks (Autonomy Retention Index)
**File:** `src/ai_pal/tasks/ari_tasks.py`

#### aggregate_ari_snapshots
- **Purpose:** Aggregate ARI metrics over time windows
- **Parameters:** user_id (optional), time_window_hours (default: 24)
- **Returns:** Aggregated statistics with min/max/average per dimension
- **Queue:** `ari_analysis`

#### analyze_ari_trends
- **Purpose:** Detect agency decline patterns
- **Parameters:** user_id, lookback_days (default: 30), threshold_percent (default: 10)
- **Returns:** Trend analysis with alerts for significant declines
- **Queue:** `ari_analysis`

### 2. FFE Tasks (Fractal Flow Engine)
**File:** `src/ai_pal/tasks/ffe_tasks.py`

#### plan_ffe_goal
- **Purpose:** Long-running goal planning with fractal decomposition
- **Parameters:** goal_id, user_id, goal_description, complexity_level
- **Returns:** Atomic blocks with time estimates
- **Queue:** `ffe_planning`

#### track_ffe_progress
- **Purpose:** Track goal completion progress
- **Parameters:** goal_id, user_id
- **Returns:** Progress metrics and status
- **Queue:** `ffe_planning`

### 3. EDM Tasks (Epistemic Debt Management)
**File:** `src/ai_pal/tasks/edm_tasks.py`

#### edm_batch_analysis
- **Purpose:** Batch analysis of epistemic debt instances
- **Parameters:** user_id (optional), time_window_days, min_severity
- **Returns:** Analyzed debts grouped by severity
- **Queue:** `edm_analysis`

#### edm_track_resolutions
- **Purpose:** Track resolution progress
- **Parameters:** user_id, lookback_days (default: 30)
- **Returns:** Resolution metrics and trends
- **Queue:** `edm_analysis`

#### edm_detect_misinformation
- **Purpose:** Detect potential misinformation
- **Parameters:** user_id, interaction_ids (optional)
- **Returns:** Detection findings with confidence levels
- **Queue:** `edm_analysis`

### 4. Model Tasks
**File:** `src/ai_pal/tasks/model_tasks.py`

#### finetune_model
- **Purpose:** Fine-tune local models on user data
- **Parameters:** user_id, model_name, training_samples, learning_rate
- **Returns:** Training metrics (loss, accuracy, perplexity)
- **Queue:** `model_training`

#### evaluate_model
- **Purpose:** Evaluate model performance
- **Parameters:** user_id, model_name, test_samples
- **Returns:** Evaluation metrics and comparisons
- **Queue:** `model_training`

#### benchmark_model
- **Purpose:** Benchmark across scenarios
- **Parameters:** model_name, scenarios (optional)
- **Returns:** Per-scenario performance metrics
- **Queue:** `model_training`

### 5. Maintenance Tasks
**File:** `src/ai_pal/tasks/maintenance_tasks.py`

#### archive_audit_logs
- **Purpose:** Archive old audit logs
- **Parameters:** days_to_keep (default: 90), archive_location
- **Returns:** Archival statistics
- **Queue:** `maintenance`

#### maintain_database
- **Purpose:** Database optimization
- **Parameters:** optimization_level (light/standard/heavy)
- **Returns:** Maintenance operations performed
- **Queue:** `maintenance`

#### cleanup_cache
- **Purpose:** Clean up cache
- **Parameters:** max_age_hours (default: 24), cleanup_expired_only (default: true)
- **Returns:** Cleanup statistics
- **Queue:** `maintenance`

#### enforce_retention_policy
- **Purpose:** Enforce data retention policies
- **Parameters:** policy (optional, uses defaults)
- **Returns:** Policy enforcement results
- **Queue:** `maintenance`

## REST API Endpoints

### Task Submission

```bash
# ARI Snapshot Aggregation
POST /api/tasks/ari/aggregate-snapshots
{
  "task_type": "ari_snapshot",
  "user_id": "user123",
  "priority": 5,
  "parameters": {
    "time_window_hours": 24
  }
}

# FFE Goal Planning
POST /api/tasks/ffe/plan-goal
{
  "task_type": "ffe_planning",
  "user_id": "user123",
  "priority": 7,
  "parameters": {
    "goal_id": "goal-uuid",
    "goal_description": "Complete project X",
    "complexity_level": "medium"
  }
}

# EDM Batch Analysis
POST /api/tasks/edm/batch-analysis
{
  "task_type": "edm_analysis",
  "user_id": "user123",
  "priority": 5,
  "parameters": {
    "time_window_days": 7,
    "min_severity": "low"
  }
}
```

### Task Monitoring

```bash
# Get task status
GET /api/tasks/status/{task_id}

# List tasks
GET /api/tasks/list?status=pending&limit=20

# Get pending tasks
GET /api/tasks/pending?limit=10

# Get failed tasks
GET /api/tasks/failed?limit=10

# Health check
GET /api/tasks/health
```

### Task Management

```bash
# Cancel a task
DELETE /api/tasks/{task_id}

# Retry a failed task
POST /api/tasks/{task_id}/retry
```

## Configuration

### Environment Variables

```bash
# Celery/Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./ai_pal.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ai_pal

DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Cors
CORS_ORIGINS=*
```

### Task Queues and Routing

The system uses 6 queues with automatic routing:

| Queue | Task Type | Priority | Max Priority |
|-------|-----------|----------|--------------|
| `ari_analysis` | ARI tasks | 5 | 10 |
| `ffe_planning` | FFE tasks | 5 | 10 |
| `edm_analysis` | EDM tasks | 5 | 10 |
| `model_training` | Model tasks | 5 | 10 |
| `maintenance` | Maintenance | 5 | 5 |
| `default` | Other tasks | 5 | 10 |

## Running the System

### Start Redis (required)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or using Homebrew (macOS)
brew install redis
redis-server
```

### Start Celery Worker

```bash
# Single worker process
celery -A ai_pal.tasks.celery_app worker --loglevel=info

# Multiple workers with concurrency
celery -A ai_pal.tasks.celery_app worker --concurrency=4 --loglevel=info

# Separate workers for different queues
celery -A ai_pal.tasks.celery_app worker -Q ari_analysis -n worker1@%h
celery -A ai_pal.tasks.celery_app worker -Q ffe_planning -n worker2@%h
celery -A ai_pal.tasks.celery_app worker -Q maintenance -n worker3@%h
```

### Start Flower (Celery Monitoring)

```bash
# Install flower if needed
pip install flower

# Start monitoring dashboard
celery -A ai_pal.tasks.celery_app flower --port=5555

# Access at http://localhost:5555
```

### Start API Server

```bash
# Development
python src/ai_pal/api/main.py

# Production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 ai_pal.api.main:app
```

## Database Schema

### BackgroundTaskDB Table

```sql
CREATE TABLE background_tasks (
    id INTEGER PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,

    created_at DATETIME NOT NULL,
    started_at DATETIME,
    completed_at DATETIME,

    result TEXT,  -- JSON serialized result
    error_message TEXT,
    error_traceback TEXT,

    attempts INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    args TEXT,  -- JSON serialized args
    kwargs TEXT,  -- JSON serialized kwargs

    duration_seconds FLOAT,
    celery_task_id VARCHAR(255),

    INDEX(task_name, status, created_at),
    INDEX(user_id, status),
    INDEX(celery_task_id)
);
```

## Error Handling and Retry Strategy

### Automatic Retry

Tasks automatically retry with exponential backoff:
- Initial delay: 60 seconds (configurable per task)
- Max retries: 3 (configurable per task)
- Backoff multiplier: 2x per retry

Example retry delays:
- Attempt 1: Immediate
- Attempt 2: 60s (2^0 × 60)
- Attempt 3: 120s (2^1 × 60)
- Attempt 4: 240s (2^2 × 60)

### Task Status States

- `pending`: Task submitted, not yet started
- `running`: Task currently executing
- `completed`: Task finished successfully
- `failed`: Task failed after max retries
- `cancelled`: Task cancelled by user

### Error Tracking

All errors are logged to:
1. Application logs (via loguru)
2. Database (error_message, error_traceback columns)
3. Celery result backend (Redis)

## Performance Considerations

### Database Optimization

- Composite indexes on frequently queried columns
- Async database operations (no blocking)
- Connection pooling (configurable pool_size, max_overflow)
- Automatic cleanup of old task records (7+ days)

### Task Optimization

- Priority queues prevent low-priority tasks from blocking high-priority work
- Worker concurrency configurable per deployment
- Task timeouts prevent hanging tasks (30 min hard limit, 25 min soft limit)
- Result expiration (1 hour) prevents result backend bloat

### Scaling Strategy

1. **Horizontal Scaling:** Multiple worker processes/machines
2. **Queue Separation:** Dedicated workers for specific task types
3. **Task Sharding:** Large datasets can be split into subtasks
4. **Database Optimization:** Use PostgreSQL for production scale

## Monitoring and Observability

### Flower Dashboard

Celery's Flower UI provides:
- Real-time worker status
- Task execution history
- Task details and errors
- Performance graphs

### Database Queries

```python
# Get pending tasks
GET /api/tasks/pending

# Get user's task history
GET /api/tasks/list?user_id=user123

# Get failed tasks for investigation
GET /api/tasks/failed?limit=50

# Task details
GET /api/tasks/status/{task_id}
```

### Logging

All task execution is logged with:
- Task ID and name
- User ID (if applicable)
- Execution duration
- Success/failure status
- Error details (if failed)

## Testing

### Unit Tests

```python
# Test task execution
from ai_pal.tasks.ari_tasks import aggregate_ari_snapshots

result = aggregate_ari_snapshots.delay(
    user_id="test_user",
    time_window_hours=24
)

task_result = result.get(timeout=30)
assert task_result["aggregated_count"] >= 0
```

### Integration Tests

```python
# Test full workflow
POST /api/tasks/ari/aggregate-snapshots
# Check response: task_id, status=pending

GET /api/tasks/status/{task_id}
# Poll until status = completed or failed

GET /api/tasks/status/{task_id}
# Verify result in response
```

## Production Deployment

### Docker Compose Setup

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres/ai_pal
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres

  worker:
    build: .
    command: celery -A ai_pal.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres/ai_pal
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres

  flower:
    build: .
    command: celery -A ai_pal.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ai_pal
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes Deployment

See `kubernetes/` directory for Helm charts and manifests.

## Future Enhancements

1. **Task Scheduling:** Implement periodic task scheduling with APScheduler
2. **Dashboard UI:** Build React components for task monitoring
3. **Advanced Monitoring:** Prometheus metrics and Grafana dashboards
4. **Task Grouping:** Support task chains and workflows
5. **Rate Limiting:** Per-user task submission limits
6. **Task Prioritization:** Dynamic priority adjustment
7. **Task Webhooks:** Notify external systems on task completion

## Troubleshooting

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check Redis info
redis-cli info
```

### Celery Worker Not Starting

```bash
# Check if Redis is running
redis-cli ping

# Check database connection
python -c "from ai_pal.storage.database import DatabaseManager; dm = DatabaseManager(); print('OK')"

# Start worker with debug output
celery -A ai_pal.tasks.celery_app worker --loglevel=debug
```

### Tasks Not Executing

1. Verify Redis is running (`redis-cli ping`)
2. Verify worker is running (`celery inspect active`)
3. Check task queue (`celery inspect active_queues`)
4. Review logs for errors

## References

- [Celery Documentation](https://docs.celeryproject.io/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
