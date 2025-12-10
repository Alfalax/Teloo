# TeLOO V3 CI/CD Pipeline Documentation

## Overview

This directory contains GitHub Actions workflows for continuous integration and deployment of the TeLOO V3 marketplace platform.

## Workflows

### 1. CI - Build and Test (`ci.yml`)

**Trigger**: Push to `main` or `develop` branches, Pull Requests

**Jobs**:
1. **Lint and Security Checks**
   - Python: black, isort, flake8, bandit, safety
   - JavaScript: ESLint
   
2. **Build Docker Images**
   - Builds all 7 service images
   - Pushes to GitHub Container Registry
   - Uses layer caching for faster builds
   
3. **Security Scan with Trivy**
   - Scans all images for vulnerabilities
   - Uploads results to GitHub Security
   - Fails on CRITICAL vulnerabilities
   
4. **Test Services**
   - Runs pytest for Python services
   - Uses PostgreSQL and Redis test containers
   - Generates coverage reports
   
5. **Test Frontends**
   - Runs Vitest for React frontends
   - Builds production bundles
   
6. **Integration Tests**
   - Starts full stack with Docker Compose
   - Tests health endpoints
   - Validates service communication

### 2. CD - Deploy to Staging (`cd-staging.yml`)

**Trigger**: Push to `develop` branch, Manual dispatch

**Process**:
1. Pull latest images from registry
2. Create staging environment configuration
3. Deploy to staging server via SSH
4. Run smoke tests
5. Notify team via Slack
6. Rollback on failure

**Requirements**:
- Staging server with Docker installed
- SSH access configured
- Environment secrets configured

### 3. CD - Deploy to Production (`cd-production.yml`)

**Trigger**: Manual dispatch only (requires version tag)

**Deployment Options**:
- **Kubernetes**: Full orchestration with auto-scaling
- **Docker Swarm**: Simpler alternative with service replication

**Process**:
1. Pre-deployment checks (version exists, images available)
2. Security scan of production images
3. Deploy to chosen orchestration platform
4. Run smoke tests
5. Create GitHub release
6. Automatic rollback on failure

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to: `Settings > Secrets and variables > Actions`

#### Required Secrets:

**Staging Environment**:
```
STAGING_DATABASE_URL=postgres://user:pass@host:5432/db
STAGING_REDIS_URL=redis://host:6379
STAGING_MINIO_ENDPOINT=minio:9000
STAGING_MINIO_ACCESS_KEY=access_key
STAGING_MINIO_SECRET_KEY=secret_key
STAGING_JWT_SECRET_KEY=your-secret-key
STAGING_AGENT_IA_API_KEY=api-key
STAGING_ANALYTICS_API_KEY=api-key
STAGING_API_URL=https://api-staging.teloo.com
STAGING_REALTIME_URL=https://ws-staging.teloo.com
STAGING_SSH_PRIVATE_KEY=<private-key>
STAGING_USER=deploy
STAGING_HOST=staging.teloo.com
```

**Production Environment**:
```
PROD_DATABASE_URL=postgres://user:pass@host:5432/db
PROD_REDIS_URL=redis://host:6379
PROD_MINIO_ENDPOINT=minio:9000
PROD_MINIO_ACCESS_KEY=access_key
PROD_MINIO_SECRET_KEY=secret_key
PROD_JWT_SECRET_KEY=your-secret-key
PROD_AGENT_IA_API_KEY=api-key
PROD_ANALYTICS_API_KEY=api-key
PROD_API_URL=https://api.teloo.com
PROD_REALTIME_URL=https://ws.teloo.com
PROD_SSH_PRIVATE_KEY=<private-key>
PROD_USER=deploy
PROD_HOST=teloo.com
KUBE_CONFIG=<base64-encoded-kubeconfig>
```

**Notifications**:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

**Optional (for LLM services)**:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

### 2. Configure Docker Registry

The workflows use GitHub Container Registry (ghcr.io) by default.

**Alternative: Docker Hub**

Update workflows to use Docker Hub:
```yaml
env:
  REGISTRY: docker.io
  IMAGE_PREFIX: your-dockerhub-username
```

Add Docker Hub credentials:
```
DOCKERHUB_USERNAME=your-username
DOCKERHUB_TOKEN=your-token
```

### 3. Setup Staging Server

**Requirements**:
- Ubuntu 20.04+ or similar Linux distribution
- Docker 20.10+ and Docker Compose 2.0+
- SSH access for deployment user
- Minimum 4GB RAM, 2 CPU cores

**Setup Steps**:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Create deployment directory
sudo mkdir -p /opt/teloo
sudo chown $USER:$USER /opt/teloo

# 4. Configure SSH key
mkdir -p ~/.ssh
echo "<public-key>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 4. Setup Production (Kubernetes)

**Requirements**:
- Kubernetes cluster (1.24+)
- kubectl configured
- Ingress controller (nginx)
- cert-manager for SSL certificates

**Setup Steps**:

