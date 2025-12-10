#!/bin/bash

# Script to test CI/CD pipeline locally before pushing to GitHub
# This helps catch issues early and speeds up development

set -e

echo "🚀 TeLOO V3 - Local CI/CD Testing"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    echo "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_status "Docker is installed"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_status "Docker Compose is installed"
    
    if ! command -v python3 &> /dev/null; then
        print_warning "Python3 is not installed (optional for linting)"
    else
        print_status "Python3 is installed"
    fi
    
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed (optional for frontend linting)"
    else
        print_status "Node.js is installed"
    fi
    
    echo ""
}

# Run Python linting
run_python_lint() {
    echo "Running Python linting..."
    
    if ! command -v python3 &> /dev/null; then
        print_warning "Skipping Python linting (Python3 not installed)"
        return
    fi
    
    # Install linting tools if not present
    pip3 install --quiet black isort flake8 bandit 2>/dev/null || true
    
    # Run black
    if command -v black &> /dev/null; then
        echo "  - Running black..."
        black --check services/ 2>/dev/null && print_status "Black passed" || print_error "Black failed"
    fi
    
    # Run isort
    if command -v isort &> /dev/null; then
        echo "  - Running isort..."
        isort --check-only services/ 2>/dev/null && print_status "isort passed" || print_error "isort failed"
    fi
    
    # Run flake8
    if command -v flake8 &> /dev/null; then
        echo "  - Running flake8..."
        flake8 services/ --max-line-length=120 --extend-ignore=E203,W503 2>/dev/null && print_status "flake8 passed" || print_error "flake8 failed"
    fi
    
    # Run bandit
    if command -v bandit &> /dev/null; then
        echo "  - Running bandit..."
        bandit -r services/ -ll 2>/dev/null && print_status "bandit passed" || print_error "bandit failed"
    fi
    
    echo ""
}

# Build Docker images
build_images() {
    echo "Building Docker images..."
    
    services=("core-api" "agent-ia" "analytics" "realtime-gateway" "files")
    
    for service in "${services[@]}"; do
        echo "  - Building $service..."
        docker build -t teloo-$service:test ./services/$service > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_status "$service built successfully"
        else
            print_error "$service build failed"
            exit 1
        fi
    done
    
    # Build frontends
    echo "  - Building admin-frontend..."
    docker build -t teloo-admin-frontend:test ./frontend/admin > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "admin-frontend built successfully"
    else
        print_error "admin-frontend build failed"
        exit 1
    fi
    
    echo "  - Building advisor-frontend..."
    docker build -t teloo-advisor-frontend:test ./frontend/advisor > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "advisor-frontend built successfully"
    else
        print_error "advisor-frontend build failed"
        exit 1
    fi
    
    echo ""
}

# Run security scan with Trivy
run_security_scan() {
    echo "Running security scans..."
    
    if ! command -v trivy &> /dev/null; then
        print_warning "Trivy not installed, skipping security scan"
        print_warning "Install with: brew install aquasecurity/trivy/trivy (macOS)"
        print_warning "Or: wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add - (Ubuntu)"
        echo ""
        return
    fi
    
    services=("core-api" "agent-ia" "analytics" "realtime-gateway" "files" "admin-frontend" "advisor-frontend")
    
    for service in "${services[@]}"; do
        echo "  - Scanning teloo-$service:test..."
        trivy image --severity HIGH,CRITICAL --quiet teloo-$service:test
        if [ $? -eq 0 ]; then
            print_status "$service scan passed"
        else
            print_warning "$service has vulnerabilities"
        fi
    done
    
    echo ""
}

# Run tests
run_tests() {
    echo "Running tests..."
    
    # Start test dependencies
    echo "  - Starting test dependencies (PostgreSQL, Redis)..."
    docker-compose up -d postgres redis > /dev/null 2>&1
    sleep 5
    
    # Run core-api tests
    echo "  - Running core-api tests..."
    cd services/core-api
    if [ -f "requirements.txt" ]; then
        pip3 install --quiet -r requirements.txt 2>/dev/null || true
        pip3 install --quiet pytest pytest-asyncio 2>/dev/null || true
        
        export DATABASE_URL="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3"
        export REDIS_URL="redis://localhost:6379"
        export JWT_SECRET_KEY="test-secret-key"
        export ENVIRONMENT="test"
        
        pytest tests/ -v 2>/dev/null && print_status "core-api tests passed" || print_warning "core-api tests failed"
    fi
    cd ../..
    
    # Run agent-ia tests
    echo "  - Running agent-ia tests..."
    cd services/agent-ia
    if [ -f "requirements.txt" ]; then
        pip3 install --quiet -r requirements.txt 2>/dev/null || true
        pip3 install --quiet pytest pytest-asyncio 2>/dev/null || true
        
        export CORE_API_URL="http://localhost:8000"
        export REDIS_URL="redis://localhost:6379"
        export ENVIRONMENT="test"
        
        pytest tests/ -v 2>/dev/null && print_status "agent-ia tests passed" || print_warning "agent-ia tests failed"
    fi
    cd ../..
    
    # Stop test dependencies
    docker-compose down > /dev/null 2>&1
    
    echo ""
}

# Run integration tests
run_integration_tests() {
    echo "Running integration tests..."
    
    # Start all services
    echo "  - Starting all services..."
    docker-compose up -d > /dev/null 2>&1
    
    # Wait for services to be ready
    echo "  - Waiting for services to be ready..."
    sleep 30
    
    # Test health endpoints
    echo "  - Testing health endpoints..."
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "core-api health check passed"
    else
        print_error "core-api health check failed"
    fi
    
    if curl -f http://localhost:8000/health/ready > /dev/null 2>&1; then
        print_status "core-api readiness check passed"
    else
        print_error "core-api readiness check failed"
    fi
    
    # Stop services
    echo "  - Stopping services..."
    docker-compose down > /dev/null 2>&1
    
    echo ""
}

# Cleanup
cleanup() {
    echo "Cleaning up..."
    docker-compose down -v > /dev/null 2>&1
    print_status "Cleanup complete"
    echo ""
}

# Main execution
main() {
    check_requirements
    
    # Parse arguments
    RUN_LINT=true
    RUN_BUILD=true
    RUN_SCAN=true
    RUN_TESTS=true
    RUN_INTEGRATION=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-lint)
                RUN_LINT=false
                shift
                ;;
            --skip-build)
                RUN_BUILD=false
                shift
                ;;
            --skip-scan)
                RUN_SCAN=false
                shift
                ;;
            --skip-tests)
                RUN_TESTS=false
                shift
                ;;
            --integration)
                RUN_INTEGRATION=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-lint        Skip Python linting"
                echo "  --skip-build       Skip Docker image builds"
                echo "  --skip-scan        Skip security scanning"
                echo "  --skip-tests       Skip unit tests"
                echo "  --integration      Run integration tests"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run selected tests
    if [ "$RUN_LINT" = true ]; then
        run_python_lint
    fi
    
    if [ "$RUN_BUILD" = true ]; then
        build_images
    fi
    
    if [ "$RUN_SCAN" = true ]; then
        run_security_scan
    fi
    
    if [ "$RUN_TESTS" = true ]; then
        run_tests
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
    fi
    
    cleanup
    
    echo "=================================="
    echo -e "${GREEN}✓ All checks completed!${NC}"
    echo "You can now push your changes to GitHub"
    echo ""
}

# Run main function
main "$@"
