/**
 * Standalone Node.js script to test contract interactions
 * This demonstrates how to use the contracts from a regular Node.js application
 */

const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

// Configuration
const RPC_URL = "http://127.0.0.1:8545";
const PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"; // First Hardhat account

async function main() {
  console.log("=== Standalone Contract Interaction Test ===\n");

  // Setup provider and signer
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const signer = new ethers.Wallet(PRIVATE_KEY, provider);
  
  console.log("Connected to network:", await provider.getNetwork());
  console.log("Using account:", signer.address);
  console.log("Account balance:", ethers.formatEther(await provider.getBalance(signer.address)), "ETH\n");

  // Load deployment addresses
  const deploymentsPath = path.join(__dirname, "..", "deployments", "all-contracts.json");
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
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    return artifact.abi;
  }

  // Create contract instances
  const patientRegistryABI = loadABI("PatientRegistry");
  const blockedIPRegistryABI = loadABI("BlockedIPRegistry");
  const attackSignatureRegistryABI = loadABI("AttackSignatureRegistry");

  const patientRegistry = new ethers.Contract(deployments.PatientRegistry, patientRegistryABI, signer);
  const blockedIPRegistry = new ethers.Contract(deployments.BlockedIPRegistry, blockedIPRegistryABI, signer);
  const attackSignatureRegistry = new ethers.Contract(deployments.AttackSignatureRegistry, attackSignatureRegistryABI, signer);

  console.log("Contract instances created successfully\n");

  // Test contract interactions
  console.log("=== Testing Contract Interactions ===\n");

  try {
    // Test 1: PatientRegistry
    console.log("1. Testing PatientRegistry...");
    const testPatientData = `Jane Smith|1985-05-15|jane@example.com|${Date.now()}`; // Add timestamp for uniqueness
    const patientHash = ethers.keccak256(ethers.toUtf8Bytes(testPatientData));
    
    console.log("Patient hash:", patientHash);
    
    // Check if patient exists (should be false initially)
    let exists = await patientRegistry.patientExists(patientHash);
    console.log("Patient exists (before registration):", exists);
    
    // Register patient
    console.log("Registering patient...");
    const tx1 = await patientRegistry.registerPatient(patientHash);
    await tx1.wait();
    console.log("Patient registered! Transaction:", tx1.hash);
    
    // Check if patient exists now (should be true)
    exists = await patientRegistry.patientExists(patientHash);
    console.log("Patient exists (after registration):", exists);
    console.log();

    // Test 2: BlockedIPRegistry
    console.log("2. Testing BlockedIPRegistry...");
    const testIP = `192.168.1.${Math.floor(Math.random() * 255)}`; // Random IP for uniqueness
    const ipHash = ethers.keccak256(ethers.toUtf8Bytes(testIP));
    
    console.log("IP hash:", ipHash);
    
    // Check if IP is blocked (should be false initially)
    let blocked = await blockedIPRegistry.isIPBlocked(ipHash);
    console.log("IP blocked (before blocking):", blocked);
    
    // Block IP for 1 hour (3600 seconds)
    console.log("Blocking IP...");
    const duration = 3600; // 1 hour in seconds
    const tx2 = await blockedIPRegistry.blockIP(ipHash, duration, "Test block", false); // false = automatic block
    await tx2.wait();
    console.log("IP blocked! Transaction:", tx2.hash);
    
    // Check if IP is blocked now (should be true)
    blocked = await blockedIPRegistry.isIPBlocked(ipHash);
    console.log("IP blocked (after blocking):", blocked);
    console.log();

    // Test 3: AttackSignatureRegistry
    console.log("3. Testing AttackSignatureRegistry...");
    
    // Check initial signature count
    let signatures = await attackSignatureRegistry.getAllSignatures();
    console.log("Initial signature count:", signatures.length);
    
    // Add an attack signature
    const attackPattern = JSON.stringify({
      endpoints: ["/api/login", "/api/admin"],
      rate: 100,
      userAgent: "bot-scanner"
    });
    
    console.log("Adding attack signature...");
    const tx3 = await attackSignatureRegistry.addSignature(attackPattern, 8); // Severity 8
    await tx3.wait();
    console.log("Attack signature added! Transaction:", tx3.hash);
    
    // Check signature count after adding
    signatures = await attackSignatureRegistry.getAllSignatures();
    console.log("Signature count after adding:", signatures.length);
    
    if (signatures.length > 0) {
      const firstSignature = await attackSignatureRegistry.getSignature(signatures[0]);
      console.log("First signature pattern:", firstSignature[1]); // pattern is at index 1
      console.log("First signature severity:", firstSignature[4].toString()); // severity is at index 4
    }
    console.log();

    console.log("=== All tests completed successfully! ===");

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