import { ethers } from "hardhat";
import {
  loadContractABI,
  loadDeployedAddress,
  loadAllDeployedAddresses,
  getContractInstance,
  getAllContractInstances,
  verifyContractDeployment,
  getNetworkInfo,
  checkDeploymentsExist
} from "./contract-utils";

async function main() {
  console.log("=== Testing Contract Interaction Utilities ===\n");

  // Test 1: Check if deployments exist
  console.log("1. Checking deployment files...");
  const deploymentsExist = checkDeploymentsExist();
  console.log(`Deployments exist: ${deploymentsExist}\n`);

  if (!deploymentsExist) {
    console.error("Deployment files not found. Please run deployment first.");
    process.exit(1);
  }

  // Test 2: Get network information
  console.log("2. Getting network information...");
  const networkInfo = await getNetworkInfo();
  console.log(`Network: ${networkInfo.name} (Chain ID: ${networkInfo.chainId})`);
  console.log(`Block number: ${networkInfo.blockNumber}`);
  console.log(`Available accounts: ${networkInfo.availableAccounts}`);
  console.log(`Default account: ${networkInfo.defaultAccount}\n`);

  // Test 3: Load deployed addresses
  console.log("3. Loading deployed addresses...");
  try {
    const patientRegistryAddress = loadDeployedAddress("PatientRegistry");
    const blockedIPRegistryAddress = loadDeployedAddress("BlockedIPRegistry");
    const attackSignatureRegistryAddress = loadDeployedAddress("AttackSignatureRegistry");
    
    console.log(`PatientRegistry: ${patientRegistryAddress}`);
    console.log(`BlockedIPRegistry: ${blockedIPRegistryAddress}`);
    console.log(`AttackSignatureRegistry: ${attackSignatureRegistryAddress}\n`);
  } catch (error) {
    console.error("Error loading addresses:", error);
    process.exit(1);
  }

  // Test 4: Load all addresses at once
  console.log("4. Loading all addresses...");
  try {
    const allAddresses = loadAllDeployedAddresses();
    console.log("All deployed contracts:", allAddresses);
    console.log();
  } catch (error) {
    console.error("Error loading all addresses:", error);
    process.exit(1);
  }

  // Test 5: Load contract ABIs
  console.log("5. Loading contract ABIs...");
  try {
    const patientRegistryABI = loadContractABI("PatientRegistry");
    const blockedIPRegistryABI = loadContractABI("BlockedIPRegistry");
    const attackSignatureRegistryABI = loadContractABI("AttackSignatureRegistry");
    
    console.log(`PatientRegistry ABI functions: ${patientRegistryABI.filter((item: any) => item.type === 'function').length}`);
    console.log(`BlockedIPRegistry ABI functions: ${blockedIPRegistryABI.filter((item: any) => item.type === 'function').length}`);
    console.log(`AttackSignatureRegistry ABI functions: ${attackSignatureRegistryABI.filter((item: any) => item.type === 'function').length}\n`);
  } catch (error) {
    console.error("Error loading ABIs:", error);
    process.exit(1);
  }

  // Test 6: Get contract instances
  console.log("6. Creating contract instances...");
  try {
    const patientRegistry = await getContractInstance("PatientRegistry");
    const blockedIPRegistry = await getContractInstance("BlockedIPRegistry");
    const attackSignatureRegistry = await getContractInstance("AttackSignatureRegistry");
    
    console.log(`PatientRegistry instance created: ${await patientRegistry.getAddress()}`);
    console.log(`BlockedIPRegistry instance created: ${await blockedIPRegistry.getAddress()}`);
    console.log(`AttackSignatureRegistry instance created: ${await attackSignatureRegistry.getAddress()}\n`);
  } catch (error) {
    console.error("Error creating contract instances:", error);
    process.exit(1);
  }

  // Test 7: Get all contract instances at once
  console.log("7. Creating all contract instances...");
  try {
    const contracts = await getAllContractInstances();
    console.log(`All contracts loaded:`);
    console.log(`- PatientRegistry: ${await contracts.patientRegistry.getAddress()}`);
    console.log(`- BlockedIPRegistry: ${await contracts.blockedIPRegistry.getAddress()}`);
    console.log(`- AttackSignatureRegistry: ${await contracts.attackSignatureRegistry.getAddress()}\n`);
  } catch (error) {
    console.error("Error creating all contract instances:", error);
    process.exit(1);
  }

  // Test 8: Verify contract deployments
  console.log("8. Verifying contract deployments...");
  const contracts = ["PatientRegistry", "BlockedIPRegistry", "AttackSignatureRegistry"];
  
  for (const contractName of contracts) {
    const isValid = await verifyContractDeployment(contractName);
    console.log(`${contractName}: ${isValid ? "✓ Valid" : "✗ Invalid"}`);
  }
  console.log();

  // Test 9: Test actual contract calls
  console.log("9. Testing contract function calls...");
  try {
    const { patientRegistry, blockedIPRegistry, attackSignatureRegistry } = await getAllContractInstances();
    
    // Test PatientRegistry
    const testPatientHash = ethers.keccak256(ethers.toUtf8Bytes("test-patient-123"));
    const isRegistered = await patientRegistry.patientExists(testPatientHash);
    console.log(`Test patient exists: ${isRegistered}`);
    
    // Test BlockedIPRegistry
    const testIPHash = ethers.keccak256(ethers.toUtf8Bytes("192.168.1.1"));
    const isBlocked = await blockedIPRegistry.isIPBlocked(testIPHash);
    console.log(`Test IP blocked: ${isBlocked}`);
    
    // Test AttackSignatureRegistry
    const signatures = await attackSignatureRegistry.getAllSignatures();
    console.log(`Attack signatures count: ${signatures.length}`);
    
  } catch (error) {
    console.error("Error testing contract calls:", error);
    process.exit(1);
  }

  console.log("\n=== All tests completed successfully! ===");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });