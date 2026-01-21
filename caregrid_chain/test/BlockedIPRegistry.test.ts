import { expect } from "chai";
import { ethers } from "hardhat";
import { BlockedIPRegistry } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("BlockedIPRegistry", function () {
  let blockedIPRegistry: BlockedIPRegistry;
  let owner: HardhatEthersSigner;
  let addr1: HardhatEthersSigner;
  let addr2: HardhatEthersSigner;

  const ipHash1 = ethers.keccak256(ethers.toUtf8Bytes("192.168.1.1"));
  const ipHash2 = ethers.keccak256(ethers.toUtf8Bytes("10.0.0.1"));
  const invalidIpHash = ethers.ZeroHash;
  const blockReason = "Suspicious activity detected";
  const duration = 3600; // 1 hour

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    
    const BlockedIPRegistry = await ethers.getContractFactory("BlockedIPRegistry");
    blockedIPRegistry = await BlockedIPRegistry.deploy();
    await blockedIPRegistry.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      expect(await blockedIPRegistry.getAddress()).to.be.properAddress;
    });

    it("Should start with empty blocklist", async function () {
      expect(await blockedIPRegistry.getBlockedIPCount()).to.equal(0);
      const list = await blockedIPRegistry.getBlockedIPList();
      expect(list.length).to.equal(0);
    });
  });

  describe("IP Blocking - Automatic", function () {
    it("Should block IP automatically with expiry", async function () {
      const tx = await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      await tx.wait();

      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.true;
      expect(await blockedIPRegistry.isBlocked(ipHash1)).to.be.true;
    });

    it("Should emit IPBlocked event for automatic block", async function () {
      const currentTime = await time.latest();
      const expectedExpiry = currentTime + duration + 1; // +1 for next block

      await expect(blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false))
        .to.emit(blockedIPRegistry, "IPBlocked")
        .withArgs(ipHash1, currentTime + 1, expectedExpiry, blockReason, false);
    });

    it("Should store correct block entry data for automatic block", async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      
      const blockEntry = await blockedIPRegistry.getBlockEntry(ipHash1);
      expect(blockEntry.ipHash).to.equal(ipHash1);
      expect(blockEntry.reason).to.equal(blockReason);
      expect(blockEntry.blockedBy).to.equal(owner.address);
      expect(blockEntry.isManual).to.be.false;
      expect(blockEntry.expiryTime).to.be.greaterThan(blockEntry.blockTime);
    });

    it("Should add IP to blocked list", async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      
      expect(await blockedIPRegistry.getBlockedIPCount()).to.equal(1);
      const list = await blockedIPRegistry.getBlockedIPList();
      expect(list[0]).to.equal(ipHash1);
    });
  });

  describe("IP Blocking - Manual", function () {
    it("Should block IP manually without expiry", async function () {
      const tx = await blockedIPRegistry.blockIP(ipHash1, 0, blockReason, true);
      await tx.wait();

      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.true;
      
      const blockEntry = await blockedIPRegistry.getBlockEntry(ipHash1);
      expect(blockEntry.isManual).to.be.true;
      expect(blockEntry.expiryTime).to.equal(0);
    });

    it("Should emit IPBlocked event for manual block", async function () {
      const currentTime = await time.latest();

      await expect(blockedIPRegistry.blockIP(ipHash1, 0, blockReason, true))
        .to.emit(blockedIPRegistry, "IPBlocked")
        .withArgs(ipHash1, currentTime + 1, 0, blockReason, true);
    });

    it("Should allow different addresses to block IPs", async function () {
      await blockedIPRegistry.connect(addr1).blockIP(ipHash1, duration, "Reason 1", false);
      await blockedIPRegistry.connect(addr2).blockIP(ipHash2, 0, "Reason 2", true);

      const entry1 = await blockedIPRegistry.getBlockEntry(ipHash1);
      const entry2 = await blockedIPRegistry.getBlockEntry(ipHash2);
      
      expect(entry1.blockedBy).to.equal(addr1.address);
      expect(entry2.blockedBy).to.equal(addr2.address);
    });
  });

  describe("Edge Cases and Invalid Inputs", function () {
    it("Should reject invalid IP hash (zero hash)", async function () {
      await expect(blockedIPRegistry.blockIP(invalidIpHash, duration, blockReason, false))
        .to.be.revertedWith("Invalid IP hash");
    });

    it("Should reject blocking already blocked IP", async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      
      await expect(blockedIPRegistry.blockIP(ipHash1, duration, "Another reason", false))
        .to.be.revertedWith("IP already blocked");
    });

    it("Should return false for non-blocked IP", async function () {
      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.false;
    });

    it("Should revert when getting non-existent block entry", async function () {
      await expect(blockedIPRegistry.getBlockEntry(ipHash1))
        .to.be.revertedWith("IP not blocked");
    });
  });

  describe("IP Unblocking", function () {
    beforeEach(async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
    });

    it("Should unblock IP successfully", async function () {
      const tx = await blockedIPRegistry.unblockIP(ipHash1);
      await tx.wait();

      expect(await blockedIPRegistry.isBlocked(ipHash1)).to.be.false;
    });

    it("Should emit IPUnblocked event", async function () {
      const currentTime = await time.latest();

      await expect(blockedIPRegistry.unblockIP(ipHash1))
        .to.emit(blockedIPRegistry, "IPUnblocked")
        .withArgs(ipHash1, currentTime + 1);
    });

    it("Should reject unblocking non-blocked IP", async function () {
      await expect(blockedIPRegistry.unblockIP(ipHash2))
        .to.be.revertedWith("IP not blocked");
    });

    it("Should reject unblocking already unblocked IP", async function () {
      await blockedIPRegistry.unblockIP(ipHash1);
      
      await expect(blockedIPRegistry.unblockIP(ipHash1))
        .to.be.revertedWith("IP not blocked");
    });
  });

  describe("Expiry Logic", function () {
    it("Should return false for expired automatic blocks", async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      
      // Fast forward time beyond expiry
      await time.increase(duration + 1);
      
      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.false;
    });

    it("Should never expire manual blocks", async function () {
      await blockedIPRegistry.blockIP(ipHash1, 0, blockReason, true);
      
      // Fast forward time significantly
      await time.increase(duration * 24); // 24 hours
      
      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.true;
    });

    it("Should cleanup expired blocks", async function () {
      // Block multiple IPs with different expiry times
      await blockedIPRegistry.blockIP(ipHash1, 100, "Short block", false);
      await blockedIPRegistry.blockIP(ipHash2, 0, "Manual block", true);
      
      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.true;
      expect(await blockedIPRegistry.isIPBlocked(ipHash2)).to.be.true;
      
      // Fast forward past first expiry
      await time.increase(101);
      
      // Cleanup expired blocks
      const tx = await blockedIPRegistry.cleanupExpiredBlocks();
      await tx.wait();
      
      // Check that expired block was cleaned up but manual block remains
      expect(await blockedIPRegistry.isBlocked(ipHash1)).to.be.false;
      expect(await blockedIPRegistry.isIPBlocked(ipHash2)).to.be.true;
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await blockedIPRegistry.blockIP(ipHash1, duration, blockReason, false);
      await blockedIPRegistry.blockIP(ipHash2, 0, "Manual block", true);
    });

    it("Should return correct blocked IP count", async function () {
      expect(await blockedIPRegistry.getBlockedIPCount()).to.equal(2);
    });

    it("Should return correct blocked IP list", async function () {
      const list = await blockedIPRegistry.getBlockedIPList();
      expect(list.length).to.equal(2);
      expect(list).to.include(ipHash1);
      expect(list).to.include(ipHash2);
    });

    it("Should return correct block entry details", async function () {
      const entry1 = await blockedIPRegistry.getBlockEntry(ipHash1);
      const entry2 = await blockedIPRegistry.getBlockEntry(ipHash2);
      
      expect(entry1.isManual).to.be.false;
      expect(entry1.expiryTime).to.be.greaterThan(0);
      
      expect(entry2.isManual).to.be.true;
      expect(entry2.expiryTime).to.equal(0);
    });

    it("Should return correct blocking status", async function () {
      expect(await blockedIPRegistry.isIPBlocked(ipHash1)).to.be.true;
      expect(await blockedIPRegistry.isIPBlocked(ipHash2)).to.be.true;
      
      const nonBlockedHash = ethers.keccak256(ethers.toUtf8Bytes("1.1.1.1"));
      expect(await blockedIPRegistry.isIPBlocked(nonBlockedHash)).to.be.false;
    });
  });
});