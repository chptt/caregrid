# Requirements Document

## Introduction

MediChain is a blockchain-based healthcare security system that provides universal patient identification across multiple hospital branches and implements advanced DDoS attack detection and prevention. The system combines traditional healthcare management with distributed ledger technology to create an immutable patient registry and a decentralized security intelligence network that protects against sophisticated distributed attacks.

## Glossary

- **System**: The complete MediChain application including Django backend, blockchain smart contracts, and security monitoring components
- **Patient_Registry**: Blockchain-based smart contract that stores universal patient identifiers
- **Security_Monitor**: Component that analyzes request patterns and calculates threat scores
- **Threat_Score**: Numerical value (0-100) representing the likelihood that a request is malicious
- **IP_Blocklist**: Blockchain-based registry of blocked IP addresses shared across all branches
- **Branch**: Individual hospital location with its own Django instance connected to shared blockchain
- **Universal_Patient_ID**: Unique blockchain-generated identifier for each patient, usable across all healthcare facilities
- **Request_Pattern**: Sequence of API requests analyzed for behavioral characteristics
- **Anomaly_Detector**: Component that identifies unusual request behaviors indicative of attacks
- **CAPTCHA_Challenge**: Human verification mechanism triggered for suspicious requests
- **Attack_Signature**: Characteristic pattern of a DDoS attack shared via blockchain

## Requirements

### Requirement 1: Universal Patient Identification

**User Story:** As a patient, I want a single unique ID that works across all hospital branches, so that my medical records are accessible wherever I receive care.

#### Acceptance Criteria

1. WHEN a new patient registers, THE Patient_Registry SHALL generate a unique blockchain-based patient ID
2. WHEN a patient ID is created, THE Patient_Registry SHALL store the ID hash on the blockchain to ensure immutability
3. WHEN a patient visits any branch, THE System SHALL retrieve patient information using the universal patient ID
4. THE Patient_Registry SHALL ensure no duplicate patient IDs can be created
5. WHEN patient data is accessed, THE System SHALL maintain privacy by storing only hashed identifiers on-chain

### Requirement 2: Multi-Factor DDoS Detection

**User Story:** As a security administrator, I want the system to detect DDoS attacks using multiple behavioral factors, so that sophisticated distributed attacks are identified even when coming from many different IPs.

#### Acceptance Criteria

1. WHEN analyzing incoming requests, THE Security_Monitor SHALL calculate a threat score based on at least 5 behavioral factors
2. WHEN request rate from a single IP exceeds 100 requests per minute, THE Security_Monitor SHALL add 20 points to the threat score
3. WHEN request pattern shows more than 80% requests to the same endpoint, THE Security_Monitor SHALL add 25 points to the threat score
4. WHEN a request has no session cookies or authentication, THE Security_Monitor SHALL add 20 points to the threat score
5. WHEN User-Agent entropy is below 2.0, THE Security_Monitor SHALL add 15 points to the threat score
6. WHEN failed authentication attempts exceed 5 within 10 minutes, THE Security_Monitor SHALL add 10 points to the threat score
7. WHEN threat score exceeds 60, THE System SHALL classify the request as high threat
8. WHEN threat score is between 40 and 60, THE System SHALL classify the request as medium threat and require CAPTCHA
9. WHEN threat score is below 40, THE System SHALL classify the request as low threat and allow normal processing

### Requirement 3: Real-Time Request Monitoring

**User Story:** As a security administrator, I want to monitor all incoming requests in real-time, so that I can observe attack patterns as they develop.

#### Acceptance Criteria

1. WHEN a request is received, THE System SHALL log the IP address, timestamp, endpoint, and User-Agent
2. WHEN requests are logged, THE System SHALL store them in a time-series format for pattern analysis
3. WHEN monitoring requests, THE System SHALL track request counts per IP per minute
4. WHEN monitoring requests, THE System SHALL calculate pattern metrics including endpoint diversity and request intervals
5. THE System SHALL retain request logs for at least 24 hours for analysis

### Requirement 4: Blockchain-Based IP Blocklist

**User Story:** As a security administrator, I want blocked IPs to be shared across all hospital branches via blockchain, so that an attack detected at one branch is automatically blocked at all branches.

#### Acceptance Criteria

1. WHEN an IP is identified as malicious, THE System SHALL write the IP address to the blockchain IP_Blocklist
2. WHEN an IP is added to the blocklist, THE IP_Blocklist SHALL record the blocking timestamp and reason
3. WHEN a request arrives, THE System SHALL check the IP against the blockchain IP_Blocklist before processing
4. WHEN an IP is found in the blocklist, THE System SHALL reject the request with a 403 status code
5. WHEN any branch adds an IP to the blocklist, THE System SHALL make it visible to all other branches within 30 seconds
6. WHERE an administrator manually reviews a block, THE System SHALL allow removal of IPs from the blocklist

### Requirement 5: Attack Pattern Recognition

**User Story:** As a security administrator, I want the system to recognize common attack patterns, so that coordinated attacks from multiple IPs are detected.

#### Acceptance Criteria

