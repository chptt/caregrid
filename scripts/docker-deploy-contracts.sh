#!/bin/bash

# Script to deploy smart contracts in Docker environment
# This script waits for Hardhat node to be ready and then deploys contracts

set -e

echo "🚀 Starting contract deployment..."

# Wait for Hardhat node to be ready
echo "⏳ Waiting for Hardhat node to be ready..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s -f http://hardhat:8545 > /dev/null 2>&1; then
        echo "✅ Hardhat node is ready!"
        break
    fi
    echo "⏳ Waiting for Hardhat node... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for Hardhat node"
    exit 1
fi

# Change to blockchain directory
cd /app

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Compile contracts
echo "🔨 Compiling smart contracts..."
npx hardhat compile

# Deploy contracts
echo "🚀 Deploying contracts to local network..."
npx hardhat run scripts/deploy-all.ts --network localhost

# Verify deployment files exist
if [ -f "deployments/PatientRegistry.json" ] && [ -f "deployments/BlockedIPRegistry.json" ] && [ -f "deployments/AttackSignatureRegistry.json" ]; then
    echo "✅ All contracts deployed successfully!"
    echo "📄 Deployment files created:"
    ls -la deployments/*.json
else
    echo "❌ Contract deployment failed - missing deployment files"
    exit 1
fi

echo "🎉 Contract deployment completed!"