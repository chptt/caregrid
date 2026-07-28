const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Counter", function () {
  it("Should return the new count once it's incremented", async function () {
    const Counter = await ethers.getContractFactory("Counter");
    const counter = await Counter.deploy();
    await counter.waitForDeployment();

    expect(await counter.x()).to.equal(0);

    const tx = await counter.inc();

    // wait until the transaction is mined
    await tx.wait();

    expect(await counter.x()).to.equal(1);
  });
});
