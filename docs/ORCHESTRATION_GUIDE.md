# TeLOO V3 Orchestration Guide

This guide covers deploying and managing TeLOO V3 in production using Kubernetes or Docker Swarm.

## Table of Contents

1. [Overview](#overview)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Docker Swarm Deployment](#docker-swarm-deployment)
4. [Load Balancing](#load-balancing)
5. [Auto-Scaling](#auto-scaling)
6. [Backup and Restore](#backup-and-restore)
7. [Rolling Updates](#rolling-updates)
8. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## Overview

TeLOO V3 supports two orchestration platforms:

- **Kubernetes**: Full-featured orchestration for large-scale deployments
- **Docker Swarm**: Simpler alternative for smaller deployments

### Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│              (Ingress / Traefik)                        │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Frontend   │  │   Backend   │  │   Support   │
│   Services   │  │   Services  │  │   Services  │
├──────────────┤  ├─────────────┤  ├─────────────┤
│ Admin (x2)   │  │ Core-API(x3)│  │ Analytics   │
│ Advisor (x2) │  │ Agent-IA(x2)│  │ Realtime    │
└──────────────┘  │ Files (x2)  │  │ Files       │
                  └─────────────┘  └─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│  PostgreSQL  │  │    Redis    │  │    MinIO    │
│   (StatefulSet)│  │(StatefulSet)│  │(StatefulSet)│
└──────────────┘  └─────────────┘  └─────────────┘
```

### Service Replicas

| Service | Min Replicas | Max Replicas | Resources |
|---------|--------------|--------------|-----------|
| core-api | 3 | 10 | 512Mi-1Gi RAM, 0.5-1 CPU |
| agent-ia | 2 | 6 | 512Mi-1Gi RAM, 0.5-1 CPU |
| analytics | 2 | 5 | 256Mi-512Mi RAM, 0.25-0.5 CPU |
| realtime-gateway | 2 | 6 | 256Mi-512Mi RAM, 0.25-0.5 CPU |
| files | 2 | 5 | 256Mi-512Mi RAM, 0.25-0.5 CPU |
| admin-frontend | 2 | 4 | 128Mi-256Mi RAM, 0.1-0.25 CPU |
| advisor-frontend | 2 | 4 | 128Mi-256Mi RAM, 0.1-0.25 CPU |

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Container registry access (GitHub Container Registry, Docker Hub, etc.)
- SSL certificates (Let's Encrypt recommended)

### Step 1: Prepare Secrets

Generate secrets using the provided script:

```bash
./scripts/generate-secrets.sh kubernetes
```

Or manually create secrets:

```bash
kubectl create secret generic teloo-secrets \
  --from-literal=postgres-user=teloo_user \
  --from-literal=postgres-password=<strong-password> \
  --from-literal=redis-password=<strong-password> \
  --from-literal=jwt-secret=<jwt-secret> \
  --namespace=teloo-production
```

### Step 2: Update Configuration

Edit `kubernetes/configmap.yaml` with your environment-specific values:

```yaml
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "WARNING"
  # Update service URLs if needed
```

### Step 3: Deploy to Kubernetes

Run the deployment script:

```bash
export REGISTRY="ghcr.io/your-org"
export IMAGE_VERSION="v1.0.0"
./scripts/deploy-kubernetes.sh
```

Or deploy manually:

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create secrets and configmap
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/configmap.yaml

# Deploy stateful services
kubectl apply -f kubernetes/statefulsets.yaml

# Deploy application services
kubectl apply -f kubernetes/core-api-deployment.yaml
kubectl apply -f kubernetes/agent-ia-deployment.yaml
kubectl apply -f kubernetes/analytics-deployment.yaml
kubectl apply -f kubernetes/realtime-gateway-deployment.yaml
kubectl apply -f kubernetes/files-deployment.yaml
kubectl apply -f kubernetes/frontends-deployment.yaml

# Deploy ingress
kubectl apply -f kubernetes/ingress.yaml

# Setup backups
kubectl apply -f kubernetes/backup-cronjob.yaml
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n teloo-production

# Check services
kubectl get services -n teloo-production

# Check ingress
kubectl get ingress -n teloo-production

# View logs
kubectl logs -f deployment/core-api -n teloo-production
```

## Docker Swarm Deployment

### Prerequisites

- Docker Engine (v20.10+)
- Docker Swarm initialized
- Container registry access
- SSL certificates

### Step 1: Initialize Swarm

```bash
# On manager node
docker swarm init

# On worker nodes (use token from init output)
docker swarm join --token <token> <manager-ip>:2377
```

### Step 2: Prepare Secrets

Create Docker secrets from environment file:

```bash
# Ensure .env.production exists with all required secrets
./scripts/deploy-swarm.sh
```

Or manually:

```bash
echo "strong-password" | docker secret create postgres_password -
echo "strong-password" | docker secret create redis_password -
echo "jwt-secret-key" | docker secret create jwt_secret -
```

### Step 3: Deploy Stack

```bash
export REGISTRY="ghcr.io/your-org"
export IMAGE_VERSION="v1.0.0"
export IMAGE_PREFIX="teloo"
export STACK_NAME="teloo"

docker stack deploy -c docker-swarm-stack.yml teloo
```

### Step 4: Verify Deployment

```bash
# Check services
docker service ls

# Check service logs
docker service logs -f teloo_core-api

# Check service status
docker service ps teloo_core-api

# View stack
docker stack ps teloo
```

## Load Balancing

### Kubernetes (Ingress)

The Kubernetes deployment uses an Ingress controller for load balancing:

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: teloo-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: api.teloo.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: core-api
            port:
              number: 8000
```

### Docker Swarm (Traefik)

The Swarm deployment uses Traefik for load balancing:

```yaml
# Traefik labels in docker-swarm-stack.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.core-api.rule=Host(`api.teloo.com`)"
  - "traefik.http.services.core-api.loadbalancer.server.port=8000"
  - "traefik.http.services.core-api.loadbalancer.healthcheck.path=/health"
```

## Auto-Scaling

### Kubernetes HPA (Horizontal Pod Autoscaler)

Auto-scaling is configured for all services:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: core-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: core-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Scaling Triggers:**
- CPU utilization > 70%
- Memory utilization > 80%

**Manual Scaling:**

```bash
# Scale up
kubectl scale deployment/core-api --replicas=5 -n teloo-production

# Scale down
kubectl scale deployment/core-api --replicas=2 -n teloo-production
```

### Docker Swarm Scaling

Swarm doesn't have built-in auto-scaling, but you can manually scale:

```bash
# Scale up
docker service scale teloo_core-api=5

# Scale down
docker service scale teloo_core-api=2

# Scale multiple services
docker service scale teloo_core-api=5 teloo_agent-ia=3
```

## Backup and Restore

### Automated Backups

Backups run automatically via CronJobs (Kubernetes) or scheduled tasks:

**PostgreSQL Backup:**
- Schedule: Daily at 2 AM
- Retention: 30 days
- Location: `/backups/postgres-backup-YYYYMMDD-HHMMSS.sql.gz`

**Redis Backup:**
- Schedule: Every 6 hours
- Retention: 7 days
- Location: `/backups/redis-backup-YYYYMMDD-HHMMSS.rdb`

**MinIO Backup:**
- Schedule: Daily at 3 AM
- Retention: 14 days
- Location: `/backups/minio-backup-YYYYMMDD-HHMMSS/`

### Manual Backup

**Kubernetes:**

```bash
# PostgreSQL
kubectl exec -it postgres-0 -n teloo-production -- \
  pg_dump -U teloo_user teloo_v3_production | gzip > backup.sql.gz

# Redis
kubectl exec -it redis-0 -n teloo-production -- \
  redis-cli --rdb /tmp/dump.rdb
kubectl cp teloo-production/redis-0:/tmp/dump.rdb ./redis-backup.rdb

# MinIO
kubectl port-forward svc/minio 9000:9000 -n teloo-production
mc mirror local-minio/teloo-files ./minio-backup/
```

**Docker Swarm:**

```bash
# PostgreSQL
docker exec $(docker ps -q -f name=teloo_postgres) \
  pg_dump -U teloo_user teloo_v3_production | gzip > backup.sql.gz

# Redis
docker exec $(docker ps -q -f name=teloo_redis) \
  redis-cli --rdb /data/dump.rdb
docker cp $(docker ps -q -f name=teloo_redis):/data/dump.rdb ./redis-backup.rdb
```

### Restore from Backup

**PostgreSQL:**

```bash
# Kubernetes
gunzip < backup.sql.gz | kubectl exec -i postgres-0 -n teloo-production -- \
  psql -U teloo_user -d teloo_v3_production

# Swarm
gunzip < backup.sql.gz | docker exec -i $(docker ps -q -f name=teloo_postgres) \
  psql -U teloo_user -d teloo_v3_production
```

**Redis:**

```bash
# Stop Redis, copy backup, restart
kubectl exec -it redis-0 -n teloo-production -- redis-cli SHUTDOWN
kubectl cp ./redis-backup.rdb teloo-production/redis-0:/data/dump.rdb
kubectl delete pod redis-0 -n teloo-production
```

## Rolling Updates

### Kubernetes Rolling Updates

Rolling updates are configured with zero downtime:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Create 1 extra pod during update
    maxUnavailable: 0  # Keep all pods running during update
```

**Update a service:**

```bash
# Update image
kubectl set image deployment/core-api \
  core-api=ghcr.io/your-org/core-api:v1.1.0 \
  -n teloo-production

# Watch rollout
kubectl rollout status deployment/core-api -n teloo-production

# Rollback if needed
kubectl rollout undo deployment/core-api -n teloo-production
```

### Docker Swarm Rolling Updates

```bash
# Update service
docker service update \
  --image ghcr.io/your-org/core-api:v1.1.0 \
  --update-parallelism 1 \
  --update-delay 10s \
  teloo_core-api

# Rollback if needed
docker service rollback teloo_core-api
```

### Rollback Script

Use the provided rollback script:

```bash
# Rollback specific service
./scripts/rollback-deployment.sh core-api

# Rollback all services
./scripts/rollback-deployment.sh all
```

## Monitoring and Troubleshooting

### Health Checks

All services expose health check endpoints:

- `/health` - Overall health
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe

### View Logs

**Kubernetes:**

```bash
# View logs
kubectl logs -f deployment/core-api -n teloo-production

# View logs from all pods
kubectl logs -f -l app=core-api -n teloo-production

# View previous logs (after crash)
kubectl logs --previous deployment/core-api -n teloo-production
```

**Docker Swarm:**

```bash
# View service logs
docker service logs -f teloo_core-api

# View logs from specific task
docker service ps teloo_core-api
docker logs <task-id>
```

### Common Issues

**Pods/Services not starting:**

```bash
# Check events
kubectl get events -n teloo-production --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n teloo-production

# Check resource usage
kubectl top pods -n teloo-production
```

**Database connection issues:**

```bash
# Test database connectivity
kubectl exec -it core-api-xxx -n teloo-production -- \
  psql $DATABASE_URL -c "SELECT 1"

# Check database logs
kubectl logs -f postgres-0 -n teloo-production
```

**Performance issues:**

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n teloo-production

# Check HPA status
kubectl get hpa -n teloo-production
kubectl describe hpa core-api-hpa -n teloo-production
```

### Metrics and Monitoring

Access Prometheus metrics:

```bash
# Port forward to Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Access at http://localhost:9090
```

Access Grafana dashboards:

```bash
# Port forward to Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Access at http://localhost:3000
```

## Best Practices

1. **Always use secrets for sensitive data** - Never hardcode passwords or API keys
2. **Set resource limits** - Prevent services from consuming all cluster resources
3. **Use health checks** - Enable automatic recovery from failures
4. **Monitor continuously** - Set up alerts for critical metrics
5. **Test rollbacks** - Regularly practice rollback procedures
6. **Backup regularly** - Automate backups and test restore procedures
7. **Use namespaces** - Isolate environments (dev, staging, production)
8. **Version images** - Always tag images with specific versions, avoid `:latest`
9. **Document changes** - Keep deployment documentation up to date
10. **Security scanning** - Scan images for vulnerabilities before deployment

## Support

For issues or questions:
- Check logs first
- Review health check endpoints
- Consult the troubleshooting section
- Contact the DevOps team

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [TeLOO Deployment Guide](./DEPLOYMENT_GUIDE.md)