```bash
# 1. Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# 2. Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 3. Create cluster issuer for Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@teloo.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# 4. Create image pull secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<github-token> \
  --namespace=teloo-production
```

### 5. Setup Production (Docker Swarm)

**Requirements**:
- Docker Swarm initialized
- Manager node accessible via SSH
- Minimum 3 nodes for high availability

**Setup Steps**:

```bash
# 1. Initialize swarm (on manager node)
docker swarm init --advertise-addr <manager-ip>

# 2. Join worker nodes
# Run on each worker node:
docker swarm join --token <token> <manager-ip>:2377

# 3. Create overlay network
docker network create --driver overlay --attachable teloo-production-network

# 4. Create deployment directory
mkdir -p /opt/teloo
```

## Usage

### Automatic Deployments

**Staging**: Automatically deploys when code is pushed to `develop` branch

**Production**: Manual deployment only

### Manual Production Deployment

1. Create and push a version tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. Go to GitHub Actions
3. Select "CD - Deploy to Production"
4. Click "Run workflow"
5. Enter version tag (e.g., `v1.0.0`)
6. Select deployment type (kubernetes or docker-swarm)
7. Click "Run workflow"

### Rollback

**Automatic**: Workflows automatically rollback on failure

**Manual Kubernetes Rollback**:
```bash
kubectl rollout undo deployment/core-api --namespace teloo-production
```

**Manual Docker Swarm Rollback**:
```bash
docker service rollback teloo_core-api
```

## Security Scanning

### Trivy Vulnerability Scanning

All images are scanned for vulnerabilities before deployment:
- **CI**: Scans on every build
- **Production**: Blocks deployment on CRITICAL vulnerabilities

View results in: `Security > Code scanning alerts`

### Dependency Scanning

Python dependencies are checked with `safety`:
```bash
safety check --json
```

JavaScript dependencies are checked with `npm audit`:
```bash
npm audit --audit-level=high
```

## Monitoring Deployments

### GitHub Actions

View workflow runs: `Actions` tab

### Kubernetes

```bash
# Watch deployment progress
kubectl rollout status deployment/core-api -n teloo-production

# View pods
kubectl get pods -n teloo-production

# View logs
kubectl logs -f deployment/core-api -n teloo-production

# View events
kubectl get events -n teloo-production --sort-by='.lastTimestamp'
```

### Docker Swarm

```bash
# View services
docker stack services teloo

# View service logs
docker service logs -f teloo_core-api

# View service tasks
docker stack ps teloo
```

## Troubleshooting

### Build Failures

**Issue**: Docker build fails with "no space left on device"
```bash
# Clean up Docker
docker system prune -af --volumes
```

**Issue**: Tests fail in CI but pass locally
- Check environment variables
- Verify test database is clean
- Check for timing issues in async tests

### Deployment Failures

**Issue**: Pods stuck in "ImagePullBackOff"
```bash
# Check image pull secret
kubectl get secret ghcr-secret -n teloo-production

# Recreate secret if needed
kubectl delete secret ghcr-secret -n teloo-production
kubectl create secret docker-registry ghcr-secret ...
```

**Issue**: Service not responding after deployment
```bash
# Check pod logs
kubectl logs -f deployment/core-api -n teloo-production

# Check pod events
kubectl describe pod <pod-name> -n teloo-production

# Check service endpoints
kubectl get endpoints -n teloo-production
```

### Rollback Issues

**Issue**: Rollback doesn't restore previous version
- Verify previous revision exists
- Check deployment history
- Manual rollback to specific revision:
```bash
kubectl rollout history deployment/core-api -n teloo-production
kubectl rollout undo deployment/core-api --to-revision=<number> -n teloo-production
```

## Best Practices

1. **Always test in staging first**
2. **Use semantic versioning** (v1.0.0, v1.1.0, v2.0.0)
3. **Tag releases** before production deployment
4. **Monitor deployments** for at least 30 minutes after
5. **Keep secrets secure** - never commit to repository
6. **Review security scan results** before deploying
7. **Document changes** in release notes
8. **Backup databases** before major updates
9. **Test rollback procedures** regularly
10. **Keep dependencies updated** to patch vulnerabilities

## Performance Optimization

### Build Speed

- Layer caching is enabled for all Docker builds
- Dependencies are cached between workflow runs
- Multi-stage builds minimize image size

### Deployment Speed

- Rolling updates with zero downtime
- Parallel deployment of independent services
- Health checks ensure services are ready before routing traffic

## Cost Optimization

### GitHub Actions

- Workflows use caching to reduce build time
- Tests run in parallel when possible
- Conditional jobs skip unnecessary work

### Container Registry

- Old images are automatically pruned
- Only necessary layers are pushed
- Compression is enabled

## Support

For issues or questions:
1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Check service logs in Kubernetes/Swarm
4. Contact DevOps team

## Changelog

- **2024-01**: Initial CI/CD pipeline setup
- Multi-stage Docker builds for all services
- Kubernetes and Docker Swarm support
- Automated security scanning with Trivy
- Staging and production deployment workflows
