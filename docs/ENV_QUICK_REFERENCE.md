# Environment Variables Quick Reference

Quick reference card for TeLOO V3 environment variables.

## 🚀 Quick Start Commands

```bash
# Development
docker-compose up -d

# Staging
docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d

# Production with secrets
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
```

## 🔑 Generate Secrets

```bash
# Linux/Mac
./scripts/generate-secrets.sh production

# Windows
.\scripts\generate-secrets.ps1 -Environment production

# Manual (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## ✅ Validate Configuration

```bash
# Single service
SERVICE_NAME=core-api python scripts/validate-env.py

# All services
./scripts/validate-all-services.sh production
```

## 📋 Critical Variables by Service

### Core API
```bash
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=<64-char-secret>
AGENT_IA_API_KEY=<32-char-secret>
ANALYTICS_API_KEY=<32-char-secret>
MINIO_ENDPOINT=minio:9000
MINIO_SECRET_KEY=<48-char-secret>
```

### Agent IA
```bash
CORE_API_URL=http://core-api:8000
SERVICE_API_KEY=<32-char-secret>
REDIS_URL=redis://redis:6379
WHATSAPP_ACCESS_TOKEN=<meta-token>
WHATSAPP_PHONE_NUMBER_ID=<meta-id>
OPENAI_API_KEY=<openai-key>
```

### Analytics
```bash
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://redis:6379
SMTP_PASSWORD=<smtp-password>
SLACK_WEBHOOK_URL=<slack-webhook>
```

### Realtime Gateway
```bash
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=<64-char-secret>
```

### Files
```bash
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<48-char-secret>
REDIS_URL=redis://redis:6379
```

## 🔒 Security Checklist

- [ ] No default values in production (`test`, `dev`, `example`)
- [ ] Secrets minimum 32 characters (64 for JWT)
- [ ] `secrets/` directory in `.gitignore`
- [ ] Secret files have 600 permissions
- [ ] Secrets backed up and encrypted
- [ ] Different secrets per environment

## 🐛 Common Issues

### Connection Refused
```bash
# Check service is running
docker-compose ps

# Check network
docker network inspect teloo-network

# Verify URLs in .env
grep -E "DATABASE_URL|REDIS_URL" .env
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

# Verify Docker Compose config
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml config

# Check mounted secrets
docker exec teloo-core-api ls -la /run/secrets/
```

## 📁 File Structure

```
teloo-v3/
├── .env.development          # Dev shared vars
├── .env.staging              # Staging shared vars
├── .env.production           # Prod shared vars
├── secrets/                  # Production secrets
│   ├── postgres_password.txt
│   ├── jwt_secret_key.txt
│   └── ...
└── services/
    ├── core-api/
    │   ├── .env.example
    │   └── .env.production
    └── ...
```

## 🔄 Environment Migration

### Dev → Staging
1. Copy `.env.development` to `.env.staging`
2. Update credentials to staging values
3. Change `ENVIRONMENT=staging`
4. Test thoroughly

### Staging → Production
1. Generate production secrets
2. Copy `.env.staging` to `.env.production`
3. Replace ALL secrets with production values
4. Change `ENVIRONMENT=production`
5. Validate: `./scripts/validate-all-services.sh production`
6. Deploy with secrets

## 📞 Support

- Full Guide: [Environment Variables Guide](./ENVIRONMENT_VARIABLES_GUIDE.md)
- Deployment: [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- Secrets: [Secrets README](../secrets/README.md)

## 🔗 External Services

### WhatsApp Business API
- Get token: https://developers.facebook.com/apps/
- Webhook setup required
- Test mode available

### OpenAI API
- Get key: https://platform.openai.com/api-keys
- Recommended model: `gpt-4o-mini`
- Monitor usage/costs

### Anthropic Claude
- Get key: https://console.anthropic.com/
- Optional but recommended
- Good for multimedia

### Google Gemini
- Get key: https://makersuite.google.com/app/apikey
- Optional
- Good for complex text

## 💰 Cost Optimization

### LLM Provider Costs (per 1M tokens)
- Deepseek: $0.14 (cheapest)
- Gemini: $1.25 (medium)
- OpenAI GPT-4o-mini: $0.15 (recommended)
- OpenAI GPT-4o: $5.00 (premium)
- Anthropic Claude: $15.00 (premium)

### Strategy
1. Use Deepseek/Ollama for simple text
2. Use Gemini for complex text
3. Use OpenAI for documents
4. Use Anthropic for multimedia
5. Enable caching (24h TTL)
6. Monitor costs daily

## 🎯 Production Readiness

Before deploying to production:

1. ✅ All secrets generated and strong
2. ✅ All validations passing
3. ✅ External services configured
4. ✅ Database/Redis/MinIO ready
5. ✅ Backups configured
6. ✅ Monitoring/alerts set up
7. ✅ SSL/TLS certificates installed
8. ✅ Smoke tests passing

---

**Quick Links**:
- [Full Documentation](./ENVIRONMENT_VARIABLES_GUIDE.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
