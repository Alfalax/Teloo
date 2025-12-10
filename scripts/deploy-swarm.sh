#!/bin/bash

# Docker Swarm Deployment Script for TeLOO V3
# This script deploys the TeLOO application to a Docker Swarm cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="${STACK_NAME:-teloo}"
REGISTRY="${REGISTRY:-ghcr.io/your-org}"
IMAGE_VERSION="${IMAGE_VERSION:-latest}"
IMAGE_PREFIX="${IMAGE_PREFIX:-teloo}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TeLOO V3 Docker Swarm Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Registry: $REGISTRY"
echo "Image Version: $IMAGE_VERSION"
echo ""

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is installed${NC}"
}

# Function to check if Swarm is initialized
check_swarm() {
    if ! docker info | grep -q "Swarm: active"; then
        echo -e "${YELLOW}Swarm is not initialized. Initializing...${NC}"
        docker swarm init
        echo -e "${GREEN}✓ Swarm initialized${NC}"
    else
        echo -e "${GREEN}✓ Swarm is active${NC}"
    fi
}

# Function to create Docker secrets
create_secrets() {
    echo ""
    echo -e "${YELLOW}Creating Docker secrets...${NC}"
    
    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}Error: .env.production file not found${NC}"
        echo -e "${YELLOW}Please create .env.production with required secrets${NC}"
        exit 1
    fi
    
    # Source environment variables
    set -a
    source .env.production
    set +a
    
    # Create secrets if they don't exist
    create_secret_if_not_exists() {
        local secret_name=$1
        local secret_value=$2
        
        if docker secret inspect $secret_name &> /dev/null; then
            echo -e "${YELLOW}  Secret $secret_name already exists, skipping${NC}"
        else
            echo "$secret_value" | docker secret create $secret_name -
            echo -e "${GREEN}  ✓ Created secret: $secret_name${NC}"
        fi
    }
    
    # Database secrets
    create_secret_if_not_exists "postgres_password" "${POSTGRES_PASSWORD_PROD}"
    create_secret_if_not_exists "redis_password" "${REDIS_PASSWORD_PROD}"
    
    # MinIO secrets
    create_secret_if_not_exists "minio_access_key" "${MINIO_ACCESS_KEY_PROD}"
    create_secret_if_not_exists "minio_secret_key" "${MINIO_SECRET_KEY_PROD}"
    
    # JWT secret
    create_secret_if_not_exists "jwt_secret" "${JWT_SECRET_KEY_PROD}"
    
    # Service API keys
    create_secret_if_not_exists "agent_ia_api_key" "${AGENT_IA_API_KEY_PROD}"
    create_secret_if_not_exists "analytics_api_key" "${ANALYTICS_API_KEY_PROD}"
    
    # External API keys (optional)
    [ ! -z "${WHATSAPP_ACCESS_TOKEN_PROD}" ] && create_secret_if_not_exists "whatsapp_access_token" "${WHATSAPP_ACCESS_TOKEN_PROD}"
    [ ! -z "${WHATSAPP_WEBHOOK_VERIFY_TOKEN_PROD}" ] && create_secret_if_not_exists "whatsapp_verify_token" "${WHATSAPP_WEBHOOK_VERIFY_TOKEN_PROD}"
    [ ! -z "${TELEGRAM_BOT_TOKEN_PROD}" ] && create_secret_if_not_exists "telegram_bot_token" "${TELEGRAM_BOT_TOKEN_PROD}"
    [ ! -z "${OPENAI_API_KEY_PROD}" ] && create_secret_if_not_exists "openai_api_key" "${OPENAI_API_KEY_PROD}"
    [ ! -z "${ANTHROPIC_API_KEY_PROD}" ] && create_secret_if_not_exists "anthropic_api_key" "${ANTHROPIC_API_KEY_PROD}"
    [ ! -z "${GEMINI_API_KEY_PROD}" ] && create_secret_if_not_exists "gemini_api_key" "${GEMINI_API_KEY_PROD}"
    [ ! -z "${DEEPSEEK_API_KEY_PROD}" ] && create_secret_if_not_exists "deepseek_api_key" "${DEEPSEEK_API_KEY_PROD}"
    [ ! -z "${SMTP_PASSWORD_PROD}" ] && create_secret_if_not_exists "smtp_password" "${SMTP_PASSWORD_PROD}"
    [ ! -z "${SLACK_WEBHOOK_URL_PROD}" ] && create_secret_if_not_exists "slack_webhook_url" "${SLACK_WEBHOOK_URL_PROD}"
    
    echo -e "${GREEN}✓ Secrets created${NC}"
}

# Function to create networks
create_networks() {
    echo ""
    echo -e "${YELLOW}Creating overlay networks...${NC}"
    
    if ! docker network inspect teloo-backend &> /dev/null; then
        docker network create --driver overlay --attachable teloo-backend
        echo -e "${GREEN}  ✓ Created network: teloo-backend${NC}"
    else
        echo -e "${YELLOW}  Network teloo-backend already exists${NC}"
    fi
    
    if ! docker network inspect teloo-frontend &> /dev/null; then
        docker network create --driver overlay --attachable teloo-frontend
        echo -e "${GREEN}  ✓ Created network: teloo-frontend${NC}"
    else
        echo -e "${YELLOW}  Network teloo-frontend already exists${NC}"
    fi
    
    echo -e "${GREEN}✓ Networks ready${NC}"
}

# Function to deploy stack
deploy_stack() {
    echo ""
    echo -e "${YELLOW}Deploying stack...${NC}"
    
    # Export environment variables for docker-compose
    export REGISTRY
    export IMAGE_VERSION
    export IMAGE_PREFIX
    
    # Deploy the stack
    docker stack deploy -c docker-swarm-stack.yml $STACK_NAME
    
    echo -e "${GREEN}✓ Stack deployed${NC}"
}

# Function to wait for services
wait_for_services() {
    echo ""
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    
    local max_wait=300
    local elapsed=0
    local interval=10
    
    while [ $elapsed -lt $max_wait ]; do
        local running=$(docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME" --format "{{.Replicas}}" | grep -c "^[1-9]")
        local total=$(docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME" | wc -l)
        
        if [ $running -eq $((total - 1)) ]; then
            echo -e "${GREEN}✓ All services are running${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}  Waiting... ($elapsed/$max_wait seconds)${NC}"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo -e "${YELLOW}Warning: Some services may still be starting${NC}"
}

# Function to display deployment status
show_status() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Status${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}Services:${NC}"
    docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    echo ""
    
    echo -e "${YELLOW}Networks:${NC}"
    docker network ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    echo ""
    
    echo -e "${YELLOW}Volumes:${NC}"
    docker volume ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    echo ""
}

# Function to display next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "1. Check service status:"
    echo "   docker service ls"
    echo ""
    echo "2. View service logs:"
    echo "   docker service logs -f ${STACK_NAME}_core-api"
    echo ""
    echo "3. Scale a service:"
    echo "   docker service scale ${STACK_NAME}_core-api=5"
    echo ""
    echo "4. Update a service:"
    echo "   docker service update --image $REGISTRY/$IMAGE_PREFIX/core-api:new-version ${STACK_NAME}_core-api"
    echo ""
    echo "5. Remove the stack:"
    echo "   docker stack rm $STACK_NAME"
    echo ""
    echo "6. Access Traefik dashboard:"
    echo "   https://traefik.teloo.com"
    echo ""
}

# Main deployment flow
main() {
    check_docker
    check_swarm
    create_secrets
    create_networks
    deploy_stack
    wait_for_services
    show_status
    show_next_steps
}

# Run main function
main
