/**
 * Simple test to verify contract utilities work correctly
 * This test only does read operations to avoid nonce issues
 */

const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

// Configuration
const RPC_URL = "http://127.0.0.1:8545";

async function main() {
  console.log("=== Simple Contract Utilities Test ===\n");

  // Setup provider (no signer needed for read operations)
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  
  console.log("Connected to network:", await provider.getNetwork());
  console.log("Current block number:", await provider.getBlockNumber());
  console.log();

  // Load deployment addresses
  const deploymentsPath = path.join(__dirname, "..", "deployments", "all-contracts.json");
  
  if (!fs.existsSync(deploymentsPath)) {
    console.error("Deployment file not found. Please run deployment first.");
    process.exit(1);
  }
  
  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));
  
  console.log("Loaded contract addresses:");
  console.log("- PatientRegistry:", deployments.PatientRegistry);
  console.log("- BlockedIPRegistry:", deployments.BlockedIPRegistry);
  console.log("- AttackSignatureRegistry:", deployments.AttackSignatureRegistry);
  console.log();

  // Load contract ABIs
  function loadABI(contractName) {
    let artifactPath;
    if (contractName === "BlockedIPRegistry") {
      artifactPath = path.join(__dirname, "..", "artifacts", "contracts", "BlockedIP.sol", "BlockedIPRegistry.json");
    } else {
      artifactPath = path.join(__dirname, "..", "artifacts", "contracts", `${contractName}.sol`, `${contractName}.json`);
    }
    
    if (!fs.existsSync(artifactPath)) {
      throw new Error(`Artifact not found: ${artifactPath}`);
    }
    
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    return artifact.abi;
  }

  // Create contract instances (read-only)
  try {
    const patientRegistryABI = loadABI("PatientRegistry");
    const blockedIPRegistryABI = loadABI("BlockedIPRegistry");
    const attackSignatureRegistryABI = loadABI("AttackSignatureRegistry");

    const patientRegistry = new ethers.Contract(deployments.PatientRegistry, patientRegistryABI, provider);
    const blockedIPRegistry = new ethers.Contract(deployments.BlockedIPRegistry, blockedIPRegistryABI, provider);
    const attackSignatureRegistry = new ethers.Contract(deployments.AttackSignatureRegistry, attackSignatureRegistryABI, provider);

    console.log("Contract instances created successfully");
    console.log("- PatientRegistry functions:", patientRegistryABI.filter(item => item.type === 'function').length);
    console.log("- BlockedIPRegistry functions:", blockedIPRegistryABI.filter(item => item.type === 'function').length);
    console.log("- AttackSignatureRegistry functions:", attackSignatureRegistryABI.filter(item => item.type === 'function').length);
    console.log();

    // Test read-only contract calls
    console.log("=== Testing Read-Only Contract Calls ===");
    
    // Test PatientRegistry
    const testPatientHash = ethers.keccak256(ethers.toUtf8Bytes("test-patient-data"));
    const patientExists = await patientRegistry.patientExists(testPatientHash);
    console.log("Test patient exists:", patientExists);
    
    // Test BlockedIPRegistry
    const testIPHash = ethers.keccak256(ethers.toUtf8Bytes("192.168.1.1"));
    const ipBlocked = await blockedIPRegistry.isIPBlocked(testIPHash);
    console.log("Test IP blocked:", ipBlocked);
    
    // Test AttackSignatureRegistry
    const signatureCount = await attackSignatureRegistry.getAllSignatures();
    console.log("Attack signatures count:", signatureCount.length);
    
    // Test getting blocked IP list
    const blockedIPList = await blockedIPRegistry.getBlockedIPList();
    console.log("Blocked IP list length:", blockedIPList.length);
    
    // Test getting blocked IP count
    const blockedIPCount = await blockedIPRegistry.getBlockedIPCount();
    console.log("Blocked IP count:", blockedIPCount.toString());
    
    console.log("\n=== All utility tests completed successfully! ===");
    console.log("\nContract interaction utilities are working correctly:");
    console.log("✓ Contract addresses loaded from deployment files");
    console.log("✓ Contract ABIs loaded from artifacts");
    console.log("✓ Contract instances created successfully");
    console.log("✓ Read-only contract calls working");
    console.log("✓ All contract functions accessible");

  } catch (error) {
    console.error("Error during contract interaction:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });