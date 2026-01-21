 # Implementation Plan: Blockchain Healthcare Security System

## Overview

This implementation plan breaks down the MediChain system into discrete, incremental coding tasks. Each task builds on previous work, with property-based tests integrated throughout to validate correctness early. The plan focuses on creating a working system that runs locally with Hardhat blockchain, demonstrating universal patient IDs and multi-factor DDoS detection.

## Tasks

- [x] 1. Set up project infrastructure and dependencies
  - Install and configure Redis for rate limiting
  - Install Web3.py for blockchain integration
  - Install Hypothesis for property-based testing
  - Configure Django settings for blockchain and Redis connections
  - Create deployment scripts for local Hardhat network
  - _Requirements: 9.1, 10.4_

- [x] 2. Implement smart contracts
  - [x] 2.1 Create PatientRegistry smart contract
    - Write Solidity contract with patient registration functions
    - Add events for patient registration
    - Implement uniqueness checks
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [x] 2.2 Write property test for PatientRegistry

    - **Property 1: Patient ID Uniqueness**
    - **Property 2: Patient ID Determinism**
    - **Property 3: Blockchain Registration Persistence**
    - **Validates: Requirements 1.1, 1.2, 1.4**
  
  - [x] 2.3 Enhance BlockedIPRegistry smart contract
    - Add expiry time and reason fields to existing contract
    - Implement manual vs automatic block tracking
    - Add unblock functionality
    - Add cleanup function for expired blocks
    - _Requirements: 4.1, 4.2, 4.6_
  
  - [x] 2.4 Write property test for BlockedIPRegistry

    - **Property 15: Blocked IP Rejection**
    - **Property 16: Blocklist Entry Completeness**
    - **Property 18: Manual Unblock Capability**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6**
  
  - [x] 2.5 Create AttackSignatureRegistry smart contract
    - Write contract for storing attack patterns
    - Implement signature addition and retrieval
    - Add severity tracking
    - _Requirements: 5.3, 5.4_
  
  - [x] 2.6 Write unit tests for smart contracts

    - Test contract deployment
    - Test edge cases (duplicate entries, invalid inputs)
    - Test event emissions

- [x] 3. Create Hardhat deployment and testing setup
  - [x] 3.1 Write deployment scripts
    - Create deploy.js for all three contracts
    - Save deployed addresses to JSON files
    - Configure Hardhat for local network
    - _Requirements: 9.1_
  
  - [x] 3.2 Create contract interaction utilities
    - Write helper functions to load contract ABIs
    - Create utilities to read deployed addresses
    - Test contract calls from Node.js
    - _Requirements: 9.1_

- [x] 4. Implement Django models
  - [x] 4.1 Enhance Patient model with blockchain integration
    - Add blockchain_id field
    - Add blockchain_registered flag
    - Add registration_tx_hash field
    - Implement generate_blockchain_id method
    - _Requirements: 1.1, 8.1_
  
  - [x] 4.2 Write property test for Patient model

    - **Property 1: Patient ID Uniqueness**
    - **Property 2: Patient ID Determinism**
    - **Property 29: Patient Record Completeness**
    - **Validates: Requirements 1.1, 8.1**
  
  - [x] 4.3 Create SecurityLog model
    - Add fields for IP, threat score, threat level
    - Add fields for all threat factors
    - Add action_taken field
    - Add blockchain sync fields
    - _Requirements: 3.1, 3.2_
  
  - [x] 4.4 Create BlockedIP model
    - Add IP address and hash fields
    - Add expiry time and reason
    - Add manual/automatic flag
    - Add blockchain sync fields
    - _Requirements: 4.1, 4.2_
  
  - [x] 4.5 Create AttackPattern model
    - Add pattern hash and JSON data fields
    - Add severity and detection time
    - Add IP and request counts
    - Add blockchain sync fields
    - _Requirements: 5.3_
  
  - [x] 4.6 Write unit tests for models

    - Test model creation and validation
    - Test field constraints
    - Test model methods

- [x] 5. Checkpoint - Database migrations and verification
  - Run migrations and verify all models are created
  - Test model creation in Django shell
  - Ensure all tests pass, ask the user if questions arise

