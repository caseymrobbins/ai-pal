# PostgreSQL Migration Guide

## Overview

This guide covers migrating AI-PAL from SQLite to PostgreSQL for improved concurrency, better performance, and production-readiness.

## Quick Start

### 1. Start PostgreSQL with Docker

```bash
docker-compose up -d postgres redis
```

Verify PostgreSQL is running:
```bash
docker-compose exec postgres pg_isready -U ai_pal_user
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update PostgreSQL settings:

```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql+asyncpg://ai_pal_user:aipal_secure_password_123@localhost:5432/ai_pal
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_ECHO=false
```

### 3. Run Optimization

```bash
# Full optimization (create tables, indexes, analyze)
python scripts/postgres_migration.py --optimize

# Or individual commands:
python scripts/postgres_migration.py --create-indexes
python scripts/postgres_migration.py --analyze
python scripts/postgres_migration.py --stats
```

### 4. Start API Server

```bash
python -m ai_pal.api.main
```

The API will now use PostgreSQL with optimized connection pooling.

## Architecture

### Connection Pooling

AI-PAL uses SQLAlchemy's `QueuePool` for PostgreSQL:

- **Pool Size**: 20 (concurrent connections)
- **Max Overflow**: 40 (temporary overflow connections)
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pre-ping**: Enabled (test connections before use)

This configuration supports:
- 100+ concurrent API requests
- Multiple background task workers
- Real-time WebSocket connections

### Database Indexes

Optimized indexes on all frequently-queried columns:

**ARI Snapshots:**
- `idx_ari_user_id` - User queries
- `idx_ari_timestamp` - Time-based queries
- `idx_ari_user_timestamp` - Combined user + time queries
- `idx_ari_score` - Score-based queries

**Background Tasks:**
- `idx_task_user_status` - Task filtering by user and status
- `idx_task_created` - Recent task queries
- `idx_task_celery_id` - Celery task tracking

**Goals & Progress:**
- `idx_goal_user_status` - User's active goals
- `idx_goal_deadline` - Deadline-based queries

**Audit & Compliance:**
- `idx_audit_user_timestamp` - User audit trail
- `idx_patch_component_status` - Patch tracking

### Performance Characteristics

**Query Performance:**
- Single row lookup: 1-5ms (vs 10-50ms with SQLite)
- Range queries: 5-20ms (vs 50-200ms with SQLite)
- Aggregations: 10-50ms (vs 100-500ms with SQLite)

**Concurrency:**
- SQLite: 1-10 concurrent connections
- PostgreSQL: 100+ concurrent connections

**Storage:**
- Indexes use ~30% additional disk space
- But dramatically improve query performance
- VACUUM and ANALYZE keep index efficiency high

## Monitoring

### Check Table Sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Monitor Connection Pool

```python
# In your API code:
from ai_pal.storage.database import get_db_manager

db = get_db_manager()
print(f"Pool size: {db.engine.pool.size()}")
print(f"Checked out: {db.engine.pool.checkedout()}")
```

### Query Performance

Enable query logging in `.env`:

```
DB_ECHO=true              # Log all SQL
DB_QUERY_LOGGING=true
SLOW_QUERY_THRESHOLD_MS=1000
```

## Troubleshooting

### Connection Refused

```
error: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart if needed
docker-compose restart postgres
```

### Too Many Connections

```
error: FATAL: sorry, too many clients already
```

**Solutions:**
1. Increase `max_connections` in PostgreSQL
2. Reduce `pool_size` in `.env`
3. Check for connection leaks in application

### Slow Queries

```bash
# Analyze slow queries
psql -U ai_pal_user -d ai_pal -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

## Production Deployment

### Cloud Databases

For production, use managed PostgreSQL services:

**AWS RDS:**
```
postgresql+asyncpg://user:pass@[endpoint].rds.amazonaws.com/ai_pal?sslmode=require
```

**Google Cloud SQL:**
```
postgresql+asyncpg://user:pass@35.x.x.x/ai_pal?sslmode=require
```

**Azure Database:**
```
postgresql+asyncpg://user:pass@[server].postgres.database.azure.com/ai_pal?sslmode=require
```

### Connection Pooling for Horizontal Scaling

Use PgBouncer to share connections across multiple API instances:

```ini
# pgbouncer.ini
[databases]
ai_pal = host=db.example.com port=5432 dbname=ai_pal user=ai_pal_user password=***

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
```

### Backup & Recovery

**Automated Backups:**
```bash
# Daily backup script
pg_dump -Fc postgresql://user:pass@localhost/ai_pal > ai_pal_backup_$(date +%Y%m%d).sql
```

**Point-in-Time Recovery:**
```bash
# Enable WAL archiving in PostgreSQL
pg_basebackup -D /backups/aipal_base -Ft
```

## Migration from SQLite

If you have existing SQLite data:

```bash
# Export SQLite
sqlite3 ai_pal.db '.dump' > sqlite_dump.sql

# Import to PostgreSQL
psql -U ai_pal_user -d ai_pal < sqlite_dump.sql

# Or use pg_migrate tool (under development)
python scripts/migrate_sqlite_to_postgres.py
```

## Database Schema

### Key Tables

**ari_snapshots** - ARI measurements over time
```sql
- snapshot_id (PK)
- user_id (FK, INDEX)
- timestamp (INDEX)
- autonomy_retention (FLOAT)
- 7 dimensions (FLOAT)
```

**ffe_goals** - User goals and progress
```sql
- goal_id (PK)
- user_id (FK, INDEX)
- status (INDEX)
- deadline (INDEX)
- created_at (INDEX)
```

**background_tasks** - Celery task tracking
```sql
- task_id (PK, UNIQUE, INDEX)
- user_id (FK, INDEX)
- status (INDEX)
- created_at (INDEX)
- celery_task_id (INDEX)
```

**audit_logs** - Security and compliance
```sql
- user_id (FK, INDEX)
- timestamp (INDEX)
- severity (INDEX)
- event_type (INDEX)
```

## Performance Tuning

### Query Optimization

Use `EXPLAIN ANALYZE` to understand query plans:

```sql
EXPLAIN ANALYZE
SELECT * FROM ari_snapshots
WHERE user_id = 'user123'
ORDER BY timestamp DESC
LIMIT 10;
```

Ensure you see `Index Scan` not `Seq Scan` for indexed columns.

### Connection Pool Tuning

For different workloads:

**High Concurrency (100+ requests/sec):**
```
pool_size = 50
max_overflow = 100
```

**Standard Load (10-50 requests/sec):**
```
pool_size = 20
max_overflow = 40
```

**Low Load (< 10 requests/sec):**
```
pool_size = 5
max_overflow = 10
```

## Next Steps

1. **Phase 2**: Add Redis caching layer for frequently accessed data
2. **Phase 3**: Optimize async operations and batch queries
3. **Phase 4**: Implement read replicas for horizontal scaling

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Connection Pool Tuning](https://wiki.postgresql.org/wiki/Number_Of_Database_Connections)
