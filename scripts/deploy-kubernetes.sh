#!/bin/bash

# Kubernetes Deployment Script for TeLOO V3
# This script deploys the TeLOO application to a Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-teloo-production}"
REGISTRY="${REGISTRY:-ghcr.io/your-org}"
IMAGE_VERSION="${IMAGE_VERSION:-latest}"
KUBECTL="${KUBECTL:-kubectl}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TeLOO V3 Kubernetes Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Namespace: $NAMESPACE"
echo "Registry: $REGISTRY"
echo "Image Version: $IMAGE_VERSION"
echo ""

# Function to check if kubectl is installed
check_kubectl() {
    if ! command -v $KUBECTL &> /dev/null; then
        echo -e "${RED}Error: kubectl is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ kubectl is installed${NC}"
}

# Function to check cluster connection
check_cluster() {
    if ! $KUBECTL cluster-info &> /dev/null; then
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
}

# Function to create namespace
create_namespace() {
    echo ""
    echo -e "${YELLOW}Creating namespace...${NC}"
    $KUBECTL apply -f kubernetes/namespace.yaml
    echo -e "${GREEN}✓ Namespace created${NC}"
}

# Function to create secrets
create_secrets() {
    echo ""
    echo -e "${YELLOW}Creating secrets...${NC}"
    
    if $KUBECTL get secret teloo-secrets -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}Warning: Secrets already exist. Skipping creation.${NC}"
        echo -e "${YELLOW}To update secrets, delete them first: kubectl delete secret teloo-secrets -n $NAMESPACE${NC}"
    else
        # Check if secrets file exists with actual values
        if [ -f "kubernetes/secrets.yaml" ]; then
            if grep -q "REPLACE_WITH_" kubernetes/secrets.yaml; then
                echo -e "${RED}Error: secrets.yaml contains placeholder values${NC}"
                echo -e "${YELLOW}Please update kubernetes/secrets.yaml with actual values or use:${NC}"
                echo -e "${YELLOW}  ./scripts/generate-secrets.sh kubernetes${NC}"
                exit 1
            fi
            $KUBECTL apply -f kubernetes/secrets.yaml
            echo -e "${GREEN}✓ Secrets created${NC}"
        else
            echo -e "${RED}Error: kubernetes/secrets.yaml not found${NC}"
            exit 1
        fi
    fi
}

# Function to create configmap
create_configmap() {
    echo ""
    echo -e "${YELLOW}Creating configmap...${NC}"
    $KUBECTL apply -f kubernetes/configmap.yaml
    echo -e "${GREEN}✓ ConfigMap created${NC}"
}

# Function to deploy stateful services
deploy_stateful() {
    echo ""
    echo -e "${YELLOW}Deploying stateful services (PostgreSQL, Redis, MinIO)...${NC}"
    $KUBECTL apply -f kubernetes/statefulsets.yaml
    
    echo -e "${YELLOW}Waiting for stateful services to be ready...${NC}"
    $KUBECTL wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
    $KUBECTL wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s
    $KUBECTL wait --for=condition=ready pod -l app=minio -n $NAMESPACE --timeout=300s
    
    echo -e "${GREEN}✓ Stateful services deployed${NC}"
}

# Function to deploy application services
deploy_services() {
    echo ""
    echo -e "${YELLOW}Deploying application services...${NC}"
    
    # Update image tags in deployment files
    for file in kubernetes/*-deployment.yaml; do
        if [ -f "$file" ]; then
            sed -i.bak "s|REGISTRY|$REGISTRY|g" "$file"
            sed -i.bak "s|IMAGE_TAG|$IMAGE_VERSION|g" "$file"
            $KUBECTL apply -f "$file"
            rm "${file}.bak"
        fi
    done
    
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    $KUBECTL wait --for=condition=available deployment --all -n $NAMESPACE --timeout=600s
    
    echo -e "${GREEN}✓ Application services deployed${NC}"
}

# Function to deploy ingress
deploy_ingress() {
    echo ""
    echo -e "${YELLOW}Deploying ingress...${NC}"
    $KUBECTL apply -f kubernetes/ingress.yaml
    echo -e "${GREEN}✓ Ingress deployed${NC}"
}

# Function to setup backup cronjobs
setup_backups() {
    echo ""
    echo -e "${YELLOW}Setting up backup cronjobs...${NC}"
    $KUBECTL apply -f kubernetes/backup-cronjob.yaml
    echo -e "${GREEN}✓ Backup cronjobs configured${NC}"
}

# Function to display deployment status
show_status() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Status${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}Pods:${NC}"
    $KUBECTL get pods -n $NAMESPACE
    echo ""
    
    echo -e "${YELLOW}Services:${NC}"
    $KUBECTL get services -n $NAMESPACE
    echo ""
    
    echo -e "${YELLOW}Ingress:${NC}"
    $KUBECTL get ingress -n $NAMESPACE
    echo ""
    
    echo -e "${YELLOW}HPA (Horizontal Pod Autoscalers):${NC}"
    $KUBECTL get hpa -n $NAMESPACE
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
    echo "1. Verify all pods are running:"
    echo "   kubectl get pods -n $NAMESPACE"
    echo ""
    echo "2. Check service logs:"
    echo "   kubectl logs -f deployment/core-api -n $NAMESPACE"
    echo ""
    echo "3. Access the application:"
    echo "   kubectl get ingress -n $NAMESPACE"
    echo ""
    echo "4. Monitor with:"
    echo "   kubectl top pods -n $NAMESPACE"
    echo ""
    echo "5. Scale services:"
    echo "   kubectl scale deployment/core-api --replicas=5 -n $NAMESPACE"
    echo ""
}

# Main deployment flow
main() {
    check_kubectl
    check_cluster
    create_namespace
    create_secrets
    create_configmap
    deploy_stateful
    deploy_services
    deploy_ingress
    setup_backups
    show_status
    show_next_steps
}

# Run main function
main
