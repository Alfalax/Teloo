# TeLOO V3 Environment Variables Guide

This comprehensive guide documents all environment variables used across the TeLOO V3 system, organized by service and environment.

## Table of Contents

1. [Overview](#overview)
2. [Environment Structure](#environment-structure)
3. [Security Best Practices](#security-best-practices)
4. [Quick Start](#quick-start)
5. [Service-Specific Variables](#service-specific-variables)
6. [Secrets Management](#secrets-management)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

## Overview

TeLOO V3 uses a multi-layered environment configuration approach:

- **Shared variables**: Defined in root `.env.{environment}` files
- **Service-specific variables**: Defined in `services/{service}/.env.{environment}` files
- **Docker secrets**: Sensitive values stored in `secrets/` directory (production only)
- **Environment validation**: Automatic validation on service startup

## Environment Structure

```
teloo-v3/
├── .env.development          # Shared development variables
├── .env.staging              # Shared staging variables
├── .env.production           # Shared production variables
├── secrets/                  # Docker secrets (production)
│   ├── postgres_password.txt
│   ├── jwt_secret_key.txt
│   └── ...
└── services/
    ├── core-api/
    │   ├── .env.example
    │   ├── .env.development
    │   ├── .env.staging
    │   └── .env.production
    ├── agent-ia/
    │   └── ...
    └── ...
```

## Security Best Practices

### 🔒 Critical Security Rules

1. **Never commit secrets to version control**
   - All `.env.*` files should be in `.gitignore`
   - Use `.env.example` files as templates only
   - Store production secrets in Docker secrets or secure vault

2. **Use strong secrets in production**
   - Minimum 32 characters for API keys
   - Minimum 64 characters for JWT secrets
   - Use cryptographically secure random generation

3. **Rotate secrets regularly**
   - Database passwords: Every 90 days
   - API keys: Every 180 days
   - JWT secrets: Every 365 days

4. **Principle of least privilege**
   - Each service only has access to secrets it needs
   - Use service-specific API keys for inter-service communication

5. **Environment isolation**
   - Development, staging, and production use completely separate secrets
   - Never use production credentials in development

### 🛡️ Secret Generation

Generate secure secrets using:

```bash
# Linux/Mac
./scripts/generate-secrets.sh production

# Windows
.\scripts\generate-secrets.ps1 -Environment production

# Manual generation (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Quick Start

### Development Setup

1. **Copy example files**:
   ```bash
   cp .env.development .env
   cp services/core-api/.env.example services/core-api/.env
   cp services/agent-ia/.env.example services/agent-ia/.env
   cp services/analytics/.env.example services/analytics/.env
   ```

2. **Update development credentials**:
   - Set test API keys for WhatsApp, LLM providers
   - Use default database/Redis passwords (already set)

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

### Staging/Production Setup

1. **Generate secrets**:
   ```bash
   ./scripts/generate-secrets.sh production
   ```

2. **Configure external services**:
   - Update `secrets/whatsapp_access_token.txt`
   - Update `secrets/openai_api_key.txt`
   - Update other external service credentials

3. **Deploy with secrets**:
   ```bash
   docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
   ```

## Service-Specific Variables

### Core API Service

#### Required Variables

| Variable | Description | Example | Environment |
|----------|-------------|---------|-------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:5432/db` | All |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` | All |
| `JWT_SECRET_KEY` | JWT signing key | `<64-char-random-string>` | All |
| `AGENT_IA_API_KEY` | Agent IA service authentication | `<32-char-random-string>` | All |
| `ANALYTICS_API_KEY` | Analytics service authentication | `<32-char-random-string>` | All |
| `MINIO_ENDPOINT` | MinIO endpoint | `minio:9000` | All |
| `MINIO_ACCESS_KEY` | MinIO access key | `teloo_minio` | All |
| `MINIO_SECRET_KEY` | MinIO secret key | `<48-char-random-string>` | All |

#### Optional Variables

| Variable | Description | Default | Environment |
|----------|-------------|---------|-------------|
| `JWT_ALGORITHM` | JWT signing algorithm | `RS256` | All |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `15` | All |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` | All |
| `LOG_LEVEL` | Logging level | `INFO` | All |
| `TIMEZONE` | System timezone | `America/Bogota` | All |
| `MAX_FILE_SIZE_MB` | Maximum upload size | `5` | All |

### Agent IA Service

#### Required Variables

| Variable | Description | Example | Environment |
|----------|-------------|---------|-------------|
| `CORE_API_URL` | Core API endpoint | `http://core-api:8000` | All |
| `SERVICE_API_KEY` | Service authentication key | `<32-char-random-string>` | All |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` | All |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp API token | `<meta-provided-token>` | Staging/Prod |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | `<meta-provided-id>` | Staging/Prod |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | `<32-char-random-string>` | Staging/Prod |

#### LLM Provider Variables

| Variable | Description | Required | Cost |
|----------|-------------|----------|------|
| `OPENAI_API_KEY` | OpenAI API key | Yes (Prod) | High |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Optional | Premium |
| `GEMINI_API_KEY` | Google Gemini API key | Optional | Medium |
| `DEEPSEEK_API_KEY` | Deepseek API key | Optional | Low |

#### Audio Processing Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_PRIMARY_STRATEGY` | Primary audio processor | `whisper` |
| `AUDIO_FALLBACK_STRATEGY` | Fallback processor | `openai` |
| `AUDIO_FALLBACK_ENABLED` | Enable fallback | `true` |
| `AUDIO_FALLBACK_CONFIDENCE_THRESHOLD` | Minimum confidence | `0.6` |

### Analytics Service

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection (read replica) | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_POOL_SIZE` | Connection pool size | `20` |
| `KPI_CACHE_TTL_SECONDS` | KPI cache duration | `300` |
| `BATCH_JOB_DAILY_HOUR` | Daily job execution hour | `2` |
| `ALERTS_ENABLED` | Enable alerting | `true` |
| `ALERT_ERROR_RATE` | Error rate threshold | `0.05` |
| `ALERT_LATENCY_P95` | Latency threshold (ms) | `300` |

#### Alert Configuration (Production)

| Variable | Description | Required |
|----------|-------------|----------|
| `SMTP_SERVER` | SMTP server | Yes |
| `SMTP_PORT` | SMTP port | Yes |
| `SMTP_USERNAME` | SMTP username | Yes |
| `SMTP_PASSWORD` | SMTP password | Yes |
| `ALERT_EMAIL_TO` | Alert recipients | Yes |
| `SLACK_WEBHOOK_URL` | Slack webhook | Optional |

### Realtime Gateway Service

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `JWT_SECRET_KEY` | JWT verification key | `<64-char-random-string>` |

### Files Service

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO endpoint | `minio:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `teloo_minio` |
| `MINIO_SECRET_KEY` | MinIO secret key | `<48-char-random-string>` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |

### Frontend Services

#### Admin Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Core API URL | `http://localhost:8000` |
| `VITE_REALTIME_URL` | Realtime Gateway URL | `http://localhost:8003` |
| `VITE_ENVIRONMENT` | Environment name | `development` |

#### Advisor Frontend

Same as Admin Frontend.

## Secrets Management

### Docker Secrets (Production)

Docker secrets provide secure secret management for production deployments.

#### Creating Secrets

1. **Generate secrets**:
   ```bash
   ./scripts/generate-secrets.sh production
   ```

2. **Verify secrets**:
   ```bash
   ls -la secrets/
   ```

3. **Update placeholders**:
   Edit files in `secrets/` directory with actual credentials.

#### Using Secrets in Docker Compose

```yaml
services:
  core-api:
    secrets:
      - jwt_secret_key
    environment:
      JWT_SECRET_KEY_FILE: /run/secrets/jwt_secret_key

secrets:
  jwt_secret_key:
    file: ./secrets/jwt_secret_key.txt
```

#### Reading Secrets in Application

```python
import os

def get_secret(secret_name: str) -> str:
    """Read secret from file or environment variable"""
    secret_file = os.getenv(f"{secret_name.upper()}_FILE")
    
    if secret_file and os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    return os.getenv(secret_name.upper(), "")
```

### Kubernetes Secrets

For Kubernetes deployments, use native Kubernetes secrets:

```bash
# Create secret from file
kubectl create secret generic teloo-secrets \
  --from-file=jwt-secret-key=./secrets/jwt_secret_key.txt \
  --from-file=postgres-password=./secrets/postgres_password.txt

# Use in deployment
env:
  - name: JWT_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: teloo-secrets
        key: jwt-secret-key
```

## Validation

### Automatic Validation

All services automatically validate environment variables on startup using `scripts/validate-env.py`.

#### Running Validation Manually

```bash
# Validate Core API
SERVICE_NAME=core-api python scripts/validate-env.py

# Validate Agent IA
SERVICE_NAME=agent-ia python scripts/validate-env.py

# Validate Analytics
SERVICE_NAME=analytics python scripts/validate-env.py
```

#### Validation Checks

- ✅ Required variables are set
- ✅ URLs are properly formatted
- ✅ Production secrets are strong (no weak/default values)
- ✅ Secret length meets minimum requirements
- ⚠️  Optional variables use defaults if not set

### Validation Output

```
==========================================
Environment Validation: Core API (production)
==========================================

[INFO] ✓ DATABASE_URL
  ✓ Valid URL format

[CRITICAL] ✗ JWT_SECRET_KEY
  ⚠️  SECURITY RISK: Weak/default value detected in production!

[WARNING] ⚠ LOG_LEVEL
  Using default value: INFO

==========================================
Summary: 15 variables checked
  Critical Issues: 1
  Warnings: 2
  Valid: 12
==========================================

❌ Environment validation FAILED!
Please fix the critical issues before starting the service.
```

## Troubleshooting

### Common Issues

#### 1. Service fails to start with "Environment validation FAILED"

**Solution**: Check validation output and fix critical issues.

```bash
# Run validation manually
SERVICE_NAME=core-api python scripts/validate-env.py

# Fix issues in .env file or secrets/
```

#### 2. "Connection refused" errors

**Cause**: Service URLs are incorrect or services not started.

**Solution**:
- Verify `DATABASE_URL`, `REDIS_URL` point to correct hosts
- Ensure dependent services are running: `docker-compose ps`
- Check network connectivity: `docker network inspect teloo-network`

#### 3. "Authentication failed" errors

**Cause**: API keys or passwords are incorrect.

**Solution**:
- Verify `AGENT_IA_API_KEY` matches between Core API and Agent IA
- Check database password in `DATABASE_URL`
- Regenerate secrets if needed: `./scripts/generate-secrets.sh`

#### 4. "Secret file not found" in production

**Cause**: Docker secrets not properly mounted.

**Solution**:
```bash
# Verify secrets exist
ls -la secrets/

# Check Docker Compose configuration
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml config

# Restart with secrets
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
```

#### 5. LLM API errors (401 Unauthorized)

**Cause**: Invalid or expired API keys.

**Solution**:
- Verify API keys are correct in `secrets/` or `.env`
- Check API key validity with provider
- Ensure no extra whitespace in secret files

### Debug Mode

Enable debug logging to troubleshoot environment issues:

```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart service
docker-compose restart core-api
```

### Checking Loaded Variables

```bash
# View environment variables in running container
docker exec teloo-core-api env | grep -E "DATABASE|REDIS|JWT"

# Check if secret files are mounted
docker exec teloo-core-api ls -la /run/secrets/
```

## Environment Migration

### Development → Staging

1. Copy `.env.development` to `.env.staging`
2. Update all credentials to staging values
3. Change `ENVIRONMENT=staging`
4. Update URLs to staging endpoints
5. Test thoroughly before production

### Staging → Production

1. Generate new production secrets: `./scripts/generate-secrets.sh production`
2. Copy `.env.staging` to `.env.production`
3. Replace ALL secrets with production values
4. Change `ENVIRONMENT=production`
5. Update URLs to production endpoints
6. Run validation: `SERVICE_NAME=core-api python scripts/validate-env.py`
7. Deploy with secrets: `docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d`

## Backup and Recovery

### Backing Up Secrets

```bash
# Create encrypted backup
tar -czf secrets-backup-$(date +%Y%m%d).tar.gz secrets/
gpg -c secrets-backup-$(date +%Y%m%d).tar.gz
rm secrets-backup-$(date +%Y%m%d).tar.gz

# Store encrypted file securely (off-site)
```

### Restoring Secrets

```bash
# Decrypt backup
gpg -d secrets-backup-20240101.tar.gz.gpg > secrets-backup-20240101.tar.gz

# Extract
tar -xzf secrets-backup-20240101.tar.gz

# Verify
ls -la secrets/
```

## Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

## Support

For environment configuration issues:
1. Check this guide first
2. Run validation script
3. Check service logs: `docker-compose logs <service>`
4. Contact DevOps team with validation output
