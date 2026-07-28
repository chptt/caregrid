// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract CareGridAccess is AccessControl {
    // Roles
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant BRANCH_MANAGER_ROLE = keccak256("BRANCH_MANAGER_ROLE");
    bytes32 public constant DOCTOR_ROLE = keccak256("DOCTOR_ROLE");
    bytes32 public constant NURSE_ROLE = keccak256("NURSE_ROLE");
    bytes32 public constant PATIENT_ROLE = keccak256("PATIENT_ROLE");

    // Branch mapping
    mapping(address => string) public branchOf;

    // Events
    event RoleAssigned(address indexed account, bytes32 role, string branch);
    event RoleRevoked(address indexed account, bytes32 role);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    // Assign role with branch tag
    function assignRole(address account, bytes32 role, string memory branch) public onlyRole(ADMIN_ROLE) {
        require(account != address(0), "Invalid address");
        _grantRole(role, account);
        branchOf[account] = branch;
        emit RoleAssigned(account, role, branch);
    }

    // Revoke role
    function revokeRole(address account, bytes32 role) public onlyRole(ADMIN_ROLE) {
        require(hasRole(role, account), "Account doesn't have role");
        _revokeRole(role, account);
        emit RoleRevoked(account, role);
    }

    // Check role and branch
    function hasRoleInBranch(address account, bytes32 role, string memory branch) public view returns (bool) {
        return hasRole(role, account) && keccak256(bytes(branchOf[account])) == keccak256(bytes(branch));
    }

    // Get branch of user
    function getBranch(address account) public view returns (string memory) {
        return branchOf[account];
    }

    // Modifier for branch-specific access
    modifier onlyBranch(bytes32 role, string memory branch) {
        require(hasRoleInBranch(msg.sender, role, branch), "Unauthorized for this branch");
        _;
    }

    // Example: branch-specific function
    function updateBranchRecords(string memory branch, string memory data) public onlyBranch(DOCTOR_ROLE, branch) {
        // Logic to update records for the branch
    }
}