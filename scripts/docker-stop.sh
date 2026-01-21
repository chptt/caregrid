#!/bin/bash

# Script to gracefully stop MediChain Docker environment

set -e

echo "🛑 Stopping MediChain Healthcare Security System"
echo "=============================================="

# Stop all services
echo "⏹️  Stopping all services..."
docker-compose down

# Optional: Remove volumes (uncomment if you want to reset data)
# echo "🗑️  Removing volumes..."
# docker-compose down -v

# Optional: Remove images (uncomment if you want to clean up completely)
# echo "🧹 Removing images..."
# docker-compose down --rmi all

echo "✅ MediChain system stopped successfully!"
echo ""
echo "📋 To restart the system:"
echo "  ./scripts/docker-start.sh"
echo ""
echo "📋 To completely reset (remove all data):"
echo "  docker-compose down -v"