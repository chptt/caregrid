#!/bin/bash

# Script to start local Hardhat blockchain and deploy contracts

echo "=== Starting MediChain Blockchain Setup ==="

# Navigate to blockchain directory
cd caregrid_chain

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing blockchain dependencies..."
    npm install
fi

# Start Hardhat node in background
echo "Starting Hardhat local blockchain..."
npx hardhat node > ../logs/hardhat.log 2>&1 &
HARDHAT_PID=$!
echo "Hardhat node started with PID: $HARDHAT_PID"

# Wait for Hardhat to be ready
echo "Waiting for Hardhat to be ready..."
sleep 5

# Deploy contracts
echo "Deploying smart contracts..."
npx hardhat run scripts/deploy-all.ts --network localhost

if [ $? -eq 0 ]; then
    echo "✓ Contracts deployed successfully!"
    echo "✓ Hardhat node is running on http://127.0.0.1:8545"
    echo "✓ Deployment info saved to caregrid_chain/deployments/"
    echo ""
    echo "To stop the blockchain, run: kill $HARDHAT_PID"
    echo "Or use: pkill -f 'hardhat node'"
else
    echo "✗ Contract deployment failed!"
    kill $HARDHAT_PID
    exit 1
fi

cd ..