- [x] 6. Implement BlockchainService
  - [x] 6.1 Create BlockchainService class
    - Implement Web3 connection to Hardhat
    - Load contract ABIs and addresses
    - Set up account for transactions
    - _Requirements: 9.1_
  
  - [x] 6.2 Implement patient registration methods
    - Write register_patient method
    - Write is_patient_registered method
    - Add transaction confirmation waiting
    - Add error handling for blockchain failures
    - _Requirements: 1.2, 9.2, 9.3_
  
  - [x] 6.3 Write property test for patient registration

    - **Property 3: Blockchain Registration Persistence**
    - **Property 5: Privacy Preservation**
    - **Validates: Requirements 1.2, 1.5**
  
  - [x] 6.4 Implement IP blocking methods
    - Write block_ip method
    - Write is_ip_blocked method
    - Write unblock_ip method
    - Add expiry time calculation
    - _Requirements: 4.1, 4.3, 4.6_
  
  - [x] 6.5 Write property test for IP blocking

    - **Property 17: Blocklist Synchronization**
    - **Property 32: Transaction Confirmation Ordering**
    - **Validates: Requirements 4.1, 9.3**
  
  - [x] 6.6 Implement attack signature methods
    - Write add_attack_signature method
    - Write get_attack_signatures method
    - Add JSON pattern handling
    - _Requirements: 5.3, 5.4_
  
  - [x] 6.7 Implement caching and fault tolerance
    - Add Redis caching for blockchain reads
    - Implement fallback to cached data on connection failure
    - Add retry logic for failed transactions
    - _Requirements: 9.4, 9.5_
  
  - [x] 6.8 Write property test for fault tolerance

    - **Property 33: Blockchain Caching**
    - **Property 34: Fault Tolerance**
    - **Validates: Requirements 9.4, 9.5**

- [x] 7. Implement ThreatScoreCalculator
  - [x] 7.1 Create ThreatScoreCalculator class
    - Set up Redis and blockchain service dependencies
    - Implement main calculate_threat_score method
    - _Requirements: 2.1_
  
  - [x] 7.2 Implement rate scoring
    - Write _calculate_rate_score method
    - Use Redis for request counting
    - Implement 1-minute sliding window
    - _Requirements: 2.2, 3.3_
  
  - [x] 7.3 Write property test for rate scoring

    - **Property 7: Rate Score Calculation**
    - **Property 14: Rate Tracking Accuracy**
    - **Validates: Requirements 2.2, 3.3**
  
  - [x] 7.4 Implement pattern scoring
    - Write _calculate_pattern_score method
    - Track last 20 endpoints per IP in Redis
    - Calculate endpoint diversity ratio
    - _Requirements: 2.3, 3.4_
  
  - [x] 7.5 Write property test for pattern scoring

    - **Property 8: Pattern Score Calculation**
    - **Validates: Requirements 2.3**
  
  - [x] 7.6 Implement session scoring
    - Write _calculate_session_score method
    - Check for cookies and authentication
    - _Requirements: 2.4_
  
  - [x] 7.7 Write property test for session scoring

    - **Property 9: Session Score Calculation**
    - **Validates: Requirements 2.4**
  
  - [x] 7.8 Implement entropy scoring
    - Write _calculate_entropy_score method
    - Track User-Agent variety in Redis
    - _Requirements: 2.5_
  
  - [x] 7.9 Implement auth failure scoring
    - Write _calculate_auth_failure_score method
    - Track failed login attempts in Redis
    - _Requirements: 2.6_
  
  - [x] 7.10 Implement attack signature matching
    - Write _check_attack_signatures method
    - Write _matches_signature helper
    - Query blockchain for known signatures
    - _Requirements: 5.5_
  
  - [x] 7.11 Write property test for threat scoring

    - **Property 6: Multi-Factor Scoring**
    - **Property 10: Threat Classification Boundaries**
    - **Property 11: Score Monotonicity**
    - **Property 21: Signature Matching Score Boost**
    - **Validates: Requirements 2.1, 2.7, 2.8, 2.9, 5.5**

- [x] 8. Checkpoint - Test threat scoring
  - Test all scoring methods with various inputs
  - Verify Redis integration works
  - Ensure all tests pass, ask the user if questions arise

