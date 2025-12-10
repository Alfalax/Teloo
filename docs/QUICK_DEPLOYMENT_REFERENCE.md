# Quick Deployment Reference

Quick reference for deploying TeLOO V3 to production.

## Prerequisites Checklist

- [ ] Container images built and pushed to registry
- [ ] Environment variables configured (.env.production)
- [ ] Secrets generated (./scripts/generate-secrets.sh)
- [ ] SSL certificates ready (or Let's Encrypt configured)
- [ ] DNS records pointing to load balancer
- [ ] Cluster access configured (kubectl or docker)

## Kubernetes Deployment

### One-Command Deploy

```bash
export REGISTRY="ghcr.io/your-org"
export IMAGE_VERSION="v1.0.0"
./scripts/deploy-kubernetes.sh
```

### Manual Steps

```bash
# 1. Create namespace
kubectl apply -f kubernetes/namespace.yaml

# 2. Create secrets
kubectl apply -f kubernetes/secrets.yaml

# 3. Create configmap
kubectl apply -f kubernetes/configmap.yaml

# 4. Deploy databases
kubectl apply -f kubernetes/statefulsets.yaml

# 5. Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n teloo-production --timeout=300s

# 6. Deploy services
kubectl apply -f kubernetes/core-api-deployment.yaml
kubectl apply -f kubernetes/agent-ia-deployment.yaml
kubectl apply -f kubernetes/analytics-deployment.yaml
kubectl apply -f kubernetes/realtime-gateway-deployment.yaml
kubectl apply -f kubernetes/files-deployment.yaml
kubectl apply -f kubernetes/frontends-deployment.yaml

# 7. Deploy ingress
kubectl apply -f kubernetes/ingress.yaml

# 8. Setup backups
kubectl apply -f kubernetes/backup-cronjob.yaml
```

### Verify Deployment

```bash
kubectl get pods -n teloo-production
kubectl get svc -n teloo-production
kubectl get ingress -n teloo-production
kubectl logs -f deployment/core-api -n teloo-production
```

## Docker Swarm Deployment

### One-Command Deploy

```bash
export REGISTRY="ghcr.io/your-org"
export IMAGE_VERSION="v1.0.0"
./scripts/deploy-swarm.sh
```

### Manual Steps

```bash
# 1. Initialize Swarm (if needed)
docker swarm init

# 2. Create secrets
echo "password" | docker secret create postgres_password -
echo "password" | docker secret create redis_password -
# ... (see deploy-swarm.sh for complete list)

# 3. Create networks
docker network create --driver overlay teloo-backend
docker network create --driver overlay teloo-frontend

# 4. Deploy stack
docker stack deploy -c docker-swarm-stack.yml teloo
```

### Verify Deployment

```bash
docker service ls
docker stack ps teloo
docker service logs -f teloo_core-api
```

## Common Operations

### Scale Services

**Kubernetes:**
```bash
kubectl scale deployment/core-api --replicas=5 -n teloo-production
```

**Swarm:**
```bash
docker service scale teloo_core-api=5
```

### Update Service

**Kubernetes:**
```bash
kubectl set image deployment/core-api \
  core-api=ghcr.io/your-org/core-api:v1.1.0 \
  -n teloo-production
```

**Swarm:**
```bash
docker service update \
  --image ghcr.io/your-org/core-api:v1.1.0 \
  teloo_core-api
```

### Rollback

**Kubernetes:**
```bash
./scripts/rollback-deployment.sh core-api
# or
kubectl rollout undo deployment/core-api -n teloo-production
```

**Swarm:**
```bash
ORCHESTRATOR=swarm ./scripts/rollback-deployment.sh core-api
# or
docker service rollback teloo_core-api
```

### View Logs

**Kubernetes:**
```bash
kubectl logs -f deployment/core-api -n teloo-production
kubectl logs -f -l app=core-api -n teloo-production  # All pods
```

**Swarm:**
```bash
docker service logs -f teloo_core-api
```

### Backup Database

**Kubernetes:**
```bash
kubectl exec -it postgres-0 -n teloo-production -- \
  pg_dump -U teloo_user teloo_v3_production | gzip > backup.sql.gz
```

**Swarm:**
```bash
docker exec $(docker ps -q -f name=teloo_postgres) \
  pg_dump -U teloo_user teloo_v3_production | gzip > backup.sql.gz
```

### Restore Database

**Kubernetes:**
```bash
gunzip < backup.sql.gz | kubectl exec -i postgres-0 -n teloo-production -- \
  psql -U teloo_user -d teloo_v3_production
```

**Swarm:**
```bash
gunzip < backup.sql.gz | docker exec -i $(docker ps -q -f name=teloo_postgres) \
  psql -U teloo_user -d teloo_v3_production
```

## Troubleshooting

### Pods/Services Not Starting

```bash
# Kubernetes
kubectl describe pod <pod-name> -n teloo-production
kubectl get events -n teloo-production --sort-by='.lastTimestamp'

# Swarm
docker service ps teloo_core-api --no-trunc
docker service inspect teloo_core-api
```

### Check Resource Usage

```bash
# Kubernetes
kubectl top nodes
kubectl top pods -n teloo-production

# Swarm
docker stats
```

### Database Connection Issues

```bash
# Kubernetes
kubectl exec -it core-api-xxx -n teloo-production -- \
  env | grep DATABASE_URL

# Swarm
docker exec $(docker ps -q -f name=teloo_core-api) \
  env | grep DATABASE_URL
```

### View Service Configuration

```bash
# Kubernetes
kubectl get deployment core-api -n teloo-production -o yaml

# Swarm
docker service inspect teloo_core-api --pretty
```

## Health Check URLs

Once deployed, verify services are healthy:

```bash
# Core API
curl https://api.teloo.com/health

# Agent IA
curl https://agent.teloo.com/health

# Analytics
curl http://analytics:8002/health  # Internal only

# Realtime Gateway
curl https://ws.teloo.com/health

# Files
curl http://files:8004/health  # Internal only

# Admin Frontend
curl https://admin.teloo.com

# Advisor Frontend
curl https://advisor.teloo.com
```

## Environment Variables

Key environment variables to set:

```bash
# Registry and versioning
export REGISTRY="ghcr.io/your-org"
export IMAGE_VERSION="v1.0.0"
export IMAGE_PREFIX="teloo"

# Kubernetes specific
export NAMESPACE="teloo-production"

# Swarm specific
export STACK_NAME="teloo"

# Orchestrator selection
export ORCHESTRATOR="kubernetes"  # or "swarm"
```

## Quick Commands

```bash
# Deploy
./scripts/deploy-kubernetes.sh
./scripts/deploy-swarm.sh

# Rollback
./scripts/rollback-deployment.sh <service-name>
./scripts/rollback-deployment.sh all

# Status
kubectl get all -n teloo-production
docker service ls

# Logs
kubectl logs -f deployment/core-api -n teloo-production
docker service logs -f teloo_core-api

# Scale
kubectl scale deployment/core-api --replicas=5 -n teloo-production
docker service scale teloo_core-api=5

# Update
kubectl set image deployment/core-api core-api=new-image -n teloo-production
docker service update --image new-image teloo_core-api
```

## Support

For detailed information, see:
- [Orchestration Guide](./ORCHESTRATION_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Environment Variables Guide](./ENVIRONMENT_VARIABLES_GUIDE.md)
