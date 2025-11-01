# AI-PAL Deployment Guide

This guide covers deploying AI-PAL in various environments from development to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Configuration](#configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB
- OS: Linux, macOS, or Windows with WSL2

**Recommended**:
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB SSD
- OS: Linux (Ubuntu 22.04 LTS)

### Software Dependencies

- Python 3.11 or higher
- pip 23.0+
- Git
- (Optional) Docker 24.0+
- (Optional) Kubernetes 1.28+

## Development Deployment

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/ai-pal.git
cd ai-pal

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -e .

# 4. Install development dependencies
pip install -e ".[dev]"

# 5. Run tests to verify installation
pytest tests/ -v

# 6. Set up pre-commit hooks (optional but recommended)
./scripts/gates/install_hooks.sh
```

### Configuration

Create `.env` file in project root:

```bash
# Model API Keys (optional - for cloud models)
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# Data Directory
AI_PAL_DATA_DIR=./data

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Features
ENABLE_ARI_MONITORING=true
ENABLE_EDM_MONITORING=true
ENABLE_GATES=true
ENABLE_FFE=true

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_SECONDS=30
```

### Running Locally

```bash
# Start in development mode
python -m ai_pal.main

# Or use the CLI
ai-pal --help
```

### Development with Local Models

```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh

# 2. Pull a model
ollama pull phi-2

# 3. Configure AI-PAL to use local models
export AI_PAL_DEFAULT_PROVIDER=local
export AI_PAL_LOCAL_MODEL=phi-2

# 4. Run
python -m ai_pal.main
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Security audit completed
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Rollback plan prepared
- [ ] API keys secured
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates obtained
- [ ] Load balancer configured

### Production Environment Setup

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    build-essential \
    git \
    nginx \
    postgresql-14 \
    redis-server \
    supervisor

# Create ai-pal user
sudo useradd -r -s /bin/bash -d /opt/ai-pal ai-pal
sudo mkdir -p /opt/ai-pal
sudo chown ai-pal:ai-pal /opt/ai-pal
```

#### 2. Application Installation

```bash
# Switch to ai-pal user
sudo su - ai-pal

# Clone repository
cd /opt/ai-pal
git clone https://github.com/your-org/ai-pal.git app
cd app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install -e .
pip install gunicorn uvicorn[standard]
```

#### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createuser ai_pal
sudo -u postgres createdb ai_pal_production -O ai_pal

# Set password
sudo -u postgres psql -c "ALTER USER ai_pal WITH PASSWORD 'your-secure-password';"

# Run migrations (if applicable)
python scripts/db/migrate.py
```

#### 4. Environment Configuration

Create `/opt/ai-pal/app/.env.production`:

```bash
# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://ai_pal:your-secure-password@localhost/ai_pal_production

# Redis
REDIS_URL=redis://localhost:6379/0

# Model APIs
ANTHROPIC_API_KEY=your-production-key
OPENAI_API_KEY=your-production-key

# Security
SECRET_KEY=your-secret-key-generate-with-openssl
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Performance
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT_SECONDS=30
WORKER_COUNT=4

# Monitoring
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_DIR=/var/log/ai-pal/audit
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# Features
ENABLE_ARI_MONITORING=true
ENABLE_EDM_MONITORING=true
ENABLE_GATES=true
ENABLE_FFE=true
ENABLE_PLUGINS=true

# Data
DATA_DIR=/var/lib/ai-pal/data
BACKUP_DIR=/var/lib/ai-pal/backups
DATA_RETENTION_DAYS=90
```

#### 5. Systemd Service

Create `/etc/systemd/system/ai-pal.service`:

```ini
[Unit]
Description=AI-PAL Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=ai-pal
Group=ai-pal
WorkingDirectory=/opt/ai-pal/app
Environment="PATH=/opt/ai-pal/app/venv/bin"
EnvironmentFile=/opt/ai-pal/app/.env.production

ExecStart=/opt/ai-pal/app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/ai-pal/access.log \
    --error-logfile /var/log/ai-pal/error.log \
    --log-level info \
    ai_pal.api.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 6. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/ai-pal`:

```nginx
upstream ai_pal {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/ai-pal-access.log;
    error_log /var/log/nginx/ai-pal-error.log;

    # Max request size (for large model inputs)
    client_max_body_size 10M;

    location / {
        proxy_pass http://ai_pal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # WebSocket support (for streaming)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://ai_pal/health;
        access_log off;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        proxy_pass http://ai_pal/metrics;
        allow 10.0.0.0/8;  # Internal network only
        deny all;
    }
}
```

#### 7. Start Services

```bash
# Create log directories
sudo mkdir -p /var/log/ai-pal
sudo chown ai-pal:ai-pal /var/log/ai-pal

# Enable and start services
sudo systemctl enable ai-pal
sudo systemctl start ai-pal
sudo systemctl status ai-pal

# Enable nginx
sudo ln -s /etc/nginx/sites-available/ai-pal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

## Docker Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: ai-pal
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_pal
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:14-alpine
    container_name: ai-pal-db
    restart: always
    environment:
      - POSTGRES_DB=ai_pal
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: ai-pal-redis
    restart: always
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    container_name: ai-pal-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY setup.py .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data /app/logs

# Create non-root user
RUN useradd -m -u 1000 aipal && \
    chown -R aipal:aipal /app

USER aipal

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "ai_pal.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy with Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

## Kubernetes Deployment

See [kubernetes/](../../kubernetes/) directory for complete manifests.

### Quick Deploy

```bash
# Create namespace
kubectl create namespace ai-pal

# Apply configurations
kubectl apply -f kubernetes/config/

# Apply secrets
kubectl create secret generic ai-pal-secrets \
    --from-env-file=.env.production \
    -n ai-pal

# Deploy database
kubectl apply -f kubernetes/postgres/

# Deploy Redis
kubectl apply -f kubernetes/redis/

# Deploy application
kubectl apply -f kubernetes/app/

# Deploy ingress
kubectl apply -f kubernetes/ingress/

# Check status
kubectl get pods -n ai-pal
kubectl get svc -n ai-pal
```

## Configuration

### Environment Variables

See `.env.example` for all available options.

**Critical Variables**:
- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

**Feature Flags**:
- `ENABLE_ARI_MONITORING`: Enable agency tracking
- `ENABLE_EDM_MONITORING`: Enable epistemic debt detection
- `ENABLE_GATES`: Enable 4-gate system
- `ENABLE_FFE`: Enable Fractal Flow Engine
- `ENABLE_PLUGINS`: Enable plugin system

### Secrets Management

**Development**: Use `.env` files (never commit!)

**Production**: Use secrets management:

**AWS Secrets Manager**:
```bash
# Store secret
aws secretsmanager create-secret \
    --name ai-pal/production/api-keys \
    --secret-string file://.env.production

# Retrieve in application
secret = boto3.client('secretsmanager').get_secret_value(
    SecretId='ai-pal/production/api-keys'
)
```

**Kubernetes Secrets**:
```bash
kubectl create secret generic ai-pal-secrets \
    --from-env-file=.env.production \
    -n ai-pal
```

## Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl https://your-domain.com/health

# Expected response:
{
    "status": "healthy",
    "version": "1.0.0",
    "components": {
        "database": "healthy",
        "redis": "healthy",
        "gates": "healthy",
        "orchestrator": "healthy"
    }
}
```

### Logs

```bash
# Application logs
tail -f /var/log/ai-pal/error.log
tail -f /var/log/ai-pal/access.log

# Audit logs
tail -f /var/log/ai-pal/audit/audit_*.jsonl

# Systemd logs
sudo journalctl -u ai-pal -f
```

### Metrics

Access Prometheus metrics:
```bash
curl http://localhost:9090/metrics
```

Key metrics:
- `ai_pal_requests_total`: Total requests
- `ai_pal_request_duration_seconds`: Request latency
- `ai_pal_gate_failures_total`: Gate failures
- `ai_pal_ari_snapshots_total`: ARI snapshots recorded
- `ai_pal_model_costs_usd_total`: Model API costs

### Backups

```bash
# Database backup
pg_dump ai_pal_production > backup_$(date +%Y%m%d).sql

# Data directory backup
tar -czf data_backup_$(date +%Y%m%d).tar.gz /var/lib/ai-pal/data

# Automated backups (cron)
0 2 * * * /opt/ai-pal/scripts/backup.sh
```

### Updates

```bash
# Pull latest code
cd /opt/ai-pal/app
sudo -u ai-pal git pull

# Activate venv
sudo -u ai-pal bash
source venv/bin/activate

# Update dependencies
pip install -e . --upgrade

# Run migrations if needed
python scripts/db/migrate.py

# Restart service
exit
sudo systemctl restart ai-pal

# Verify
curl https://your-domain.com/health
```

## Troubleshooting

### Application won't start

```bash
# Check logs
sudo journalctl -u ai-pal -n 100

# Common issues:
# 1. Missing environment variables
grep -v '^#' .env.production | grep -v '^$'

# 2. Database connection
psql -U ai_pal -d ai_pal_production -h localhost

# 3. Port already in use
sudo lsof -i :8000
```

### High memory usage

```bash
# Check process memory
ps aux | grep ai-pal

# Monitor in real-time
htop

# Solutions:
# 1. Reduce worker count
# 2. Increase worker memory limit
# 3. Enable request queuing
```

### Slow responses

```bash
# Check metrics
curl http://localhost:9090/metrics | grep request_duration

# Profile a request
time curl -X POST https://your-domain.com/api/v1/request \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}'

# Solutions:
# 1. Check database query performance
# 2. Review model selection (use faster models)
# 3. Enable caching
# 4. Scale horizontally
```

### Gate failures

```bash
# Check gate logs
grep "gate_failed" /var/log/ai-pal/audit/audit_*.jsonl | tail -20

# Review gate configuration
cat .env.production | grep GATE

# Test individual gates
python scripts/gates/test_gates.py
```

## Security Hardening

### Firewall

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Fail2Ban

```bash
# Install
sudo apt install fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Add nginx jail
[nginx-ai-pal]
enabled = true
port = http,https
filter = nginx-ai-pal
logpath = /var/log/nginx/ai-pal-access.log
maxretry = 5
bantime = 3600
```

### Regular Security Updates

```bash
# Schedule weekly updates
sudo crontab -e

# Add:
0 3 * * 0 apt update && apt upgrade -y && systemctl restart ai-pal
```

## Performance Tuning

### Database

```sql
-- Add indexes
CREATE INDEX idx_ari_snapshots_user_timestamp
ON ari_snapshots(user_id, timestamp DESC);

CREATE INDEX idx_epistemic_debts_task
ON epistemic_debts(task_id, severity);

-- Configure PostgreSQL
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Caching

```python
# Enable response caching
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE_MB=1000
```

### Worker Tuning

```bash
# Calculate optimal workers
workers = (2 * CPU_cores) + 1

# For 4-core machine:
WORKER_COUNT=9
```

## Scaling

### Horizontal Scaling

```bash
# Add more application servers
# 1. Deploy to new server
# 2. Add to load balancer
# 3. Share Redis and PostgreSQL
```

### Load Balancing

```nginx
upstream ai_pal {
    least_conn;
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}
```

### Database Read Replicas

```python
DATABASE_READ_URLS=postgresql://ai_pal:password@replica1:5432/ai_pal,postgresql://ai_pal:password@replica2:5432/ai_pal
```

## Support

- **Documentation**: https://docs.ai-pal.dev
- **Issues**: https://github.com/your-org/ai-pal/issues
- **Community**: https://community.ai-pal.dev

---

**Production Deployment Checklist**: See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)
