// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BlockedIPRegistry {
    struct BlockEntry {
        string ip;
        uint256 timestamp;
    }

    BlockEntry[] public blockedIPs;

    event IPBlocked(string ip, uint256 timestamp);

    function blockIP(string memory ip) public {
        blockedIPs.push(BlockEntry(ip, block.timestamp));
        emit IPBlocked(ip, block.timestamp);
    }

    function getBlockedIPs() public view returns (BlockEntry[] memory) {
        return blockedIPs;
    }
}