- [x] 9. Implement SecurityMiddleware
  - [x] 9.1 Create SecurityMiddleware class
    - Set up middleware with Redis and blockchain service
    - Implement process_request method
    - Add IP extraction logic
    - _Requirements: 3.1_
  
  - [x] 9.2 Implement blockchain blocklist checking
    - Check IP against blockchain before processing
    - Return 403 for blocked IPs
    - _Requirements: 4.3, 4.4_
  
  - [x] 9.3 Write property test for blocklist checking

    - **Property 15: Blocked IP Rejection**
    - **Validates: Requirements 4.3, 4.4**
  
  - [x] 9.4 Implement threat-based request handling
    - Calculate threat score for each request
    - Block high-threat requests (score >= 60)
    - Require CAPTCHA for medium-threat (40-59)
    - Allow low-threat requests (< 40)
    - _Requirements: 2.7, 2.8, 2.9_
  
  - [x] 9.5 Write property test for threat handling

    - **Property 10: Threat Classification Boundaries**
    - **Property 22: CAPTCHA Triggering**
    - **Validates: Requirements 2.7, 2.8, 2.9, 6.1**
  
  - [x] 9.6 Implement security logging
    - Log all requests to SecurityLog model
    - Include threat score and all factors
    - Record action taken
    - _Requirements: 3.1, 3.2_
  
  - [x] 9.7 Write property test for security logging

    - **Property 12: Complete Log Entries**
    - **Property 13: Log Temporal Ordering**
    - **Validates: Requirements 3.1, 3.2**
  
  - [x] 9.8 Implement auto-blocking
    - Auto-block IPs with score >= 80
    - Write to blockchain and local database
    - Set 24-hour expiry
    - _Requirements: 11.1, 11.2_
  
  - [x] 9.9 Write property test for auto-blocking

    - **Property 38: High Score Auto-Block**
    - **Property 39: Auto-Block Expiration**
    - **Validates: Requirements 11.1, 11.2**
  
  - [x] 9.10 Implement CAPTCHA verification
    - Add _verify_captcha method
    - Check CAPTCHA tokens in Redis
    - Track CAPTCHA failures
    - Temporarily block after 3 failures
    - _Requirements: 6.2, 6.3_
  
  - [x] 9.11 Write property test for CAPTCHA

    - **Property 23: CAPTCHA Success Processing**
    - **Property 24: CAPTCHA Failure Blocking**
    - **Property 25: Authenticated User CAPTCHA Exemption**
    - **Validates: Requirements 6.2, 6.3, 6.5**

- [x] 10. Implement rate limiting
  - [x] 10.1 Create rate limiting decorator
    - Implement @rate_limit decorator for views
    - Use Redis for distributed rate limiting
    - Support different limits for authenticated/unauthenticated
    - _Requirements: 10.1, 10.2, 10.4_
  
  - [ ]* 10.2 Write property test for rate limiting
    - **Property 35: Unauthenticated Rate Limit Enforcement**
    - **Property 36: Authenticated Rate Limit Enforcement**
    - **Property 37: Rate Limit Threat Score Impact**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.5**
  
  - [x] 10.3 Implement rate limit response
    - Return HTTP 429 when limit exceeded
    - Add Retry-After header
    - Increase threat score for repeat violations
    - _Requirements: 10.3, 10.5_

- [ ] 11. Implement patient management API
  - [x] 11.1 Create patient registration endpoint
    - Implement POST /api/patients/
    - Validate patient data
    - Generate blockchain ID
    - Register on blockchain
    - Save to database
    - _Requirements: 1.1, 1.2, 8.1_
  
  - [ ]* 11.2 Write property test for patient registration
    - **Property 1: Patient ID Uniqueness**
    - **Property 3: Blockchain Registration Persistence**
    - **Property 29: Patient Record Completeness**
    - **Validates: Requirements 1.1, 1.2, 8.1**
  
  - [x] 11.3 Create patient retrieval endpoint
    - Implement GET /api/patients/{id}/
    - Support lookup by blockchain ID
    - Include appointment history
    - _Requirements: 1.3, 8.3_
  
  - [ ]* 11.4 Write property test for patient retrieval
    - **Property 4: Cross-Branch Patient Retrieval**
    - **Validates: Requirements 1.3, 8.4**
  
  - [-] 11.5 Implement role-based access control
    - Add permission classes for patient endpoints
    - Enforce doctor/nurse/admin roles
    - _Requirements: 8.5_
  
  - [ ]* 11.6 Write property test for access control
    - **Property 31: Role-Based Access Control**
    - **Validates: Requirements 8.5**

