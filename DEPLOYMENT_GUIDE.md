# AI-Pal Deployment Guide

This guide covers deploying AI-Pal using Docker Compose (development) and Kubernetes (production).

## Table of Contents

1. [Quick Start with Docker Compose](#quick-start-with-docker-compose)
2. [Docker Image Building](#docker-image-building)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Configuration Management](#configuration-management)
5. [Health Checks & Monitoring](#health-checks--monitoring)
6. [Scaling & Performance](#scaling--performance)
7. [Troubleshooting](#troubleshooting)
8. [Production Checklist](#production-checklist)

## Quick Start with Docker Compose

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Setup

1. **Create environment file:**

```bash
cd ai-pal
cp .env.example .env
```

Edit `.env` to set credentials:

```env
DB_USER=aipal
DB_PASSWORD=STRONG_PASSWORD_HERE
REDIS_PASSWORD=ANOTHER_STRONG_PASSWORD
LOG_LEVEL=info
```

2. **Start all services:**

```bash
docker-compose up -d
```

3. **Initialize database:**

```bash
docker-compose exec api python -m ai_pal.storage.database create_tables
```

4. **Verify services are running:**

```bash
docker-compose ps
docker-compose logs -f
```

5. **Access the services:**

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/tasks/health
- **Flower (Task Monitoring)**: http://localhost:5555 (admin:flower_dev_password)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Common Docker Compose Commands

```bash
# View logs
docker-compose logs api
docker-compose logs -f worker-ari

# Stop all services
docker-compose down

# Remove all volumes (careful!)
docker-compose down -v

# Restart a specific service
docker-compose restart api

# Scale workers
docker-compose up -d --scale worker-ari=3

# Execute command in container
docker-compose exec api bash
```

## Docker Image Building

### Building Images

```bash
# Build API image
docker build -t ai-pal:api-latest -f Dockerfile.api .

# Build Worker image
docker build -t ai-pal:worker-latest -f Dockerfile.worker .

# Tag for registry
docker tag ai-pal:api-latest myregistry.azurecr.io/ai-pal:api-v1.0
docker tag ai-pal:worker-latest myregistry.azurecr.io/ai-pal:worker-v1.0

# Push to registry
docker push myregistry.azurecr.io/ai-pal:api-v1.0
docker push myregistry.azurecr.io/ai-pal:worker-v1.0
```

### Image Verification

```bash
# Test image
docker run --rm ai-pal:api-latest --help
docker run --rm ai-pal:worker-latest celery --help

# Check image size
docker images ai-pal

# Inspect image
docker inspect ai-pal:api-latest
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Storage class available
- Ingress controller (nginx recommended)
- cert-manager (for TLS)

### Installation Steps

1. **Create namespace and secrets:**

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
```

2. **Edit secrets with production values:**

```bash
kubectl edit secret ai-pal-secrets -n ai-pal
```

3. **Create storage:**

```bash
kubectl apply -f k8s/03-storage.yaml
```

4. **Deploy databases (PostgreSQL & Redis):**

```bash
kubectl apply -f k8s/10-postgres.yaml
kubectl apply -f k8s/11-redis.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n ai-pal --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n ai-pal --timeout=300s
```

5. **Deploy API service:**

```bash
kubectl apply -f k8s/20-api-service.yaml

# Wait for deployment
kubectl rollout status deployment/api -n ai-pal
```

6. **Deploy Celery workers:**

```bash
kubectl apply -f k8s/21-celery-workers.yaml

# Wait for workers
kubectl get pods -n ai-pal -l app=worker
```

7. **Deploy Flower monitoring:**

```bash
kubectl apply -f k8s/22-flower.yaml
```

8. **Setup Ingress (update hostnames first):**

Edit `k8s/30-ingress.yaml` and update:
- `api.example.com` → your API domain
- `flower.example.com` → your Flower domain

```bash
kubectl apply -f k8s/30-ingress.yaml
```

### Verification

```bash
# Check deployments
kubectl get deployments -n ai-pal
kubectl get pods -n ai-pal

# Check services
kubectl get svc -n ai-pal

# Check ingress
kubectl get ingress -n ai-pal

# View logs
kubectl logs -f deployment/api -n ai-pal
kubectl logs -f deployment/worker-ari -n ai-pal

# Test API
kubectl port-forward svc/api 8000:8000 -n ai-pal
curl http://localhost:8000/api/tasks/health
```

## Configuration Management

### Environment Variables

Create `.env` file with:

```env
# Database
DB_USER=aipal
DB_PASSWORD=strong_password
DB_NAME=aipal

# Redis
REDIS_PASSWORD=strong_password

# API
LOG_LEVEL=info
API_WORKERS=4

# Celery
CELERY_CONCURRENCY=4

# Flower
FLOWER_USER=admin
FLOWER_PASSWORD=strong_password
```

### ConfigMap Updates

```bash
# Edit ConfigMap
kubectl edit configmap ai-pal-config -n ai-pal

# Restart pods to pick up changes
kubectl rollout restart deployment/api -n ai-pal
kubectl rollout restart deployment/worker-ari -n ai-pal
```

### Secrets Rotation

```bash
# Update secret
kubectl patch secret ai-pal-secrets -n ai-pal -p '{"data":{"DB_PASSWORD":"'$(echo -n 'new_password' | base64)'"}}'

# Restart pods
kubectl rollout restart deployment/api -n ai-pal
kubectl rollout restart deployment/worker-ari -n ai-pal
```

## Health Checks & Monitoring

### API Health Check

```bash
curl http://localhost:8000/api/tasks/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "celery": "ready",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Worker Health

```bash
# Via Flower UI
# Check worker status in http://localhost:5555

# Via kubectl
kubectl get pods -n ai-pal -l app=worker -o wide
```

### Database Health

```bash
# PostgreSQL
kubectl exec -it postgres-0 -n ai-pal -- pg_isready

# Redis
kubectl exec -it redis-0 -n ai-pal -- redis-cli -a $(kubectl get secret ai-pal-secrets -n ai-pal -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d) ping
```

### Monitoring with Prometheus

The deployments include Prometheus scrape annotations. Configure Prometheus to scrape:

```yaml
scrape_configs:
- job_name: 'ai-pal'
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
      - ai-pal
```

## Scaling & Performance

### Horizontal Pod Autoscaling

API autoscaling is configured in `20-api-service.yaml`:

```bash
# Check HPA status
kubectl get hpa -n ai-pal
kubectl describe hpa api-hpa -n ai-pal
```

### Manual Scaling

```bash
# Scale API
kubectl scale deployment api --replicas=5 -n ai-pal

# Scale specific worker
kubectl scale deployment worker-ari --replicas=4 -n ai-pal

# Check scale
kubectl get pods -n ai-pal -l app=api
```

### Resource Optimization

Monitor resource usage:

```bash
# Pod resource usage
kubectl top pods -n ai-pal

# Node resource usage
kubectl top nodes

# Detailed metrics
kubectl describe node <node-name>
```

Adjust resource requests/limits in manifests as needed.

### Queue Monitoring

Monitor queue depths via Flower:
- http://localhost:5555/tasks
- Check pending task counts
- Monitor worker capacity

## Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n ai-pal

# View logs
kubectl logs <pod-name> -n ai-pal
kubectl logs <pod-name> -n ai-pal --previous

# Check resource availability
kubectl describe node <node-name>
```

### Database connection errors

```bash
# Verify PostgreSQL is running
kubectl get pod postgres-0 -n ai-pal
kubectl logs postgres-0 -n ai-pal

# Test connection from pod
kubectl run -it --rm --image=postgres:15-alpine psql-test -- \
  psql -h postgres -U aipal -d aipal -c "SELECT version();"
```

### Redis connection errors

```bash
# Verify Redis is running
kubectl get pod redis-0 -n ai-pal
kubectl logs redis-0 -n ai-pal

# Test connection
kubectl run -it --rm --image=redis:7-alpine redis-test -- \
  redis-cli -h redis -a $(kubectl get secret ai-pal-secrets -n ai-pal -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d) ping
```

### Worker not processing tasks

```bash
# Check worker status in Flower
# http://localhost:5555/workers

# View worker logs
kubectl logs deployment/worker-ari -n ai-pal -f

# Check queue depth
kubectl exec redis-0 -n ai-pal -- redis-cli -a password LLEN celery
```

### Persistent volume issues

```bash
# Check PVC status
kubectl get pvc -n ai-pal
kubectl describe pvc postgres-pvc -n ai-pal

# Check node storage
kubectl get pv
kubectl describe pv <pv-name>
```

## Production Checklist

- [ ] Update all secrets in `k8s/02-secrets.yaml` with strong passwords
- [ ] Update hostnames in `k8s/30-ingress.yaml`
- [ ] Enable RBAC and network policies
- [ ] Configure ingress TLS certificates
- [ ] Setup backup for PostgreSQL
- [ ] Setup backup for Redis
- [ ] Configure log aggregation (ELK, Splunk, etc.)
- [ ] Setup monitoring and alerting (Prometheus + Grafana)
- [ ] Configure resource limits based on your workload
- [ ] Setup pod disruption budgets
- [ ] Configure registry authentication if using private registry
- [ ] Test failover and recovery procedures
- [ ] Document runbooks for common operations
- [ ] Setup automated backup tests
- [ ] Configure cluster autoscaling
- [ ] Setup rate limiting on Ingress
- [ ] Enable API authentication/authorization
- [ ] Configure audit logging
- [ ] Performance test under expected load
- [ ] Document scaling thresholds

## Performance Tuning

### Database

```sql
-- PostgreSQL tuning (in k8s/10-postgres.yaml)
shared_buffers=256MB
max_connections=200
work_mem=4MB
maintenance_work_mem=64MB
checkpoint_completion_target=0.9
wal_buffers=16MB
default_statistics_target=100
random_page_cost=1.1
effective_cache_size=1GB
```

### Redis

```bash
# Redis tuning (in k8s/11-redis.yaml)
maxmemory=1gb
maxmemory-policy=allkeys-lru
appendonly=yes
appendfsync=everysec
```

### API

- Adjust worker count based on CPU cores
- Set connection pool size based on database connections
- Configure request timeout appropriately

### Workers

- Adjust concurrency per queue based on task complexity
- Set max_tasks_per_child to prevent memory leaks
- Configure time limits appropriate for your tasks

## Backup & Recovery

### PostgreSQL Backup

```bash
# Full backup
kubectl exec postgres-0 -n ai-pal -- \
  pg_dump -U aipal aipal > backup.sql

# Point-in-time recovery
kubectl exec postgres-0 -n ai-pal -- \
  pg_basebackup -D /backup/base -R -P -v
```

### Redis Backup

```bash
# Create snapshot
kubectl exec redis-0 -n ai-pal -- \
  redis-cli -a password BGSAVE

# Copy from container
kubectl cp ai-pal/redis-0:/data/dump.rdb ./dump.rdb
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
