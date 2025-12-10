#!/bin/bash
# Generate Docker Secrets for TeLOO V3
# This script generates secure random secrets for production deployment

set -e

SECRETS_DIR="./secrets"
ENVIRONMENT="${1:-production}"

echo "=========================================="
echo "TeLOO V3 Secrets Generator"
echo "Environment: $ENVIRONMENT"
echo "=========================================="
echo ""

# Create secrets directory
mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"

# Function to generate a secure random string
generate_secret() {
    local length="${1:-32}"
    python3 -c "import secrets; print(secrets.token_urlsafe($length))"
}

# Function to create secret file
create_secret() {
    local name="$1"
    local value="$2"
    local file="$SECRETS_DIR/${name}.txt"
    
    if [ -f "$file" ] && [ "$ENVIRONMENT" = "production" ]; then
        echo "⚠️  WARNING: $name already exists. Skipping to avoid overwriting production secret."
        return
    fi
    
    echo "$value" > "$file"
    chmod 600 "$file"
    echo "✓ Generated: $name"
}

echo "Generating infrastructure secrets..."
echo ""

# Database Secrets
create_secret "postgres_password" "$(generate_secret 32)"

# Redis Secrets
create_secret "redis_password" "$(generate_secret 32)"

# MinIO Secrets
create_secret "minio_access_key" "teloo_minio_$(generate_secret 16)"
create_secret "minio_secret_key" "$(generate_secret 48)"

echo ""
echo "Generating application secrets..."
echo ""

# JWT Secrets (longer for production)
create_secret "jwt_secret_key" "$(generate_secret 64)"

# Service Authentication
create_secret "agent_ia_api_key" "$(generate_secret 32)"
create_secret "analytics_api_key" "$(generate_secret 32)"

echo ""
echo "=========================================="
echo "IMPORTANT: External Service Configuration"
echo "=========================================="
echo ""
echo "The following secrets require manual configuration:"
echo ""
echo "1. WhatsApp API (Meta Business):"
echo "   - whatsapp_access_token.txt"
echo "   - whatsapp_verify_token.txt"
echo "   - whatsapp_webhook_secret.txt"
echo ""
echo "2. Telegram Bot:"
echo "   - telegram_bot_token.txt"
echo ""
echo "3. LLM API Keys:"
echo "   - openai_api_key.txt"
echo "   - anthropic_api_key.txt"
echo "   - gemini_api_key.txt"
echo "   - deepseek_api_key.txt"
echo ""
echo "4. Email/Alerts:"
echo "   - smtp_password.txt"
echo "   - slack_webhook_url.txt"
echo ""
echo "Please create these files manually with your actual credentials."
echo ""

# Create placeholder files for manual secrets
create_placeholder() {
    local name="$1"
    local description="$2"
    local file="$SECRETS_DIR/${name}.txt"
    
    if [ ! -f "$file" ]; then
        echo "REPLACE_WITH_YOUR_${name^^}" > "$file"
        chmod 600 "$file"
        echo "⚠️  Created placeholder: $name - $description"
    fi
}

echo "Creating placeholder files for manual secrets..."
echo ""

create_placeholder "whatsapp_access_token" "WhatsApp Business API access token"
create_placeholder "whatsapp_verify_token" "WhatsApp webhook verification token"
create_placeholder "whatsapp_webhook_secret" "WhatsApp webhook secret"
create_placeholder "telegram_bot_token" "Telegram Bot API token"
create_placeholder "openai_api_key" "OpenAI API key"
create_placeholder "anthropic_api_key" "Anthropic Claude API key"
create_placeholder "gemini_api_key" "Google Gemini API key"
create_placeholder "deepseek_api_key" "Deepseek API key"
create_placeholder "smtp_password" "SMTP server password"
create_placeholder "slack_webhook_url" "Slack webhook URL for alerts"

echo ""
echo "=========================================="
echo "Secrets Generation Complete!"
echo "=========================================="
echo ""
echo "Generated secrets are stored in: $SECRETS_DIR"
echo ""
echo "⚠️  SECURITY WARNINGS:"
echo "1. Never commit the secrets/ directory to version control"
echo "2. Ensure secrets/ is in .gitignore"
echo "3. Backup secrets securely (encrypted storage)"
echo "4. Rotate secrets regularly (every 90 days recommended)"
echo "5. Replace all placeholder values before deployment"
echo ""
echo "Next steps:"
echo "1. Review and update placeholder secrets with real values"
echo "2. Verify all secrets are properly set"
echo "3. Deploy using: docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d"
echo ""
