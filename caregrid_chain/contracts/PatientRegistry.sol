// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PatientRegistry {
    struct Patient {
        bytes32 patientIdHash;      // Hashed patient ID for privacy
        uint256 registrationTime;
        address registeredBy;       // Hospital/branch that registered
        bool isActive;
    }
    
    mapping(bytes32 => Patient) public patients;
    mapping(bytes32 => bool) public patientExists;
    
    event PatientRegistered(bytes32 indexed patientIdHash, uint256 timestamp, address registeredBy);
    event PatientDeactivated(bytes32 indexed patientIdHash, uint256 timestamp);
    
    /**
     * @dev Register a new patient with their hashed ID
     * @param patientIdHash The keccak256 hash of the patient's unique identifier
     * @return success True if registration was successful
     */
    function registerPatient(bytes32 patientIdHash) external returns (bool) {
        require(patientIdHash != bytes32(0), "Invalid patient ID hash");
        require(!patientExists[patientIdHash], "Patient already registered");
        
        patients[patientIdHash] = Patient({
            patientIdHash: patientIdHash,
            registrationTime: block.timestamp,
            registeredBy: msg.sender,
            isActive: true
        });
        
        patientExists[patientIdHash] = true;
        
        emit PatientRegistered(patientIdHash, block.timestamp, msg.sender);
        
        return true;
    }
    
    /**
     * @dev Check if a patient is registered
     * @param patientIdHash The keccak256 hash of the patient's unique identifier
     * @return registered True if patient is registered and active
     */
    function isPatientRegistered(bytes32 patientIdHash) external view returns (bool) {
        return patientExists[patientIdHash] && patients[patientIdHash].isActive;
    }
    
    /**
     * @dev Get patient information
     * @param patientIdHash The keccak256 hash of the patient's unique identifier
     * @return patient The patient struct containing registration details
     */
    function getPatient(bytes32 patientIdHash) external view returns (Patient memory) {
        require(patientExists[patientIdHash], "Patient not found");
        return patients[patientIdHash];
    }
    
    /**
     * @dev Deactivate a patient (soft delete)
     * @param patientIdHash The keccak256 hash of the patient's unique identifier
     */
    function deactivatePatient(bytes32 patientIdHash) external {
        require(patientExists[patientIdHash], "Patient not found");
        require(patients[patientIdHash].isActive, "Patient already deactivated");
        
        patients[patientIdHash].isActive = false;
        
        emit PatientDeactivated(patientIdHash, block.timestamp);
    }
}
