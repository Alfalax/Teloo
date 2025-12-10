#!/bin/bash
# Test script for TeLOO V3 health checks
# This script tests all health check endpoints for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service definitions: name:port
SERVICES=(
  "core-api:8000"
  "agent-ia:8001"
  "analytics:8002"
  "files:8003"
  "realtime-gateway:8004"
)

# Health check endpoints
ENDPOINTS=(
  "/health"
  "/health/ready"
  "/health/live"
)

echo "========================================="
echo "TeLOO V3 Health Check Test Suite"
echo "========================================="
echo ""

total_tests=0
passed_tests=0
failed_tests=0

# Function to test an endpoint
test_endpoint() {
  local service_name=$1
  local port=$2
  local endpoint=$3
  local url="http://localhost:$port$endpoint"
  
  total_tests=$((total_tests + 1))
  
  # Make request with timeout
  response=$(curl -s -w "\n%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  # Check if request succeeded
  if [ "$http_code" = "200" ] || [ "$http_code" = "503" ]; then
    echo -e "${GREEN}✓${NC} $service_name $endpoint - HTTP $http_code"
    passed_tests=$((passed_tests + 1))
    
    # Validate JSON response
    if echo "$body" | jq empty 2>/dev/null; then
      echo "  └─ Valid JSON response"
    else
      echo -e "  ${YELLOW}└─ Warning: Invalid JSON response${NC}"
    fi
  else
    echo -e "${RED}✗${NC} $service_name $endpoint - HTTP $http_code (Expected 200 or 503)"
    failed_tests=$((failed_tests + 1))
    
    if [ "$http_code" = "000" ]; then
      echo "  └─ Service not reachable (connection refused or timeout)"
    fi
  fi
}

# Test each service
for service in "${SERVICES[@]}"; do
  IFS=':' read -r name port <<< "$service"
  
  echo ""
  echo "Testing $name (port $port)..."
  echo "-----------------------------------"
  
  for endpoint in "${ENDPOINTS[@]}"; do
    test_endpoint "$name" "$port" "$endpoint"
  done
done

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Total tests: $total_tests"
echo -e "${GREEN}Passed: $passed_tests${NC}"
if [ $failed_tests -gt 0 ]; then
  echo -e "${RED}Failed: $failed_tests${NC}"
else
  echo "Failed: $failed_tests"
fi
echo ""

# Exit with appropriate code
if [ $failed_tests -gt 0 ]; then
  echo -e "${RED}Some health checks failed!${NC}"
  echo "Note: Services may not be running. Start them with:"
  echo "  docker-compose up -d"
  exit 1
else
  echo -e "${GREEN}All health checks passed!${NC}"
  exit 0
fi
