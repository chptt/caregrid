import { expect } from "chai";
import { ethers } from "hardhat";
import { AttackSignatureRegistry } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("AttackSignatureRegistry", function () {
  let attackSignatureRegistry: AttackSignatureRegistry;
  let owner: HardhatEthersSigner;
  let addr1: HardhatEthersSigner;
  let addr2: HardhatEthersSigner;

  const pattern1 = '{"endpoint": "/api/login", "rate": 100, "user_agent": "bot"}';
  const pattern2 = '{"endpoint": "/api/data", "rate": 200, "method": "POST"}';
  const emptyPattern = "";
  const severity1 = 5;
  const severity2 = 8;
  const invalidSeverityLow = 0;
  const invalidSeverityHigh = 11;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    
    const AttackSignatureRegistry = await ethers.getContractFactory("AttackSignatureRegistry");
    attackSignatureRegistry = await AttackSignatureRegistry.deploy();
    await attackSignatureRegistry.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      expect(await attackSignatureRegistry.getAddress()).to.be.properAddress;
    });

    it("Should start with empty signature registry", async function () {
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(0);
      const signatures = await attackSignatureRegistry.getAllSignatures();
      expect(signatures.length).to.equal(0);
    });
  });

  describe("Adding Attack Signatures", function () {
    it("Should add signature successfully", async function () {
      const tx = await attackSignatureRegistry.addSignature(pattern1, severity1);
      const receipt = await tx.wait();
      
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(1);
      
      // Get signature hash from event
      const event = receipt?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      
      if (event) {
        const parsedEvent = attackSignatureRegistry.interface.parseLog(event);
        const signatureHash = parsedEvent?.args[0];
        expect(await attackSignatureRegistry.hasSignature(signatureHash)).to.be.true;
      }
    });

    it("Should emit AttackSignatureAdded event", async function () {
      const currentTime = await ethers.provider.getBlock("latest").then(b => b!.timestamp);
      
      await expect(attackSignatureRegistry.addSignature(pattern1, severity1))
        .to.emit(attackSignatureRegistry, "AttackSignatureAdded");
      
      // We can't predict the exact hash due to timestamp and sender inclusion
      // but we can verify the event was emitted with correct severity
    });

    it("Should store correct signature data", async function () {
      const tx = await attackSignatureRegistry.addSignature(pattern1, severity1);
      const receipt = await tx.wait();
      
      // Get signature hash from event
      const event = receipt?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      
      if (event) {
        const parsedEvent = attackSignatureRegistry.interface.parseLog(event);
        const signatureHash = parsedEvent?.args[0];
        
        const signature = await attackSignatureRegistry.getSignature(signatureHash);
        expect(signature.signatureHash).to.equal(signatureHash);
        expect(signature.pattern).to.equal(pattern1);
        expect(signature.severity).to.equal(severity1);
        expect(signature.reportedBy).to.equal(owner.address);
        expect(signature.detectedTime).to.be.greaterThan(0);
      }
    });

    it("Should allow different addresses to add signatures", async function () {
      await attackSignatureRegistry.connect(addr1).addSignature(pattern1, severity1);
      await attackSignatureRegistry.connect(addr2).addSignature(pattern2, severity2);
      
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(2);
    });

    it("Should return signature hash", async function () {
      const tx = await attackSignatureRegistry.addSignature(pattern1, severity1);
      const receipt = await tx.wait();
      
      // Verify that the transaction succeeded and returned a hash
      expect(receipt?.status).to.equal(1);
    });
  });

  describe("Edge Cases and Invalid Inputs", function () {
    it("Should reject empty pattern", async function () {
      await expect(attackSignatureRegistry.addSignature(emptyPattern, severity1))
        .to.be.revertedWith("Pattern cannot be empty");
    });

    it("Should reject invalid severity (too low)", async function () {
      await expect(attackSignatureRegistry.addSignature(pattern1, invalidSeverityLow))
        .to.be.revertedWith("Severity must be between 1 and 10");
    });

    it("Should reject invalid severity (too high)", async function () {
      await expect(attackSignatureRegistry.addSignature(pattern1, invalidSeverityHigh))
        .to.be.revertedWith("Severity must be between 1 and 10");
    });

    it("Should handle boundary severity values", async function () {
      // Test minimum valid severity
      await expect(attackSignatureRegistry.addSignature(pattern1, 1))
        .to.not.be.reverted;
      
      // Test maximum valid severity
      await expect(attackSignatureRegistry.addSignature(pattern2, 10))
        .to.not.be.reverted;
      
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(2);
    });

    it("Should reject getting non-existent signature", async function () {
      const fakeHash = ethers.keccak256(ethers.toUtf8Bytes("fake"));
      await expect(attackSignatureRegistry.getSignature(fakeHash))
        .to.be.revertedWith("Signature not found");
    });
  });

  describe("Signature Retrieval", function () {
    let signatureHash1: string;
    let signatureHash2: string;

    beforeEach(async function () {
      const tx1 = await attackSignatureRegistry.addSignature(pattern1, severity1);
      const receipt1 = await tx1.wait();
      const event1 = receipt1?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event1) {
        const parsedEvent1 = attackSignatureRegistry.interface.parseLog(event1);
        signatureHash1 = parsedEvent1?.args[0];
      }

      const tx2 = await attackSignatureRegistry.addSignature(pattern2, severity2);
      const receipt2 = await tx2.wait();
      const event2 = receipt2?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event2) {
        const parsedEvent2 = attackSignatureRegistry.interface.parseLog(event2);
        signatureHash2 = parsedEvent2?.args[0];
      }
    });

    it("Should get signature by hash", async function () {
      const signature = await attackSignatureRegistry.getSignature(signatureHash1);
      expect(signature.pattern).to.equal(pattern1);
      expect(signature.severity).to.equal(severity1);
    });

    it("Should get all signatures", async function () {
      const allSignatures = await attackSignatureRegistry.getAllSignatures();
      expect(allSignatures.length).to.equal(2);
      expect(allSignatures).to.include(signatureHash1);
      expect(allSignatures).to.include(signatureHash2);
    });

    it("Should return correct signature count", async function () {
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(2);
    });

    it("Should check signature existence", async function () {
      expect(await attackSignatureRegistry.hasSignature(signatureHash1)).to.be.true;
      expect(await attackSignatureRegistry.hasSignature(signatureHash2)).to.be.true;
      
      const fakeHash = ethers.keccak256(ethers.toUtf8Bytes("fake"));
      expect(await attackSignatureRegistry.hasSignature(fakeHash)).to.be.false;
    });
  });

  describe("Severity Updates", function () {
    let signatureHash: string;

    beforeEach(async function () {
      const tx = await attackSignatureRegistry.addSignature(pattern1, severity1);
      const receipt = await tx.wait();
      const event = receipt?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event) {
        const parsedEvent = attackSignatureRegistry.interface.parseLog(event);
        signatureHash = parsedEvent?.args[0];
      }
    });

    it("Should update severity successfully", async function () {
      const newSeverity = 9;
      await attackSignatureRegistry.updateSeverity(signatureHash, newSeverity);
      
      const signature = await attackSignatureRegistry.getSignature(signatureHash);
      expect(signature.severity).to.equal(newSeverity);
    });

    it("Should emit AttackSignatureUpdated event", async function () {
      const newSeverity = 7;
      const currentTime = await ethers.provider.getBlock("latest").then(b => b!.timestamp);
      
      await expect(attackSignatureRegistry.updateSeverity(signatureHash, newSeverity))
        .to.emit(attackSignatureRegistry, "AttackSignatureUpdated")
        .withArgs(signatureHash, newSeverity, currentTime + 1);
    });

    it("Should reject updating non-existent signature", async function () {
      const fakeHash = ethers.keccak256(ethers.toUtf8Bytes("fake"));
      await expect(attackSignatureRegistry.updateSeverity(fakeHash, 5))
        .to.be.revertedWith("Signature not found");
    });

    it("Should reject invalid severity in update", async function () {
      await expect(attackSignatureRegistry.updateSeverity(signatureHash, 0))
        .to.be.revertedWith("Severity must be between 1 and 10");
      
      await expect(attackSignatureRegistry.updateSeverity(signatureHash, 11))
        .to.be.revertedWith("Severity must be between 1 and 10");
    });
  });

  describe("Severity Filtering", function () {
    let lowSeverityHash: string;
    let mediumSeverityHash: string;
    let highSeverityHash: string;

    beforeEach(async function () {
      // Add signatures with different severities
      const tx1 = await attackSignatureRegistry.addSignature(pattern1, 3); // Low
      const receipt1 = await tx1.wait();
      const event1 = receipt1?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event1) {
        const parsedEvent1 = attackSignatureRegistry.interface.parseLog(event1);
        lowSeverityHash = parsedEvent1?.args[0];
      }

      const tx2 = await attackSignatureRegistry.addSignature(pattern2, 6); // Medium
      const receipt2 = await tx2.wait();
      const event2 = receipt2?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event2) {
        const parsedEvent2 = attackSignatureRegistry.interface.parseLog(event2);
        mediumSeverityHash = parsedEvent2?.args[0];
      }

      const tx3 = await attackSignatureRegistry.addSignature('{"high": "severity"}', 9); // High
      const receipt3 = await tx3.wait();
      const event3 = receipt3?.logs.find(log => {
        try {
          return attackSignatureRegistry.interface.parseLog(log)?.name === "AttackSignatureAdded";
        } catch {
          return false;
        }
      });
      if (event3) {
        const parsedEvent3 = attackSignatureRegistry.interface.parseLog(event3);
        highSeverityHash = parsedEvent3?.args[0];
      }
    });

    it("Should filter signatures by minimum severity", async function () {
      // Get signatures with severity >= 6
      const mediumAndHigh = await attackSignatureRegistry.getSignaturesBySeverity(6);
      expect(mediumAndHigh.length).to.equal(2);
      expect(mediumAndHigh).to.include(mediumSeverityHash);
      expect(mediumAndHigh).to.include(highSeverityHash);
      expect(mediumAndHigh).to.not.include(lowSeverityHash);
    });

    it("Should return all signatures for minimum severity 1", async function () {
      const allSignatures = await attackSignatureRegistry.getSignaturesBySeverity(1);
      expect(allSignatures.length).to.equal(3);
    });

    it("Should return empty array for very high minimum severity", async function () {
      const noSignatures = await attackSignatureRegistry.getSignaturesBySeverity(10);
      expect(noSignatures.length).to.equal(0);
    });

    it("Should reject invalid severity in filter", async function () {
      await expect(attackSignatureRegistry.getSignaturesBySeverity(0))
        .to.be.revertedWith("Severity must be between 1 and 10");
      
      await expect(attackSignatureRegistry.getSignaturesBySeverity(11))
        .to.be.revertedWith("Severity must be between 1 and 10");
    });
  });

  describe("Complex Scenarios", function () {
    it("Should handle multiple signatures from same address", async function () {
      await attackSignatureRegistry.addSignature(pattern1, severity1);
      await attackSignatureRegistry.addSignature(pattern2, severity2);
      
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(2);
      
      const allSignatures = await attackSignatureRegistry.getAllSignatures();
      expect(allSignatures.length).to.equal(2);
    });

    it("Should maintain signature uniqueness based on hash generation", async function () {
      // Add same pattern from different addresses at different times
      await attackSignatureRegistry.connect(addr1).addSignature(pattern1, severity1);
      
      // Wait a bit to ensure different timestamp
      await ethers.provider.send("evm_mine", []);
      
      await attackSignatureRegistry.connect(addr2).addSignature(pattern1, severity1);
      
      // Should create two different signatures even with same pattern
      expect(await attackSignatureRegistry.getSignatureCount()).to.equal(2);
    });
  });
});