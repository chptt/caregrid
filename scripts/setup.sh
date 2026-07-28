#!/bin/bash

# Comprehensive setup script for MediChain project

echo "=== MediChain Project Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if Redis is installed
echo ""
echo "Checking Redis installation..."
if command -v redis-server &> /dev/null; then
    redis_version=$(redis-server --version | awk '{print $3}')
    echo "Redis version: $redis_version"
else
    echo "Warning: Redis is not installed!"
    echo "Please install Redis:"
    echo "  - Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  - macOS: brew install redis"
    echo "  - Windows: Download from https://redis.io/download"
fi

# Check if Node.js is installed
echo ""
echo "Checking Node.js installation..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "Node.js version: $node_version"
else
    echo "Error: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✓ Python dependencies installed successfully"
    else
        echo "✗ Failed to install Python dependencies"
        exit 1
    fi
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Install blockchain dependencies
echo ""
echo "Installing blockchain dependencies..."
cd caregrid_chain
if [ -f "package.json" ]; then
    npm install
    if [ $? -eq 0 ]; then
        echo "✓ Blockchain dependencies installed successfully"
    else
        echo "✗ Failed to install blockchain dependencies"
        exit 1
    fi
else
    echo "Error: package.json not found in caregrid_chain!"
    exit 1
fi
cd ..

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p caregrid_chain/deployments
echo "✓ Directories created"

# Run Django migrations
echo ""
echo "Running Django migrations..."
python3 manage.py makemigrations
python3 manage.py migrate
if [ $? -eq 0 ]; then
    echo "✓ Database migrations completed"
else
    echo "✗ Database migrations failed"
    exit 1
fi

# Check if Redis is running
echo ""
echo "Checking Redis status..."
if redis-cli ping &> /dev/null; then
    echo "✓ Redis is running"
else
    echo "Warning: Redis is not running!"
    echo "Start Redis with: redis-server"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start Redis (if not running): redis-server"
echo "2. Start blockchain: ./scripts/start-blockchain.sh"
echo "3. Update contract addresses: python3 scripts/update_contract_addresses.py"
echo "4. Start Django server: python3 manage.py runserver"
echo ""
