#!/bin/bash

# Virtual Substation Deployment Script
# Automated deployment for production environments

set -e

echo "🚀 Virtual Substation Deployment Script"
echo "======================================="

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Build containers
build_containers() {
    echo "🔨 Building containers..."
    docker-compose build --no-cache
    echo "✅ Containers built successfully"
}

# Deploy system
deploy_system() {
    echo "🚀 Deploying Virtual Substation..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check service health
    check_services
}

# Check service health
check_services() {
    echo "🔍 Checking service health..."
    
    services=("protection_relay_ied" "circuit_breaker_ied" "hmi_scada" "substation_web_ui")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            echo "✅ $service is running"
        else
            echo "❌ $service failed to start"
            docker-compose logs "$service"
            exit 1
        fi
    done
    
    echo "✅ All services are healthy"
}

# Display access information
show_access_info() {
    echo ""
    echo "🎯 Virtual Substation Access Information"
    echo "======================================="
    echo "Web Interface:     http://localhost:3000"
    echo "Protection Relay:  http://localhost:8082"
    echo "Circuit Breaker:   http://localhost:8081"
    echo "HMI/SCADA:        http://localhost:8080"
    echo "MMS Server:       localhost:102"
    echo ""
    echo "GUI Panels: Run 'make gui' to launch training interface"
    echo ""
}

# Main deployment flow
main() {
    cd "$(dirname "$0")"/.. || exit 1
    check_prerequisites
    build_containers
    deploy_system
    show_access_info
    
    echo "🎉 Virtual Substation deployed successfully!"
    echo "📚 See docs/INSTALL.md for usage instructions"
}

# Handle script arguments
case "${1:-deploy}" in
    "build")
        check_prerequisites
        build_containers
        ;;
    "deploy")
        main
        ;;
    "check")
        check_services
        ;;
    "info")
        show_access_info
        ;;
    *)
        echo "Usage: $0 [build|deploy|check|info]"
        echo "  build  - Build containers only"
        echo "  deploy - Full deployment (default)"
        echo "  check  - Check service health"
        echo "  info   - Show access information"
        exit 1
        ;;
esac