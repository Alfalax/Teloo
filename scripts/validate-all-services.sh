#!/bin/bash
# Validate environment variables for all TeLOO V3 services

set -e

ENVIRONMENT="${1:-development}"
FAILED=0

echo "=========================================="
echo "TeLOO V3 - Validate All Services"
echo "Environment: $ENVIRONMENT"
echo "=========================================="
echo ""

# Export environment for validation script
export ENVIRONMENT="$ENVIRONMENT"

# Load environment file if it exists
ENV_FILE=".env.${ENVIRONMENT}"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
    echo ""
fi

# Services to validate
SERVICES=("core-api" "agent-ia" "analytics" "realtime-gateway" "files")

for SERVICE in "${SERVICES[@]}"; do
    echo "=========================================="
    echo "Validating: $SERVICE"
    echo "=========================================="
    echo ""
    
    # Load service-specific env file if exists
    SERVICE_ENV_FILE="services/${SERVICE}/.env.${ENVIRONMENT}"
    if [ -f "$SERVICE_ENV_FILE" ]; then
        echo "Loading service environment from: $SERVICE_ENV_FILE"
        set -a
        source "$SERVICE_ENV_FILE"
        set +a
    fi
    
    # Run validation
    export SERVICE_NAME="$SERVICE"
    if python3 scripts/validate-env.py; then
        echo ""
        echo "✅ $SERVICE validation PASSED"
        echo ""
    else
        echo ""
        echo "❌ $SERVICE validation FAILED"
        echo ""
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo "Total services: ${#SERVICES[@]}"
echo "Passed: $((${#SERVICES[@]} - FAILED))"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All services validated successfully!"
    echo ""
    exit 0
else
    echo "❌ $FAILED service(s) failed validation"
    echo "Please fix the issues before deployment"
    echo ""
    exit 1
fi
