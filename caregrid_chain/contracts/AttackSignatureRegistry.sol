// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AttackSignatureRegistry {
    struct AttackSignature {
        bytes32 signatureHash;
        string pattern;             // JSON string describing attack pattern
        uint256 detectedTime;
        address reportedBy;
        uint256 severity;           // 1-10 scale
    }
    
    mapping(bytes32 => AttackSignature) public signatures;
    mapping(bytes32 => bool) public signatureExists;
    bytes32[] public signatureList;
    
    event AttackSignatureAdded(bytes32 indexed signatureHash, uint256 severity, uint256 timestamp, address reportedBy);
    event AttackSignatureUpdated(bytes32 indexed signatureHash, uint256 newSeverity, uint256 timestamp);
    
    /**
     * @dev Add a new attack signature
     * @param pattern JSON string describing the attack pattern
     * @param severity Severity level from 1 (low) to 10 (critical)
     * @return signatureHash The hash of the created signature
     */
    function addSignature(string memory pattern, uint256 severity) external returns (bytes32) {
        require(bytes(pattern).length > 0, "Pattern cannot be empty");
        require(severity >= 1 && severity <= 10, "Severity must be between 1 and 10");
        
        bytes32 signatureHash = keccak256(abi.encodePacked(pattern, block.timestamp, msg.sender));
        require(!signatureExists[signatureHash], "Signature already exists");
        
        signatures[signatureHash] = AttackSignature({
            signatureHash: signatureHash,
            pattern: pattern,
            detectedTime: block.timestamp,
            reportedBy: msg.sender,
            severity: severity
        });
        
        signatureExists[signatureHash] = true;
        signatureList.push(signatureHash);
        
        emit AttackSignatureAdded(signatureHash, severity, block.timestamp, msg.sender);
        
        return signatureHash;
    }
    
    /**
     * @dev Get a specific attack signature
     * @param signatureHash The hash of the signature to retrieve
     * @return signature The attack signature struct
     */
    function getSignature(bytes32 signatureHash) external view returns (AttackSignature memory) {
        require(signatureExists[signatureHash], "Signature not found");
        return signatures[signatureHash];
    }
    
    /**
     * @dev Get all signature hashes
     * @return hashes Array of all signature hashes
     */
    function getAllSignatures() external view returns (bytes32[] memory) {
        return signatureList;
    }
    
    /**
     * @dev Get the total number of signatures
     * @return count Number of signatures in the registry
     */
    function getSignatureCount() external view returns (uint256) {
        return signatureList.length;
    }
    
    /**
     * @dev Update the severity of an existing signature
     * @param signatureHash The hash of the signature to update
     * @param newSeverity New severity level from 1 to 10
     */
    function updateSeverity(bytes32 signatureHash, uint256 newSeverity) external {
        require(signatureExists[signatureHash], "Signature not found");
        require(newSeverity >= 1 && newSeverity <= 10, "Severity must be between 1 and 10");
        
        signatures[signatureHash].severity = newSeverity;
        
        emit AttackSignatureUpdated(signatureHash, newSeverity, block.timestamp);
    }
    
    /**
     * @dev Check if a signature exists
     * @param signatureHash The hash to check
     * @return exists True if signature exists
     */
    function hasSignature(bytes32 signatureHash) external view returns (bool) {
        return signatureExists[signatureHash];
    }
    
    /**
     * @dev Get signatures by severity level
     * @param minSeverity Minimum severity level
     * @return hashes Array of signature hashes matching criteria
     */
    function getSignaturesBySeverity(uint256 minSeverity) external view returns (bytes32[] memory) {
        require(minSeverity >= 1 && minSeverity <= 10, "Severity must be between 1 and 10");
        
        // First pass: count matching signatures
        uint256 count = 0;
        for (uint256 i = 0; i < signatureList.length; i++) {
            if (signatures[signatureList[i]].severity >= minSeverity) {
                count++;
            }
        }
        
        // Second pass: collect matching signatures
        bytes32[] memory result = new bytes32[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < signatureList.length; i++) {
            if (signatures[signatureList[i]].severity >= minSeverity) {
                result[index] = signatureList[i];
                index++;
            }
        }
        
        return result;
    }
}
