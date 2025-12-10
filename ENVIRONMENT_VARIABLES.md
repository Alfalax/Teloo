# TeLOO V3 Environment Variables Documentation

This document provides comprehensive documentation for all environment variables used across the TeLOO V3 system.

## 📚 Documentation Structure

This is the main index for environment configuration. For detailed information, see:

- **[Environment Variables Guide](./docs/ENVIRONMENT_VARIABLES_GUIDE.md)** - Complete guide with all variables
- **[Quick Reference](./docs/ENV_QUICK_REFERENCE.md)** - Quick reference card
- **[Deployment Checklist](./docs/DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[Secrets Management](./secrets/README.md)** - Secrets directory documentation

## Table of Contents

1. [Overview](#overview)
2. [Environment Files Structure](#environment-files-structure)
3. [Quick Start](#quick-start)
4. [Core API Variables](#core-api-variables)
5. [Agent IA Variables](#agent-ia-variables)
6. [Analytics Service Variables](#analytics-service-variables)
7. [Realtime Gateway Variables](#realtime-gateway-variables)
8. [Files Service Variables](#files-service-variables)
9. [Frontend Variables](#frontend-variables)
10. [Secrets Management](#secrets-management)
11. [Validation](#validation)

## Overview

TeLOO V3 uses a comprehensive environment configuration system with:

- **Shared environment files** (`.env.{environment}`) for common variables
- **Service-specific files** (`services/{service}/.env.{environment}`) for service configs
- **Docker secrets** (`secrets/`) for sensitive production values
- **Automatic validation** on service startup

## Environment Files Structure

```
teloo-v3/
├── .env.development          # Shared development variables
├── .env.staging              # Shared staging variables
├── .env.production           # Shared production variables
├── secrets/                  # Docker secrets (production)
│   ├── README.md
│   ├── postgres_password.txt
│   ├── jwt_secret_key.txt
│   └── ...
├── scripts/
│   ├── generate-secrets.sh   # Generate production secrets
│   ├── generate-secrets.ps1  # Windows version
│   ├── validate-env.py       # Validate environment
│   └── validate-all-services.sh
└── services/
    ├── core-api/
    │   ├── .env.example
    │   ├── .env.development
    │   ├── .env.staging
    │   └── .env.production
    └── ...
```

## Quick Start

### Development Setup

```bash
# 1. Copy environment files
cp .env.development .env
cp services/core-api/.env.example services/core-api/.env

# 2. Start services
docker-compose up -d

# 3. Verify
docker-compose ps
```

### Production Setup

```bash
# 1. Generate secrets
./scripts/generate-secrets.sh production

# 2. Configure external services
# Edit files in secrets/ directory

# 3. Validate configuration
./scripts/validate-all-services.sh production

# 4. Deploy with secrets
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
```

## Core API Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection | `redis://redis:6379` |
| `JWT_SECRET_KEY` | JWT signing key | `<64-char-random>` |
| `AGENT_IA_API_KEY` | Agent IA auth | `<32-char-random>` |
| `ANALYTICS_API_KEY` | Analytics auth | `<32-char-random>` |
| `MINIO_ENDPOINT` | MinIO endpoint | `minio:9000` |
| `MINIO_SECRET_KEY` | MinIO secret | `<48-char-random>` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `RS256` | JWT algorithm |
| `LOG_LEVEL` | `INFO` | Logging level |
| `TIMEZONE` | `America/Bogota` | System timezone |

## Agent IA Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `CORE_API_URL` | Core API endpoint | `http://core-api:8000` |
| `SERVICE_API_KEY` | Service auth key | `<32-char-random>` |
| `REDIS_URL` | Redis connection | `redis://redis:6379` |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp token | `<meta-token>` |
| `OPENAI_API_KEY` | OpenAI key | `<openai-key>` |

### LLM Providers

| Variable | Required | Cost Level |
|----------|----------|------------|
| `OPENAI_API_KEY` | Yes (Prod) | Medium |
| `ANTHROPIC_API_KEY` | Optional | Premium |
| `GEMINI_API_KEY` | Optional | Medium |
| `DEEPSEEK_API_KEY` | Optional | Low |

## Analytics Service Variables

### Required

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection (read replica) |
| `REDIS_URL` | Redis connection |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_POOL_SIZE` | `20` | Connection pool size |
| `KPI_CACHE_TTL_SECONDS` | `300` | KPI cache duration |
| `ALERTS_ENABLED` | `true` | Enable alerting |

## Realtime Gateway Vari
ables

### Required

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | Redis connection |
| `JWT_SECRET_KEY` | JWT verification key |

## Files Service Variables

### Required

| Variable | Description |
|----------|-------------|
| `MINIO_ENDPOINT` | MinIO endpoint |
| `MINIO_ACCESS_KEY` | MinIO access key |
| `MINIO_SECRET_KEY` | MinIO secret key |
| `REDIS_URL` | Redis connection |

## Frontend Variables

### Admin & Advisor Frontends

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Core API URL | `http://localhost:8000` |
| `VITE_REALTIME_URL` | Realtime Gateway URL | `http://localhost:8003` |
| `VITE_ENVIRONMENT` | Environment name | `development` |

## Secrets Management

### Docker Secrets (Production)

TeLOO V3 uses Docker secrets for secure credential management in production.

#### Generate Secrets

```bash
# Linux/Mac
./scripts/generate-secrets.sh production

# Windows
.\scripts\generate-secrets.ps1 -Environment production
```

#### Required Secret Files

Create these files in `secrets/` directory:

**Infrastructure:**
- `postgres_password.txt`
- `redis_password.txt`
- `minio_access_key.txt`
- `minio_secret_key.txt`

**Application:**
- `jwt_secret_key.txt` (64+ characters)
- `agent_ia_api_key.txt`
- `analytics_api_key.txt`

**External Services:**
- `whatsapp_access_token.txt`
- `whatsapp_verify_token.txt`
- `whatsapp_webhook_secret.txt`
- `telegram_bot_token.txt`
- `openai_api_key.txt`
- `anthropic_api_key.txt`
- `gemini_api_key.txt`
- `deepseek_api_key.txt`

**Monitoring:**
- `smtp_password.txt`
- `slack_webhook_url.txt`

#### Using Secrets

Secrets are automatically loaded from files when `{SECRET_NAME}_FILE` environment variable is set:

```python
# In application code
from utils.secrets import get_secret

jwt_secret = get_secret('JWT_SECRET_KEY')
db_url = get_database_url()
```

## Validation

### Automatic Validation

All services validate environment variables on startup.

### Manual Validation

```bash
# Single service
SERVICE_NAME=core-api python scripts/validate-env.py

# All services
./scripts/validate-all-services.sh production
```

### Validation Checks

- ✅ Required variables are set
- ✅ URLs are properly formatted
- ✅ Production secrets are strong
- ✅ Secret length meets minimums
- ⚠️  Optional variables use defaults

## Security Best Practices

### 🔒 Critical Rules

1. **Never commit secrets to version control**
2. **Use strong random secrets** (32+ characters)
3. **Rotate secrets regularly** (90 days for DB, 180 days for APIs)
4. **Separate secrets by environment**
5. **Backup secrets encrypted**

### Generate Strong Secrets

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Using script
./scripts/generate-secrets.sh production
```

### Verify Secret Strength

Production secrets must NOT contain:
- `test`, `dev`, `development`
- `example`, `your-`, `change-in-production`
- `12345`, `password`, `secret`

## Troubleshooting

### Connection Refused

```bash
# Check services running
docker-compose ps

# Verify URLs
grep -E "DATABASE_URL|REDIS_URL" .env

# Check network
docker network inspect teloo-network
```

### Authentication Failed

```bash
# Verify API keys match
grep AGENT_IA_API_KEY services/core-api/.env
grep SERVICE_API_KEY services/agent-ia/.env

# Regenerate if needed
./scripts/generate-secrets.sh production
```

### Secret File Not Found

```bash
# Check secrets exist
ls -la secrets/

# Verify Docker Compose
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml config

# Check mounted secrets
docker exec teloo-core-api ls -la /run/secrets/
```

## Environment Migration

### Development → Staging

1. Copy `.env.development` to `.env.staging`
2. Update credentials to staging values
3. Change `ENVIRONMENT=staging`
4. Update URLs to staging endpoints
5. Test thoroughly

### Staging → Production

1. Generate production secrets: `./scripts/generate-secrets.sh production`
2. Copy `.env.staging` to `.env.production`
3. Replace ALL secrets with production values
4. Change `ENVIRONMENT=production`
5. Validate: `./scripts/validate-all-services.sh production`
6. Deploy with secrets

## Additional Resources

- **[Complete Guide](./docs/ENVIRONMENT_VARIABLES_GUIDE.md)** - Full documentation
- **[Quick Reference](./docs/ENV_QUICK_REFERENCE.md)** - Quick reference card
- **[Deployment Checklist](./docs/DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[Secrets README](./secrets/README.md)** - Secrets management guide

## Support

For environment configuration issues:

1. Check this documentation
2. Run validation: `./scripts/validate-all-services.sh`
3. Check service logs: `docker-compose logs <service>`
4. Review [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
5. Contact DevOps team

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintained By**: TeLOO DevOps Team
