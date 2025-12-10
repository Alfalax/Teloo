#!/bin/bash

# Rollback Script for TeLOO V3
# This script rolls back deployments in Kubernetes or Docker Swarm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ORCHESTRATOR="${ORCHESTRATOR:-kubernetes}"  # kubernetes or swarm
NAMESPACE="${NAMESPACE:-teloo-production}"
STACK_NAME="${STACK_NAME:-teloo}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TeLOO V3 Rollback Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Orchestrator: $ORCHESTRATOR"
echo ""

# Function to rollback Kubernetes deployment
rollback_kubernetes() {
    local service=$1
    
    echo -e "${YELLOW}Rolling back $service in Kubernetes...${NC}"
    
    # Check if deployment exists
    if ! kubectl get deployment $service -n $NAMESPACE &> /dev/null; then
        echo -e "${RED}Error: Deployment $service not found${NC}"
        return 1
    fi
    
    # Get rollout history
    echo -e "${YELLOW}Rollout history for $service:${NC}"
    kubectl rollout history deployment/$service -n $NAMESPACE
    echo ""
    
    # Perform rollback
    kubectl rollout undo deployment/$service -n $NAMESPACE
    
    # Wait for rollback to complete
    echo -e "${YELLOW}Waiting for rollback to complete...${NC}"
    kubectl rollout status deployment/$service -n $NAMESPACE
    
    echo -e "${GREEN}✓ Rollback completed for $service${NC}"
}

# Function to rollback Docker Swarm service
rollback_swarm() {
    local service=$1
    local full_service_name="${STACK_NAME}_${service}"
    
    echo -e "${YELLOW}Rolling back $service in Docker Swarm...${NC}"
    
    # Check if service exists
    if ! docker service inspect $full_service_name &> /dev/null; then
        echo -e "${RED}Error: Service $full_service_name not found${NC}"
        return 1
    fi
    
    # Perform rollback
    docker service rollback $full_service_name
    
    # Wait for rollback to complete
    echo -e "${YELLOW}Waiting for rollback to complete...${NC}"
    local max_wait=300
    local elapsed=0
    local interval=5
    
    while [ $elapsed -lt $max_wait ]; do
        local state=$(docker service inspect $full_service_name --format '{{.UpdateStatus.State}}')
        
        if [ "$state" == "completed" ] || [ "$state" == "" ]; then
            echo -e "${GREEN}✓ Rollback completed for $service${NC}"
            return 0
        elif [ "$state" == "rollback_paused" ] || [ "$state" == "rollback_failed" ]; then
            echo -e "${RED}Error: Rollback failed for $service${NC}"
            return 1
        fi
        
        echo -e "${YELLOW}  Rollback state: $state ($elapsed/$max_wait seconds)${NC}"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo -e "${YELLOW}Warning: Rollback may still be in progress${NC}"
}

# Function to rollback all services
rollback_all() {
    local services=("core-api" "agent-ia" "analytics" "realtime-gateway" "files" "admin-frontend" "advisor-frontend")
    
    echo -e "${YELLOW}Rolling back all services...${NC}"
    echo ""
    
    for service in "${services[@]}"; do
        if [ "$ORCHESTRATOR" == "kubernetes" ]; then
            rollback_kubernetes $service
        else
            rollback_swarm $service
        fi
        echo ""
    done
    
    echo -e "${GREEN}✓ All services rolled back${NC}"
}

# Function to rollback specific service
rollback_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        echo -e "${RED}Error: Service name required${NC}"
        echo "Usage: $0 <service-name>"
        echo "Available services: core-api, agent-ia, analytics, realtime-gateway, files, admin-frontend, advisor-frontend"
        exit 1
    fi
    
    if [ "$ORCHESTRATOR" == "kubernetes" ]; then
        rollback_kubernetes $service
    else
        rollback_swarm $service
    fi
}

# Function to show rollback status
show_status() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Current Status${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [ "$ORCHESTRATOR" == "kubernetes" ]; then
        echo -e "${YELLOW}Deployments:${NC}"
        kubectl get deployments -n $NAMESPACE
        echo ""
        echo -e "${YELLOW}Pods:${NC}"
        kubectl get pods -n $NAMESPACE
    else
        echo -e "${YELLOW}Services:${NC}"
        docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    fi
}

# Main function
main() {
    if [ "$1" == "all" ]; then
        rollback_all
    elif [ ! -z "$1" ]; then
        rollback_service $1
    else
        echo -e "${YELLOW}Usage:${NC}"
        echo "  $0 all                    # Rollback all services"
        echo "  $0 <service-name>         # Rollback specific service"
        echo ""
        echo -e "${YELLOW}Available services:${NC}"
        echo "  - core-api"
        echo "  - agent-ia"
        echo "  - analytics"
        echo "  - realtime-gateway"
        echo "  - files"
        echo "  - admin-frontend"
        echo "  - advisor-frontend"
        echo ""
        echo -e "${YELLOW}Environment variables:${NC}"
        echo "  ORCHESTRATOR=kubernetes|swarm  (default: kubernetes)"
        echo "  NAMESPACE=<namespace>          (default: teloo-production)"
        echo "  STACK_NAME=<stack>             (default: teloo)"
        exit 1
    fi
    
    show_status
}

# Run main function
main "$@"
