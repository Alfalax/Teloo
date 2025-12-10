# Validate environment variables for all TeLOO V3 services (PowerShell)

param(
    [string]$Environment = "development"
)

$ErrorActionPreference = "Stop"
$Failed = 0

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TeLOO V3 - Validate All Services" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variable
$env:ENVIRONMENT = $Environment

# Load environment file if it exists
$EnvFile = ".env.$Environment"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment from: $EnvFile" -ForegroundColor Yellow
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host ""
}

# Services to validate
$Services = @("core-api", "agent-ia", "analytics", "realtime-gateway", "files")

foreach ($Service in $Services) {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Validating: $Service" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Load service-specific env file if exists
    $ServiceEnvFile = "services/$Service/.env.$Environment"
    if (Test-Path $ServiceEnvFile) {
        Write-Host "Loading service environment from: $ServiceEnvFile" -ForegroundColor Yellow
        Get-Content $ServiceEnvFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
    
    # Run validation
    $env:SERVICE_NAME = $Service
    
    try {
        python scripts/validate-env.py
        Write-Host ""
        Write-Host "✅ $Service validation PASSED" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host ""
        Write-Host "❌ $Service validation FAILED" -ForegroundColor Red
        Write-Host ""
        $Failed++
    }
    
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total services: $($Services.Count)"
Write-Host "Passed: $($Services.Count - $Failed)" -ForegroundColor Green
Write-Host "Failed: $Failed" -ForegroundColor $(if ($Failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($Failed -eq 0) {
    Write-Host "✅ All services validated successfully!" -ForegroundColor Green
    Write-Host ""
    exit 0
}
else {
    Write-Host "❌ $Failed service(s) failed validation" -ForegroundColor Red
    Write-Host "Please fix the issues before deployment" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
