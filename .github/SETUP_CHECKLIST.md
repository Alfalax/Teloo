# CI/CD Setup Checklist

Use this checklist to setup the CI/CD pipeline for TeLOO V3.

## Phase 1: GitHub Configuration

### GitHub Secrets - Staging

- [ ] `STAGING_DATABASE_URL` - PostgreSQL connection string
- [ ] `STAGING_DB_USER` - Database username
- [ ] `STAGING_DB_PASSWORD` - Database password
- [ ] `STAGING_REDIS_URL` - Redis connection string
- [ ] `STAGING_MINIO_ENDPOINT` - MinIO endpoint
- [ ] `STAGING_MINIO_ACCESS_KEY` - MinIO access key
- [ ] `STAGING_MINIO_SECRET_KEY` - MinIO secret key
- [ ] `STAGING_JWT_SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- [ ] `STAGING_AGENT_IA_API_KEY` - Service auth key (generate with `openssl rand -hex 32`)
- [ ] `STAGING_ANALYTICS_API_KEY` - Service auth key (generate with `openssl rand -hex 32`)
- [ ] `STAGING_API_URL` - API URL (e.g., https://api-staging.teloo.com)
- [ ] `STAGING_REALTIME_URL` - WebSocket URL (e.g., https://ws-staging.teloo.com)
- [ ] `STAGING_SSH_PRIVATE_KEY` - SSH private key for deployment
- [ ] `STAGING_USER` - SSH username (e.g., deploy)
- [ ] `STAGING_HOST` - Staging server hostname

### GitHub Secrets - Production

- [ ] `PROD_DATABASE_URL` - PostgreSQL connection string
- [ ] `PROD_DB_USER` - Database username
- [ ] `PROD_DB_PASSWORD` - Database password
- [ ] `PROD_REDIS_URL` - Redis connection string
- [ ] `PROD_MINIO_ENDPOINT` - MinIO endpoint
- [ ] `PROD_MINIO_ACCESS_KEY` - MinIO access key
- [ ] `PROD_MINIO_SECRET_KEY` - MinIO secret key
- [ ] `PROD_JWT_SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- [ ] `PROD_AGENT_IA_API_KEY` - Service auth key
- [ ] `PROD_ANALYTICS_API_KEY` - Service auth key
- [ ] `PROD_API_URL` - API URL (e.g., https://api.teloo.com)
- [ ] `PROD_REALTIME_URL` - WebSocket URL (e.g., https://ws.teloo.com)

### GitHub Secrets - Production (Kubernetes)

- [ ] `KUBE_CONFIG` - Base64 encoded kubeconfig file
  ```bash
  cat ~/.kube/config | base64 | tr -d '\n'
  ```

### GitHub Secrets - Production (Docker Swarm)

- [ ] `PROD_SSH_PRIVATE_KEY` - SSH private key for swarm manager
- [ ] `PROD_USER` - SSH username
- [ ] `PROD_HOST` - Swarm manager hostname

### GitHub Secrets - Notifications

- [ ] `SLACK_WEBHOOK_URL` - Slack webhook for notifications

### GitHub Secrets - Optional (LLM Services)

- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `ANTHROPIC_API_KEY` - Anthropic API key
- [ ] `GEMINI_API_KEY` - Google Gemini API key

### GitHub Settings

- [ ] Enable GitHub Actions in repository settings
- [ ] Enable GitHub Container Registry
- [ ] Configure branch protection rules for `main` and `develop`
- [ ] Require status checks to pass before merging
- [ ] Enable "Require branches to be up to date before merging"

## Phase 2: Staging Server Setup

### Server Requirements

- [ ] Ubuntu 20.04+ or similar Linux distribution
- [ ] Minimum 4GB RAM, 2 CPU cores
- [ ] 50GB+ disk space
- [ ] Public IP address or domain name

### Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

- [ ] Docker installed and running
- [ ] User added to docker group

### Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

- [ ] Docker Compose installed

### Setup Deployment Directory

```bash
sudo mkdir -p /opt/teloo
sudo chown $USER:$USER /opt/teloo
```

- [ ] Deployment directory created

### Configure SSH Access

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Add your public key to authorized_keys
echo "your-public-key" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

- [ ] SSH key configured
- [ ] Can SSH without password: `ssh deploy@staging.teloo.com`

### Configure Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

- [ ] Firewall configured

### DNS Configuration

- [ ] `staging.teloo.com` points to staging server IP
- [ ] `api-staging.teloo.com` points to staging server IP
- [ ] `ws-staging.teloo.com` points to staging server IP

## Phase 3: Production Setup (Choose One)

### Option A: Kubernetes

#### Prerequisites

- [ ] Kubernetes cluster (1.24+) provisioned
- [ ] kubectl installed locally
- [ ] kubectl configured to access cluster

#### Install Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

- [ ] Nginx ingress controller installed
- [ ] Ingress controller has external IP

#### Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

- [ ] cert-manager installed

#### Create ClusterIssuer

```bash
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
```

- [ ] ClusterIssuer created

#### Create Namespace

```bash
kubectl create namespace teloo-production
```

- [ ] Namespace created

#### Create Image Pull Secret

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<github-token> \
  --namespace=teloo-production
```

- [ ] Image pull secret created

#### DNS Configuration

- [ ] `teloo.com` points to ingress external IP
- [ ] `www.teloo.com` points to ingress external IP
- [ ] `api.teloo.com` points to ingress external IP

### Option B: Docker Swarm

#### Initialize Swarm

```bash
# On manager node
docker swarm init --advertise-addr <manager-ip>
```

- [ ] Swarm initialized
- [ ] Join token saved

#### Join Worker Nodes

```bash
# On each worker node
docker swarm join --token <token> <manager-ip>:2377
```

- [ ] Worker nodes joined (minimum 2 recommended)

#### Create Network

```bash
docker network create --driver overlay --attachable teloo-production-network
```

- [ ] Overlay network created

#### Setup Deployment Directory

```bash
mkdir -p /opt/teloo
```

- [ ] Deployment directory created on manager node

#### Configure SSH Access

- [ ] SSH access to swarm manager configured
- [ ] Can SSH without password

#### DNS Configuration

- [ ] `teloo.com` points to swarm manager IP (or load balancer)
- [ ] `api.teloo.com` points to swarm manager IP

## Phase 4: SSL Certificates

### Option A: Let's Encrypt (Automatic with cert-manager)

- [ ] cert-manager configured (Kubernetes only)
- [ ] ClusterIssuer created
- [ ] Ingress configured with TLS

### Option B: Manual Certificates

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout teloo.com.key -out teloo.com.crt

# Or use your CA-signed certificates
```

- [ ] SSL certificate obtained
- [ ] Certificate and key placed in `/opt/teloo/ssl/` or Kubernetes secret

## Phase 5: Database Setup

### PostgreSQL

- [ ] PostgreSQL 15+ installed or provisioned
- [ ] Database `teloo_v3_production` created
- [ ] User created with appropriate permissions
- [ ] Connection string tested
- [ ] Backups configured

### Redis

- [ ] Redis 7+ installed or provisioned
- [ ] Password configured
- [ ] Connection tested
- [ ] Persistence enabled

### MinIO

- [ ] MinIO installed or S3-compatible storage provisioned
- [ ] Bucket created
- [ ] Access keys generated
- [ ] Connection tested

## Phase 6: Monitoring Setup

### Prometheus

- [ ] Prometheus installed
- [ ] Scraping TeLOO services
- [ ] Retention configured

### Grafana

- [ ] Grafana installed
- [ ] Connected to Prometheus
- [ ] Dashboards imported
- [ ] Alerts configured

### Logging

- [ ] Log aggregation setup (ELK, Loki, or similar)
- [ ] Services configured to send logs
- [ ] Log retention configured

## Phase 7: Testing

### Local Testing

```bash
./scripts/test-ci-locally.sh
```

- [ ] Local CI tests pass

### CI Pipeline

- [ ] Push to feature branch
- [ ] CI workflow runs successfully
- [ ] All checks pass

### Staging Deployment

- [ ] Merge to develop
- [ ] Staging deployment succeeds
- [ ] Services are healthy
- [ ] Can access staging site
- [ ] Can login to admin panel
- [ ] Can create test solicitud

### Production Deployment

- [ ] Create version tag
- [ ] Run production deployment workflow
- [ ] Deployment succeeds
- [ ] Services are healthy
- [ ] Can access production site
- [ ] SSL certificate valid
- [ ] All critical flows work

### Rollback Test

- [ ] Test rollback procedure
- [ ] Verify services restore to previous version
- [ ] Verify data integrity maintained

## Phase 8: Documentation

- [ ] Update team wiki with deployment procedures
- [ ] Document emergency contacts
- [ ] Create runbook for common issues
- [ ] Train team on deployment process
- [ ] Document rollback procedures

## Phase 9: Security

### Security Scanning

- [ ] Trivy scanning enabled in CI
- [ ] Security alerts configured
- [ ] Vulnerability management process defined

### Access Control

- [ ] GitHub repository access reviewed
- [ ] Production server access limited
- [ ] Kubernetes RBAC configured (if using K8s)
- [ ] Secrets rotation schedule defined

### Compliance

- [ ] Security audit completed
- [ ] Compliance requirements met
- [ ] Data protection measures in place

## Phase 10: Go Live

### Pre-Launch

- [ ] All checklist items completed
- [ ] Team trained
- [ ] Monitoring configured
- [ ] Alerts tested
- [ ] Backup verified
- [ ] Rollback tested
- [ ] Load testing completed
- [ ] Security review passed

### Launch

- [ ] Deploy to production
- [ ] Monitor for 1 hour
- [ ] Verify all services healthy
- [ ] Test critical user flows
- [ ] Announce to team

### Post-Launch

- [ ] Monitor for 24 hours
- [ ] Review metrics
- [ ] Address any issues
- [ ] Document lessons learned
- [ ] Celebrate! 🎉

## Maintenance

### Regular Tasks

- [ ] Weekly: Review security scan results
- [ ] Weekly: Check resource usage
- [ ] Monthly: Update dependencies
- [ ] Monthly: Review and rotate secrets
- [ ] Quarterly: Disaster recovery drill
- [ ] Quarterly: Review and update documentation

## Notes

Use this space to track progress and notes:

```
Date: ___________
Completed by: ___________
Notes:




```

## Support

If you need help with any step:
- Check `DEPLOYMENT_GUIDE.md` for detailed instructions
- Check `.github/workflows/README.md` for workflow details
- Contact DevOps team: devops@teloo.com
- Slack: #teloo-devops
