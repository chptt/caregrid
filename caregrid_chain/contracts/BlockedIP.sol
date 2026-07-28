// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BlockedIPRegistry {
    struct BlockEntry {
        bytes32 ipHash;             // Hashed IP for privacy
        uint256 blockTime;
        uint256 expiryTime;         // Auto-unblock time
        string reason;
        address blockedBy;
        bool isManual;              // Manual vs automatic block
    }
    
    mapping(bytes32 => BlockEntry) public blockedIPs;
    mapping(bytes32 => bool) public isBlocked;
    bytes32[] public blockedIPList;
    
    event IPBlocked(bytes32 indexed ipHash, uint256 blockTime, uint256 expiryTime, string reason, bool isManual);
    event IPUnblocked(bytes32 indexed ipHash, uint256 timestamp);
    
    /**
     * @dev Block an IP address with expiry time and reason
     * @param ipHash The keccak256 hash of the IP address
     * @param duration Duration in seconds until auto-unblock (0 for manual blocks)
     * @param reason Reason for blocking
     * @param manual True if manually blocked by admin, false if automatic
     */
    function blockIP(bytes32 ipHash, uint256 duration, string memory reason, bool manual) external {
        require(ipHash != bytes32(0), "Invalid IP hash");
        require(!isBlocked[ipHash], "IP already blocked");
        
        uint256 expiryTime = manual ? 0 : block.timestamp + duration;
        
        blockedIPs[ipHash] = BlockEntry({
            ipHash: ipHash,
            blockTime: block.timestamp,
            expiryTime: expiryTime,
            reason: reason,
            blockedBy: msg.sender,
            isManual: manual
        });
        
        isBlocked[ipHash] = true;
        blockedIPList.push(ipHash);
        
        emit IPBlocked(ipHash, block.timestamp, expiryTime, reason, manual);
    }
    
    /**
     * @dev Unblock an IP address
     * @param ipHash The keccak256 hash of the IP address
     */
    function unblockIP(bytes32 ipHash) external {
        require(isBlocked[ipHash], "IP not blocked");
        
        isBlocked[ipHash] = false;
        
        emit IPUnblocked(ipHash, block.timestamp);
    }
    
    /**
     * @dev Check if an IP is currently blocked
     * @param ipHash The keccak256 hash of the IP address
     * @return blocked True if IP is blocked and not expired
     */
    function isIPBlocked(bytes32 ipHash) external view returns (bool) {
        if (!isBlocked[ipHash]) {
            return false;
        }
        
        BlockEntry memory entry = blockedIPs[ipHash];
        
        // Manual blocks never expire (expiryTime == 0)
        if (entry.isManual) {
            return true;
        }
        
        // Check if automatic block has expired
        if (entry.expiryTime > 0 && block.timestamp >= entry.expiryTime) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev Get block entry details
     * @param ipHash The keccak256 hash of the IP address
     * @return entry The block entry struct
     */
    function getBlockEntry(bytes32 ipHash) external view returns (BlockEntry memory) {
        require(isBlocked[ipHash], "IP not blocked");
        return blockedIPs[ipHash];
    }
    
    /**
     * @dev Clean up expired automatic blocks
     * @dev This function can be called periodically to remove expired entries
     */
    function cleanupExpiredBlocks() external {
        uint256 count = 0;
        
        for (uint256 i = 0; i < blockedIPList.length; i++) {
            bytes32 ipHash = blockedIPList[i];
            
            if (isBlocked[ipHash]) {
                BlockEntry memory entry = blockedIPs[ipHash];
                
                // Only cleanup automatic blocks that have expired
                if (!entry.isManual && entry.expiryTime > 0 && block.timestamp >= entry.expiryTime) {
                    isBlocked[ipHash] = false;
                    emit IPUnblocked(ipHash, block.timestamp);
                    count++;
                }
            }
        }
    }
    
    /**
     * @dev Get all currently blocked IPs (including expired ones in mapping)
     * @return hashes Array of blocked IP hashes
     */
    function getBlockedIPList() external view returns (bytes32[] memory) {
        return blockedIPList;
    }
    
    /**
     * @dev Get count of blocked IPs
     * @return count Number of IPs in the blocklist
     */
    function getBlockedIPCount() external view returns (uint256) {
        return blockedIPList.length;
    }
}