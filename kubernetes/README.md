# AI-PAL Kubernetes Deployment

This directory contains Kubernetes manifests for deploying AI-PAL in a production Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured to access your cluster
- Ingress controller (e.g., nginx-ingress) installed
- cert-manager for TLS certificates (optional)
- Metrics server for HPA (optional)
- StorageClass configured for persistent volumes

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Configure Secrets

**IMPORTANT:** Never commit secrets to version control!

```bash
# Create secrets from command line
kubectl create secret generic ai-pal-secrets \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=ENCRYPTION_KEY=$(openssl rand -base64 32) \
  -n ai-pal

# Or edit secrets.yaml template and apply
# kubectl apply -f secrets.yaml
```

### 3. Deploy Infrastructure

```bash
# Create persistent volumes
kubectl apply -f pvc.yaml

# Deploy PostgreSQL
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Deploy Redis
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n ai-pal --timeout=300s
```

### 4. Deploy Application

```bash
# Apply configuration
kubectl apply -f configmap.yaml

# Deploy application
kubectl apply -f app-deployment.yaml
kubectl apply -f app-service.yaml

# Wait for application to be ready
kubectl wait --for=condition=ready pod -l app=ai-pal -n ai-pal --timeout=300s
```

### 5. Configure Ingress

```bash
# Edit ingress.yaml to set your domain
# Then apply:
kubectl apply -f ingress.yaml
```

### 6. Enable Autoscaling (Optional)

```bash
# Requires metrics-server
kubectl apply -f hpa.yaml
```

## Deployment Order

For a fresh deployment, apply manifests in this order:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml  # After filling in values
kubectl apply -f pvc.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml
kubectl apply -f app-deployment.yaml
kubectl apply -f app-service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
```

Or use a single command:

```bash
# After configuring secrets
kubectl apply -f kubernetes/
```

## Verification

### Check All Resources

```bash
kubectl get all -n ai-pal
```

### Check Pod Status

```bash
kubectl get pods -n ai-pal
kubectl describe pod <pod-name> -n ai-pal
```

### View Logs

```bash
# Application logs
kubectl logs -f deployment/ai-pal-app -n ai-pal

# PostgreSQL logs
kubectl logs -f statefulset/postgres -n ai-pal

# Redis logs
kubectl logs -f deployment/redis -n ai-pal
```

### Test Application

```bash
# Port forward to test locally
kubectl port-forward svc/ai-pal-service 8000:80 -n ai-pal

# Then access http://localhost:8000/health
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

Edit `configmap.yaml` to configure:
- Feature flags (ARI, EDM, FFE, Gates)
- Module enablement
- Four Gates thresholds
- Learning settings
- Dream module schedule

### Secrets

Manage secrets using `secrets.yaml` or kubectl:

```bash
# Update a secret
kubectl create secret generic ai-pal-secrets \
  --from-literal=OPENAI_API_KEY=new-key \
  --dry-run=client -o yaml | kubectl apply -f -

# View secret (base64 encoded)
kubectl get secret ai-pal-secrets -n ai-pal -o yaml
```

### Resource Limits

Adjust resource requests/limits in:
- `app-deployment.yaml` - Application pods
- `postgres-statefulset.yaml` - Database
- `redis-deployment.yaml` - Cache

### Scaling

#### Manual Scaling

```bash
# Scale application
kubectl scale deployment ai-pal-app --replicas=5 -n ai-pal

# PostgreSQL is StatefulSet - scaling requires data replication setup
```

#### Auto Scaling

Edit `hpa.yaml` to configure:
- Min/max replicas
- CPU/memory thresholds
- Scale up/down policies

## Storage

### Storage Classes

Specify storage class in PVC manifests:

```yaml
storageClassName: fast-ssd  # Your storage class
```

### Volume Types

- **ai-pal-data-pvc**: Application data (20Gi, ReadWriteMany)
- **ai-pal-logs-pvc**: Application logs (10Gi, ReadWriteMany)
- **ai-pal-models-pvc**: Local AI models (50Gi, ReadWriteMany)
- **postgres-storage**: Database (10Gi, from StatefulSet template)
- **redis-pvc**: Redis persistence (5Gi, ReadWriteOnce)