- [x] 12. Implement appointment management
  - [x] 12.1 Create appointment endpoints
    - Implement POST /api/appointments/
    - Implement GET /api/appointments/
    - Associate with patient using universal ID
    - _Requirements: 8.2_
  
  - [ ]* 12.2 Write property test for appointments
    - **Property 30: Appointment-Patient Association**
    - **Validates: Requirements 8.2**
  
  - [ ]* 12.3 Write unit tests for appointment API
    - Test appointment creation
    - Test appointment listing
    - Test filtering by patient

- [x] 13. Checkpoint - Test patient and appointment APIs
  - Test all endpoints with Postman or curl
  - Verify blockchain integration works
  - Ensure all tests pass, ask the user if questions arise

- [x] 14. Implement anomaly detection
  - [x] 14.1 Create AnomalyDetector class
    - Implement pattern analysis across multiple IPs
    - Track request patterns in Redis
    - _Requirements: 5.1_
  
  - [x] 14.2 Implement coordinated attack detection
    - Detect 50+ IPs with identical patterns
    - Flag as coordinated attack
    - _Requirements: 5.2_
  
  - [ ]* 14.3 Write property test for attack detection
    - **Property 19: Coordinated Attack Detection**
    - **Validates: Requirements 5.2**
  
  - [x] 14.3 Implement attack signature creation
    - Generate signature from detected pattern
    - Store on blockchain
    - Save to local database
    - _Requirements: 5.3, 5.4_
  
  - [ ]* 14.4 Write property test for signatures
    - **Property 20: Attack Signature Creation**
    - **Property 42: Attack Signature Sharing**
    - **Validates: Requirements 5.3, 5.4, 12.2**

- [x] 15. Implement security dashboard API
  - [x] 15.1 Create dashboard endpoints
    - Implement GET /api/security/dashboard/
    - Return current request rate
    - Return top 10 threats
    - Return time-series data
    - _Requirements: 7.1, 7.3, 7.4_
  
  - [ ]* 15.2 Write property test for dashboard
    - **Property 26: Top Threats Ranking**
    - **Property 27: Time-Series Data Accuracy**
    - **Validates: Requirements 7.3, 7.4**
  
  - [x] 15.3 Create admin block/unblock endpoints
    - Implement POST /api/security/block/
    - Implement POST /api/security/unblock/
    - Update blockchain and database
    - _Requirements: 4.6, 7.6_
  
  - [ ]* 15.4 Write property test for admin operations
    - **Property 28: Admin Block/Unblock Operations**
    - **Property 40: Manual Block Persistence**
    - **Property 41: Unblock Score Reset**
    - **Validates: Requirements 4.6, 7.6, 11.4, 11.5**

- [x] 16. Implement background tasks
  - [x] 16.1 Create cleanup task for expired blocks
    - Implement periodic task to remove expired IPs
    - Call blockchain cleanup function
    - Update local database
    - _Requirements: 11.3_
  
  - [x] 16.2 Create blockchain sync task
    - Implement task to sync pending blockchain operations
    - Retry failed transactions
    - Update sync status in database
    - _Requirements: 9.3, 12.5_
  
  - [ ]* 16.3 Write property test for sync
    - **Property 43: New Branch Synchronization**
    - **Property 44: Offline Queue and Sync**
    - **Validates: Requirements 12.3, 12.5**

- [x] 17. Create Docker setup
  - [x] 17.1 Write Dockerfile for Django
    - Create multi-stage build
    - Install all dependencies
    - Configure for production
  
  - [x] 17.2 Create docker-compose.yml
    - Add services: Django, Redis, Hardhat
    - Configure networking
    - Add volume mounts
    - _Requirements: 9.1, 10.4_
  
  - [x] 17.3 Write startup scripts
    - Create script to deploy contracts
    - Create script to run migrations
    - Create script to start all services

- [x] 18. Create documentation
  - [x] 18.1 Write comprehensive README.md
    - Add project description
    - Add architecture diagram
    - Add setup instructions
    - Add API documentation
    - Add screenshots/demo
  
  - [x] 18.2 Create API documentation
    - Document all endpoints
    - Add request/response examples
    - Create Postman collection
  
  - [x] 18.3 Write deployment guide
    - Document local setup
    - Document Docker setup
    - Document testing procedures

- [x] 19. Final checkpoint - Integration testing
  - Run complete test suite
  - Test Docker deployment
  - Verify all features work end-to-end
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation
- The system runs completely offline using Hardhat local blockchain
- Redis is required for rate limiting and caching
- All blockchain operations use Web3.py to interact with smart contracts
