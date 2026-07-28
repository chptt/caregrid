import { expect } from "chai";
import { ethers } from "hardhat";
import { PatientRegistry } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("PatientRegistry", function () {
  let patientRegistry: PatientRegistry;
  let owner: HardhatEthersSigner;
  let addr1: HardhatEthersSigner;
  let addr2: HardhatEthersSigner;

  const patientId1 = ethers.keccak256(ethers.toUtf8Bytes("patient1@example.com"));
  const patientId2 = ethers.keccak256(ethers.toUtf8Bytes("patient2@example.com"));
  const invalidPatientId = ethers.ZeroHash;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    
    const PatientRegistry = await ethers.getContractFactory("PatientRegistry");
    patientRegistry = await PatientRegistry.deploy();
    await patientRegistry.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      expect(await patientRegistry.getAddress()).to.be.properAddress;
    });
  });

  describe("Patient Registration", function () {
    it("Should register a new patient successfully", async function () {
      const tx = await patientRegistry.registerPatient(patientId1);
      await tx.wait();

      expect(await patientRegistry.isPatientRegistered(patientId1)).to.be.true;
      expect(await patientRegistry.patientExists(patientId1)).to.be.true;
    });

    it("Should emit PatientRegistered event", async function () {
      await expect(patientRegistry.registerPatient(patientId1))
        .to.emit(patientRegistry, "PatientRegistered")
        .withArgs(patientId1, await ethers.provider.getBlock("latest").then(b => b!.timestamp + 1), owner.address);
    });

    it("Should store correct patient data", async function () {
      await patientRegistry.registerPatient(patientId1);
      
      const patient = await patientRegistry.getPatient(patientId1);
      expect(patient.patientIdHash).to.equal(patientId1);
      expect(patient.registeredBy).to.equal(owner.address);
      expect(patient.isActive).to.be.true;
      expect(patient.registrationTime).to.be.greaterThan(0);
    });

    it("Should allow different addresses to register patients", async function () {
      await patientRegistry.connect(addr1).registerPatient(patientId1);
      await patientRegistry.connect(addr2).registerPatient(patientId2);

      expect(await patientRegistry.isPatientRegistered(patientId1)).to.be.true;
      expect(await patientRegistry.isPatientRegistered(patientId2)).to.be.true;

      const patient1 = await patientRegistry.getPatient(patientId1);
      const patient2 = await patientRegistry.getPatient(patientId2);
      
      expect(patient1.registeredBy).to.equal(addr1.address);
      expect(patient2.registeredBy).to.equal(addr2.address);
    });
  });

  describe("Edge Cases and Invalid Inputs", function () {
    it("Should reject invalid patient ID hash (zero hash)", async function () {
      await expect(patientRegistry.registerPatient(invalidPatientId))
        .to.be.revertedWith("Invalid patient ID hash");
    });

    it("Should reject duplicate patient registration", async function () {
      await patientRegistry.registerPatient(patientId1);
      
      await expect(patientRegistry.registerPatient(patientId1))
        .to.be.revertedWith("Patient already registered");
    });

    it("Should return false for unregistered patient", async function () {
      expect(await patientRegistry.isPatientRegistered(patientId1)).to.be.false;
    });

    it("Should revert when getting non-existent patient", async function () {
      await expect(patientRegistry.getPatient(patientId1))
        .to.be.revertedWith("Patient not found");
    });
  });

  describe("Patient Deactivation", function () {
    beforeEach(async function () {
      await patientRegistry.registerPatient(patientId1);
    });

    it("Should deactivate patient successfully", async function () {
      const tx = await patientRegistry.deactivatePatient(patientId1);
      await tx.wait();

      expect(await patientRegistry.isPatientRegistered(patientId1)).to.be.false;
      
      const patient = await patientRegistry.getPatient(patientId1);
      expect(patient.isActive).to.be.false;
    });

    it("Should emit PatientDeactivated event", async function () {
      await expect(patientRegistry.deactivatePatient(patientId1))
        .to.emit(patientRegistry, "PatientDeactivated")
        .withArgs(patientId1, await ethers.provider.getBlock("latest").then(b => b!.timestamp + 1));
    });

    it("Should reject deactivating non-existent patient", async function () {
      await expect(patientRegistry.deactivatePatient(patientId2))
        .to.be.revertedWith("Patient not found");
    });

    it("Should reject deactivating already deactivated patient", async function () {
      await patientRegistry.deactivatePatient(patientId1);
      
      await expect(patientRegistry.deactivatePatient(patientId1))
        .to.be.revertedWith("Patient already deactivated");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await patientRegistry.registerPatient(patientId1);
    });

    it("Should return correct registration status", async function () {
      expect(await patientRegistry.isPatientRegistered(patientId1)).to.be.true;
      expect(await patientRegistry.isPatientRegistered(patientId2)).to.be.false;
    });

    it("Should return correct patient existence", async function () {
      expect(await patientRegistry.patientExists(patientId1)).to.be.true;
      expect(await patientRegistry.patientExists(patientId2)).to.be.false;
    });

    it("Should return patient data correctly", async function () {
      const patient = await patientRegistry.getPatient(patientId1);
      
      expect(patient.patientIdHash).to.equal(patientId1);
      expect(patient.registeredBy).to.equal(owner.address);
      expect(patient.isActive).to.be.true;
    });
  });
});