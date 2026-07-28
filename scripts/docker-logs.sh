#!/bin/bash

# Script to view logs from MediChain Docker services

set -e

# Function to display usage
show_usage() {
    echo "Usage: $0 [service_name]"
    echo ""
    echo "Available services:"
    echo "  • django     - Django application logs"
    echo "  • redis      - Redis cache logs"
    echo "  • hardhat    - Blockchain node logs"
    echo "  • migrate    - Database migration logs"
    echo "  • deploy-contracts - Contract deployment logs"
    echo "  • all        - All services logs (default)"
    echo ""
    echo "Examples:"
    echo "  $0 django    - View Django logs"
    echo "  $0 all       - View all logs"
    echo "  $0           - View all logs (default)"
}

# Get service name from argument or default to 'all'
SERVICE=${1:-all}

case $SERVICE in
    "django"|"redis"|"hardhat"|"migrate"|"deploy-contracts")
        echo "📋 Viewing logs for $SERVICE..."
        docker-compose logs -f $SERVICE
        ;;
    "all")
        echo "📋 Viewing logs for all services..."
        docker-compose logs -f
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo ""
        show_usage
        exit 1
        ;;
esac