### Backup Volumes

```bash
# Backup PostgreSQL
kubectl exec -n ai-pal postgres-0 -- pg_dump -U aipal aipal > backup.sql

# Backup persistent volumes
kubectl cp ai-pal/ai-pal-app-xxx:/app/data ./backup/data
```

## Networking

### Services

- **ai-pal-service**: Main application (ClusterIP, port 80)
- **postgres-service**: PostgreSQL (Headless, port 5432)
- **redis-service**: Redis cache (ClusterIP, port 6379)

### Ingress

Configure in `ingress.yaml`:
- Domain name
- TLS certificates
- Rate limiting
- CORS settings
- Security headers

### TLS Certificates

#### Using cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

#### Manual Certificates

```bash
# Create TLS secret
kubectl create secret tls ai-pal-tls-cert \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n ai-pal
```

## Monitoring

### Health Checks

Application includes:
- Liveness probe: `/health` endpoint
- Readiness probe: `/health` endpoint

### Metrics

Prometheus metrics available at `/metrics` endpoint.

#### Deploy Prometheus (Optional)

```bash
# Using Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### Logs

View logs from all pods:

```bash
# Application
kubectl logs -f -l app=ai-pal -n ai-pal --tail=100

# With stern (multi-pod log viewer)
stern ai-pal -n ai-pal
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-pal

# Common issues:
# - Image pull errors: Check image name/registry
# - Resource limits: Check node capacity
# - Volume mount errors: Check PVC status
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
kubectl get pods -l app=postgres -n ai-pal

# Test connection from app pod
kubectl exec -it deployment/ai-pal-app -n ai-pal -- \
  psql postgresql://aipal:password@postgres-service:5432/aipal
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress ai-pal-ingress -n ai-pal

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Application Errors

```bash
# View application logs
kubectl logs -f deployment/ai-pal-app -n ai-pal

# Check configuration
kubectl get configmap ai-pal-config -n ai-pal -o yaml
kubectl get secret ai-pal-secrets -n ai-pal -o yaml
```

## Maintenance

### Updates

```bash
# Update application image
kubectl set image deployment/ai-pal-app \
  ai-pal=ai-pal:new-version \
  -n ai-pal

# Or edit deployment
kubectl edit deployment ai-pal-app -n ai-pal

# Rollback if needed
kubectl rollout undo deployment/ai-pal-app -n ai-pal
```

### Database Migrations

Migrations run automatically via init container, but can be run manually:

```bash
kubectl exec -it deployment/ai-pal-app -n ai-pal -- \
  python -m alembic upgrade head
```

### Cleanup

```bash
# Delete all resources
kubectl delete namespace ai-pal

# Or delete individually
kubectl delete -f kubernetes/
```

## Production Considerations

### High Availability

1. **Multi-replica deployment**: Already configured (3 replicas)
2. **Pod Disruption Budget**: Add PDB to prevent all pods going down
3. **Node affinity**: Spread pods across availability zones
4. **Database replication**: Configure PostgreSQL streaming replication

### Security

1. **Network Policies**: Restrict pod-to-pod communication
2. **RBAC**: Limit service account permissions
3. **Pod Security Policies**: Enforce security standards
4. **Secrets Management**: Use external secret managers (Vault, AWS Secrets Manager)
5. **Image Scanning**: Scan container images for vulnerabilities

### Performance

1. **Resource tuning**: Adjust based on monitoring data
2. **HPA configuration**: Fine-tune autoscaling thresholds
3. **Database optimization**: Connection pooling, indexes
4. **Caching**: Redis configuration and eviction policies

### Backup & Disaster Recovery

1. **Database backups**: Automated pg_dump or volume snapshots
2. **Volume backups**: Persistent volume snapshots
3. **Configuration backups**: Export ConfigMaps and Secrets
4. **Disaster recovery plan**: Document recovery procedures

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AI-PAL Deployment Guide](../docs/deployment/DEPLOYMENT_GUIDE.md)
- [AI-PAL Architecture](../docs/developer/ARCHITECTURE.md)

## Support

For issues or questions:
- Check troubleshooting section above
- Review application logs
- Consult AI-PAL documentation
