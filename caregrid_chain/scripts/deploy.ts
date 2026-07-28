import hre from "hardhat";
import { ethers } from "hardhat";

async function main() {
  const Contract = await ethers.getContractFactory("Counter");
  const contract = await Contract.deploy();
  await contract.waitForDeployment();

  console.log("Deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