1. WHEN analyzing requests from multiple IPs, THE Anomaly_Detector SHALL identify common behavioral patterns
2. WHEN 50 or more IPs show identical request patterns within 5 minutes, THE Anomaly_Detector SHALL flag it as a coordinated attack
3. WHEN a coordinated attack is detected, THE System SHALL create an attack signature describing the pattern
4. WHEN an attack signature is created, THE System SHALL store it on the blockchain for cross-branch sharing
5. WHEN requests match a known attack signature, THE System SHALL automatically increase the threat score by 30 points

### Requirement 6: CAPTCHA Challenge System

**User Story:** As a legitimate user, I want to prove I'm human when my activity looks suspicious, so that I'm not permanently blocked for unusual but legitimate behavior.

#### Acceptance Criteria

1. WHEN a request has a medium threat score (40-60), THE System SHALL present a CAPTCHA challenge
2. WHEN a CAPTCHA is successfully completed, THE System SHALL allow the request to proceed
3. WHEN a CAPTCHA fails 3 times, THE System SHALL temporarily block the IP for 15 minutes
4. WHEN a CAPTCHA is completed successfully, THE System SHALL reduce the threat score by 20 points for subsequent requests from that IP
5. THE System SHALL not require CAPTCHA for authenticated users with established session history

### Requirement 7: Security Dashboard

**User Story:** As a security administrator, I want a real-time dashboard showing current threats and system status, so that I can monitor security posture and respond to incidents.

#### Acceptance Criteria

1. WHEN the dashboard loads, THE System SHALL display current request rate across all branches
2. WHEN the dashboard is active, THE System SHALL update threat metrics every 5 seconds
3. WHEN displaying threats, THE System SHALL show the top 10 IPs by threat score
4. WHEN displaying activity, THE System SHALL show a time-series graph of requests per minute for the last hour
5. WHEN an IP is blocked, THE System SHALL display a notification on the dashboard
6. WHERE an administrator views the dashboard, THE System SHALL provide controls to manually block or unblock IPs

### Requirement 8: Patient Management Core Features

**User Story:** As a hospital staff member, I want to manage patient records and appointments, so that I can provide healthcare services efficiently.

#### Acceptance Criteria

1. WHEN a patient is registered, THE System SHALL create a patient record with name, date of birth, contact information, and universal patient ID
2. WHEN creating an appointment, THE System SHALL associate it with a patient using their universal patient ID
3. WHEN viewing patient records, THE System SHALL display appointment history and medical notes
4. WHEN a patient visits multiple branches, THE System SHALL show their complete history from all locations
5. THE System SHALL enforce role-based access control for patient data (doctors, nurses, admin)

### Requirement 9: Smart Contract Integration

**User Story:** As a system architect, I want Django to interact seamlessly with blockchain smart contracts, so that patient IDs and security data are properly synchronized.

#### Acceptance Criteria

1. WHEN the System starts, THE System SHALL connect to the blockchain network using Web3 provider
2. WHEN interacting with smart contracts, THE System SHALL handle transaction confirmations and errors gracefully
3. WHEN writing to blockchain, THE System SHALL wait for transaction confirmation before updating local database
4. WHEN reading from blockchain, THE System SHALL cache results locally to minimize RPC calls
5. IF blockchain connection fails, THEN THE System SHALL log the error and continue operating with cached data

### Requirement 10: API Rate Limiting

**User Story:** As a system administrator, I want API endpoints to have rate limits, so that even legitimate users cannot accidentally overwhelm the system.

#### Acceptance Criteria

1. THE System SHALL enforce a rate limit of 100 requests per minute per IP for unauthenticated requests
2. THE System SHALL enforce a rate limit of 500 requests per minute per user for authenticated requests
3. WHEN rate limit is exceeded, THE System SHALL return HTTP 429 status code with retry-after header
4. THE System SHALL use Redis for distributed rate limiting across multiple server instances
5. WHERE an IP consistently hits rate limits, THE System SHALL increase its threat score

### Requirement 11: Automated Blocking and Unblocking

**User Story:** As a security administrator, I want IPs to be automatically blocked when threat scores are high and automatically unblocked after a cooldown period, so that the system is self-managing.

#### Acceptance Criteria

1. WHEN threat score exceeds 80, THE System SHALL automatically add the IP to the blockchain blocklist
2. WHEN an IP is automatically blocked, THE System SHALL set a 24-hour expiration time
3. WHEN the expiration time is reached, THE System SHALL automatically remove the IP from the blocklist
4. WHERE an administrator manually blocks an IP, THE System SHALL not automatically unblock it
5. WHEN an IP is unblocked, THE System SHALL reset its threat score to 0

### Requirement 12: Cross-Branch Data Synchronization

**User Story:** As a hospital administrator, I want patient data and security intelligence to be synchronized across all branches, so that the system operates as a unified network.

#### Acceptance Criteria

1. WHEN patient data is updated at any branch, THE System SHALL propagate changes to the blockchain within 10 seconds
2. WHEN security events occur, THE System SHALL share attack signatures across branches via blockchain
3. WHEN a new branch joins the network, THE System SHALL synchronize with existing blockchain data
4. THE System SHALL ensure eventual consistency across all branches for patient records
5. IF a branch goes offline, THEN THE System SHALL queue updates and synchronize when connection is restored
