import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Utility functions for interacting with deployed contracts
 */

export interface DeploymentInfo {
  address: string;
  deployer: string;
  timestamp: string;
  network: string;
}

export interface AllDeployments {
  PatientRegistry: string;
  BlockedIPRegistry: string;
  AttackSignatureRegistry: string;
  deployer: string;
  timestamp: string;
  network: string;
}

/**
 * Load contract ABI from artifacts
 */
export function loadContractABI(contractName: string): any {
  let artifactPath: string;
  
  // Handle special case for BlockedIPRegistry which is in BlockedIP.sol
  if (contractName === "BlockedIPRegistry") {
    artifactPath = path.join(
      __dirname,
      "..",
      "artifacts",
      "contracts",
      "BlockedIP.sol",
      "BlockedIPRegistry.json"
    );
  } else {
    artifactPath = path.join(
      __dirname,
      "..",
      "artifacts",
      "contracts",
      `${contractName}.sol`,
      `${contractName}.json`
    );
  }
  
  if (!fs.existsSync(artifactPath)) {
    throw new Error(`Contract artifact not found: ${artifactPath}`);
  }
  
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  return artifact.abi;
}

/**
 * Load deployed contract address from deployment file
 */
export function loadDeployedAddress(contractName: string): string {
  const deploymentPath = path.join(
    __dirname,
    "..",
    "deployments",
    `${contractName}.json`
  );
  
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}`);
  }
  
  const deployment: DeploymentInfo = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  return deployment.address;
}

/**
 * Load all deployed contract addresses
 */
export function loadAllDeployedAddresses(): AllDeployments {
  const deploymentPath = path.join(
    __dirname,
    "..",
    "deployments",
    "all-contracts.json"
  );
  
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`All contracts deployment file not found: ${deploymentPath}`);
  }
  
  return JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
}

/**
 * Get contract instance for a deployed contract
 */
export async function getContractInstance(contractName: string, signerIndex: number = 0) {
  const address = loadDeployedAddress(contractName);
  const abi = loadContractABI(contractName);
  const signers = await ethers.getSigners();
  
  if (signerIndex >= signers.length) {
    throw new Error(`Signer index ${signerIndex} out of range. Available signers: ${signers.length}`);
  }
  
  return new ethers.Contract(address, abi, signers[signerIndex]);
}

/**
 * Get all contract instances
 */
export async function getAllContractInstances(signerIndex: number = 0) {
  const [patientRegistry, blockedIPRegistry, attackSignatureRegistry] = await Promise.all([
    getContractInstance("PatientRegistry", signerIndex),
    getContractInstance("BlockedIPRegistry", signerIndex),
    getContractInstance("AttackSignatureRegistry", signerIndex)
  ]);
  
  return {
    patientRegistry,
    blockedIPRegistry,
    attackSignatureRegistry
  };
}

/**
 * Verify contract deployment by calling a read-only function
 */
export async function verifyContractDeployment(contractName: string): Promise<boolean> {
  try {
    const contract = await getContractInstance(contractName);
    
    // Try to call a simple read function to verify the contract is deployed and working
    switch (contractName) {
      case "PatientRegistry":
        // Call a view function that should always work
        await contract.patientExists("0x0000000000000000000000000000000000000000000000000000000000000000");
        break;
      case "BlockedIPRegistry":
        await contract.isIPBlocked("0x0000000000000000000000000000000000000000000000000000000000000000");
        break;
      case "AttackSignatureRegistry":
        await contract.getAllSignatures();
        break;
      default:
        throw new Error(`Unknown contract: ${contractName}`);
    }
    
    return true;
  } catch (error) {
    console.error(`Contract verification failed for ${contractName}:`, error);
    return false;
  }
}

/**
 * Get network information
 */
export async function getNetworkInfo() {
  const network = await ethers.provider.getNetwork();
  const blockNumber = await ethers.provider.getBlockNumber();
  const signers = await ethers.getSigners();
  
  return {
    name: network.name,
    chainId: network.chainId.toString(),
    blockNumber,
    availableAccounts: signers.length,
    defaultAccount: signers[0]?.address
  };
}

/**
 * Check if deployments exist and are valid
 */
export function checkDeploymentsExist(): boolean {
  const requiredFiles = [
    "PatientRegistry.json",
    "BlockedIPRegistry.json", 
    "AttackSignatureRegistry.json",
    "all-contracts.json"
  ];
  
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  
  for (const file of requiredFiles) {
    const filePath = path.join(deploymentsDir, file);
    if (!fs.existsSync(filePath)) {
      console.error(`Missing deployment file: ${file}`);
      return false;
    }
  }
  
  return true;
}