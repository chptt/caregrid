import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("Starting deployment of all contracts...");

  // Get the deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  // Deploy PatientRegistry
  console.log("\n1. Deploying PatientRegistry...");
  const PatientRegistry = await ethers.getContractFactory("PatientRegistry");
  const patientRegistry = await PatientRegistry.deploy();
  await patientRegistry.waitForDeployment();
  const patientRegistryAddress = await patientRegistry.getAddress();
  console.log("PatientRegistry deployed to:", patientRegistryAddress);

  // Save PatientRegistry deployment info
  fs.writeFileSync(
    path.join(deploymentsDir, "PatientRegistry.json"),
    JSON.stringify({
      address: patientRegistryAddress,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      network: (await ethers.provider.getNetwork()).name,
    }, null, 2)
  );

  // Deploy BlockedIPRegistry
  console.log("\n2. Deploying BlockedIPRegistry...");
  const BlockedIPRegistry = await ethers.getContractFactory("BlockedIPRegistry");
  const blockedIPRegistry = await BlockedIPRegistry.deploy();
  await blockedIPRegistry.waitForDeployment();
  const blockedIPRegistryAddress = await blockedIPRegistry.getAddress();
  console.log("BlockedIPRegistry deployed to:", blockedIPRegistryAddress);

  // Save BlockedIPRegistry deployment info
  fs.writeFileSync(
    path.join(deploymentsDir, "BlockedIPRegistry.json"),
    JSON.stringify({
      address: blockedIPRegistryAddress,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      network: (await ethers.provider.getNetwork()).name,
    }, null, 2)
  );

  // Deploy AttackSignatureRegistry
  console.log("\n3. Deploying AttackSignatureRegistry...");
  const AttackSignatureRegistry = await ethers.getContractFactory("AttackSignatureRegistry");
  const attackSignatureRegistry = await AttackSignatureRegistry.deploy();
  await attackSignatureRegistry.waitForDeployment();
  const attackSignatureRegistryAddress = await attackSignatureRegistry.getAddress();
  console.log("AttackSignatureRegistry deployed to:", attackSignatureRegistryAddress);

  // Save AttackSignatureRegistry deployment info
  fs.writeFileSync(
    path.join(deploymentsDir, "AttackSignatureRegistry.json"),
    JSON.stringify({
      address: attackSignatureRegistryAddress,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      network: (await ethers.provider.getNetwork()).name,
    }, null, 2)
  );

  // Create a combined deployment file
  const allDeployments = {
    PatientRegistry: patientRegistryAddress,
    BlockedIPRegistry: blockedIPRegistryAddress,
    AttackSignatureRegistry: attackSignatureRegistryAddress,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    network: (await ethers.provider.getNetwork()).name,
  };

  fs.writeFileSync(
    path.join(deploymentsDir, "all-contracts.json"),
    JSON.stringify(allDeployments, null, 2)
  );

  console.log("\n=== Deployment Summary ===");
  console.log("PatientRegistry:", patientRegistryAddress);
  console.log("BlockedIPRegistry:", blockedIPRegistryAddress);
  console.log("AttackSignatureRegistry:", attackSignatureRegistryAddress);
  console.log("\nDeployment info saved to:", deploymentsDir);
  console.log("\nAll contracts deployed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
