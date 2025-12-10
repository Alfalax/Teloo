# Generate Docker Secrets for TeLOO V3 (PowerShell version)
# This script generates secure random secrets for production deployment

param(
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

$SecretsDir = "./secrets"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TeLOO V3 Secrets Generator" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Create secrets directory
if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir | Out-Null
}

# Function to generate a secure random string
function Generate-Secret {
    param([int]$Length = 32)
    
    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    
    return [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
}

# Function to create secret file
function Create-Secret {
    param(
        [string]$Name,
        [string]$Value
    )
    
    $file = Join-Path $SecretsDir "$Name.txt"
    
    if ((Test-Path $file) -and ($Environment -eq "production")) {
        Write-Host "⚠️  WARNING: $Name already exists. Skipping to avoid overwriting production secret." -ForegroundColor Yellow
        return
    }
    
    $Value | Out-File -FilePath $file -Encoding UTF8 -NoNewline
    Write-Host "✓ Generated: $Name" -ForegroundColor Green
}

Write-Host "Generating infrastructure secrets..." -ForegroundColor Yellow
Write-Host ""

# Database Secrets
Create-Secret "postgres_password" (Generate-Secret 32)

# Redis Secrets
Create-Secret "redis_password" (Generate-Secret 32)

# MinIO Secrets
Create-Secret "minio_access_key" "teloo_minio_$(Generate-Secret 16)"
Create-Secret "minio_secret_key" (Generate-Secret 48)

Write-Host ""
Write-Host "Generating application secrets..." -ForegroundColor Yellow
Write-Host ""

# JWT Secrets (longer for production)
Create-Secret "jwt_secret_key" (Generate-Secret 64)

# Service Authentication
Create-Secret "agent_ia_api_key" (Generate-Secret 32)
Create-Secret "analytics_api_key" (Generate-Secret 32)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "IMPORTANT: External Service Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The following secrets require manual configuration:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. WhatsApp API (Meta Business):"
Write-Host "   - whatsapp_access_token.txt"
Write-Host "   - whatsapp_verify_token.txt"
Write-Host "   - whatsapp_webhook_secret.txt"
Write-Host ""
Write-Host "2. Telegram Bot:"
Write-Host "   - telegram_bot_token.txt"
Write-Host ""
Write-Host "3. LLM API Keys:"
Write-Host "   - openai_api_key.txt"
Write-Host "   - anthropic_api_key.txt"
Write-Host "   - gemini_api_key.txt"
Write-Host "   - deepseek_api_key.txt"
Write-Host ""
Write-Host "4. Email/Alerts:"
Write-Host "   - smtp_password.txt"
Write-Host "   - slack_webhook_url.txt"
Write-Host ""
Write-Host "Please create these files manually with your actual credentials." -ForegroundColor Yellow
Write-Host ""

# Create placeholder files for manual secrets
function Create-Placeholder {
    param(
        [string]$Name,
        [string]$Description
    )
    
    $file = Join-Path $SecretsDir "$Name.txt"
    
    if (-not (Test-Path $file)) {
        "REPLACE_WITH_YOUR_$($Name.ToUpper())" | Out-File -FilePath $file -Encoding UTF8 -NoNewline
        Write-Host "⚠️  Created placeholder: $Name - $Description" -ForegroundColor Yellow
    }
}

Write-Host "Creating placeholder files for manual secrets..." -ForegroundColor Yellow
Write-Host ""

Create-Placeholder "whatsapp_access_token" "WhatsApp Business API access token"
Create-Placeholder "whatsapp_verify_token" "WhatsApp webhook verification token"
Create-Placeholder "whatsapp_webhook_secret" "WhatsApp webhook secret"
Create-Placeholder "telegram_bot_token" "Telegram Bot API token"
Create-Placeholder "openai_api_key" "OpenAI API key"
Create-Placeholder "anthropic_api_key" "Anthropic Claude API key"
Create-Placeholder "gemini_api_key" "Google Gemini API key"
Create-Placeholder "deepseek_api_key" "Deepseek API key"
Create-Placeholder "smtp_password" "SMTP server password"
Create-Placeholder "slack_webhook_url" "Slack webhook URL for alerts"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Secrets Generation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated secrets are stored in: $SecretsDir" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  SECURITY WARNINGS:" -ForegroundColor Red
Write-Host "1. Never commit the secrets/ directory to version control"
Write-Host "2. Ensure secrets/ is in .gitignore"
Write-Host "3. Backup secrets securely (encrypted storage)"
Write-Host "4. Rotate secrets regularly (every 90 days recommended)"
Write-Host "5. Replace all placeholder values before deployment"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review and update placeholder secrets with real values"
Write-Host "2. Verify all secrets are properly set"
Write-Host "3. Deploy using: docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d"
Write-Host ""
