#!/bin/bash

# Main startup script for MediChain Docker environment
# This script orchestrates the startup of all services

set -e

echo "🏥 Starting MediChain Healthcare Security System"
echo "=============================================="

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Checking health of $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "healthy"; then
            echo "✅ $service_name is healthy!"
            return 0
        fi
        
        echo "⏳ Waiting for $service_name to be healthy... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become healthy"
    return 1
}

# Function to wait for service completion
wait_for_completion() {
    local service_name=$1
    local max_attempts=60
    local attempt=1
    
    echo "⏳ Waiting for $service_name to complete..."
    
    while [ $attempt -le $max_attempts ]; do
        local status=$(docker-compose ps -q $service_name | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        
        if [ "$status" = "exited" ]; then
            local exit_code=$(docker-compose ps -q $service_name | xargs docker inspect --format='{{.State.ExitCode}}' 2>/dev/null || echo "1")
            if [ "$exit_code" = "0" ]; then
                echo "✅ $service_name completed successfully!"
                return 0
            else
                echo "❌ $service_name failed with exit code $exit_code"
                return 1
            fi
        fi
        
        echo "⏳ Waiting for $service_name to complete... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name did not complete in time"
    return 1
}

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down -v

# Start infrastructure services first
echo "🚀 Starting infrastructure services..."
docker-compose up -d redis hardhat

# Wait for infrastructure to be healthy
check_service_health "redis"
check_service_health "hardhat"

# Deploy contracts
echo "📜 Deploying smart contracts..."
docker-compose up deploy-contracts
wait_for_completion "deploy-contracts"

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose up migrate
wait_for_completion "migrate"

# Start Django application
echo "🌐 Starting Django application..."
docker-compose up -d django

# Wait for Django to be healthy
check_service_health "django"

# Display service status
echo ""
echo "🎉 MediChain system started successfully!"
echo "=============================================="
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access Points:"
echo "  • Django Admin: http://localhost:8000/admin/"
echo "  • API Endpoints: http://localhost:8000/api/"
echo "  • Security Dashboard: http://localhost:8000/api/security/dashboard/"
echo "  • Hardhat Node: http://localhost:8545"
echo "  • Redis: localhost:6379"
echo ""
echo "👤 Default Admin Credentials:"
echo "  • Username: admin"
echo "  • Password: admin123"
echo ""
echo "📋 Useful Commands:"
echo "  • View logs: docker-compose logs -f [service_name]"
echo "  • Stop system: docker-compose down"
echo "  • Restart system: docker-compose restart"
echo "  • View contract addresses: cat caregrid_chain/deployments/all-contracts.json"
echo ""
echo "✅ System is ready for use!"