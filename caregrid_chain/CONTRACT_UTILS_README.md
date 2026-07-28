# Contract Interaction Utilities

This directory contains utilities for interacting with the deployed smart contracts in the MediChain system.

## Overview

The contract utilities provide a simple interface for:
- Loading contract ABIs from artifacts
- Reading deployed contract addresses
- Creating contract instances
- Verifying contract deployments
- Testing contract interactions

## Files

- `scripts/contract-utils.ts` - Main utility functions (TypeScript/Hardhat)
- `scripts/test-contracts.ts` - Comprehensive test suite using Hardhat
- `scripts/simple-test.js` - Simple Node.js test for basic functionality
- `scripts/standalone-test.js` - Full interaction test (may have nonce issues)
- `deployments/` - Directory containing deployed contract addresses

## Quick Start

### 1. Start Local Blockchain

```bash
npm run node
```

### 2. Deploy Contracts

```bash
npm run deploy
```

### 3. Test Contract Utilities

```bash
# Test using Hardhat environment
npm run test-contracts

# Test using standalone Node.js
npm run test-utils
```

## Usage Examples

### Loading Contract Addresses

```javascript
const fs = require("fs");
const path = require("path");

// Load all contract addresses
const deploymentsPath = path.join(__dirname, "deployments", "all-contracts.json");
const deployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));

console.log("PatientRegistry:", deployments.PatientRegistry);
console.log("BlockedIPRegistry:", deployments.BlockedIPRegistry);
console.log("AttackSignatureRegistry:", deployments.AttackSignatureRegistry);
```

### Creating Contract Instances

```javascript
const { ethers } = require("ethers");

// Setup provider and signer
const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
const signer = new ethers.Wallet(PRIVATE_KEY, provider);

// Load ABI (handle special case for BlockedIPRegistry)
function loadABI(contractName) {
  let artifactPath;
  if (contractName === "BlockedIPRegistry") {
    artifactPath = path.join(__dirname, "artifacts", "contracts", "BlockedIP.sol", "BlockedIPRegistry.json");
  } else {
    artifactPath = path.join(__dirname, "artifacts", "contracts", `${contractName}.sol`, `${contractName}.json`);
  }
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  return artifact.abi;
}

// Create contract instance
const patientRegistryABI = loadABI("PatientRegistry");
const patientRegistry = new ethers.Contract(
  deployments.PatientRegistry, 
  patientRegistryABI, 
  signer
);
```

### Using Hardhat Utilities (TypeScript)

```typescript
import {
  loadContractABI,
  loadDeployedAddress,
  getContractInstance,
  getAllContractInstances,
  verifyContractDeployment
} from "./scripts/contract-utils";

// Load individual contract
const patientRegistry = await getContractInstance("PatientRegistry");

// Load all contracts
const { patientRegistry, blockedIPRegistry, attackSignatureRegistry } = 
  await getAllContractInstances();

// Verify deployment
const isValid = await verifyContractDeployment("PatientRegistry");
```

## Contract Functions

### PatientRegistry
- `registerPatient(bytes32 patientIdHash)` - Register a new patient
- `patientExists(bytes32 patientIdHash)` - Check if patient is registered
- `isPatientRegistered(bytes32 patientIdHash)` - Alias for patientExists
- `getPatient(bytes32 patientIdHash)` - Get patient details

### BlockedIPRegistry
- `blockIP(bytes32 ipHash, uint256 duration, string reason, bool manual)` - Block an IP
- `unblockIP(bytes32 ipHash)` - Unblock an IP
- `isIPBlocked(bytes32 ipHash)` - Check if IP is blocked
- `getBlockEntry(bytes32 ipHash)` - Get block details
- `cleanupExpiredBlocks()` - Remove expired blocks
- `getBlockedIPList()` - Get all blocked IP hashes
- `getBlockedIPCount()` - Get count of blocked IPs

### AttackSignatureRegistry
- `addSignature(string pattern, uint256 severity)` - Add attack signature
- `getSignature(bytes32 signatureHash)` - Get signature details
- `getAllSignatures()` - Get all signature hashes

## Network Configuration

The utilities are configured to work with:
- **Local Development**: Hardhat node on `http://127.0.0.1:8545`
- **Testnet**: Sepolia (configured in hardhat.config.ts)

## Deployment Files

After deployment, the following files are created in `deployments/`:
- `PatientRegistry.json` - Individual contract deployment info
- `BlockedIPRegistry.json` - Individual contract deployment info  
- `AttackSignatureRegistry.json` - Individual contract deployment info
- `all-contracts.json` - Combined deployment info

Each file contains:
```json
{
  "address": "0x...",
  "deployer": "0x...",
  "timestamp": "2026-01-17T...",
  "network": "localhost"
}
```

## Error Handling

Common issues and solutions:

### Contract Artifact Not Found
- Ensure contracts are compiled: `npm run compile`
- Check that the contract name matches the file name
- Note: BlockedIPRegistry is in `BlockedIP.sol`

### Deployment Files Missing
- Run deployment first: `npm run deploy`
- Check that Hardhat node is running: `npm run node`

### Nonce Issues
- Restart Hardhat node for clean state
- Use read-only operations when possible
- Wait for transaction confirmations

### Connection Issues
- Ensure Hardhat node is running on port 8545
- Check network configuration in hardhat.config.ts

## Integration with Django

These utilities can be used from the Django backend:

```python
# In Django settings or service
import subprocess
import json

def get_contract_addresses():
    """Load contract addresses for Django integration"""
    result = subprocess.run([
        'node', 
        'caregrid_chain/scripts/simple-test.js'
    ], capture_output=True, text=True)
    
    # Parse deployment file directly
    with open('caregrid_chain/deployments/all-contracts.json') as f:
        return json.load(f)
```

## Testing

Run the test suite to verify everything works:

```bash
# Full test with Hardhat environment
npm run test-contracts

# Simple read-only test
npm run test-utils

# Run actual Hardhat tests
npm test
```

## Troubleshooting

1. **Contracts not deploying**: Check that Hardhat node is running
2. **ABI loading errors**: Ensure contracts are compiled
3. **Address loading errors**: Ensure deployment completed successfully
4. **Transaction failures**: Check account has sufficient ETH
5. **Nonce errors**: Restart Hardhat node for clean state

For more help, check the test files for working examples.