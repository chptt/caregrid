# Security Dashboard API Documentation

This document describes the security dashboard API endpoints implemented for the MediChain blockchain healthcare security system.

## Endpoints

### 1. Security Dashboard
**GET** `/api/security/dashboard/`

Returns comprehensive security dashboard data including current request rate, top threats, time-series data, and blocked IPs count.

**Response:**
```json
{
  "current_request_rate": 15,
  "top_threats": [
    {
      "ip_address": "192.168.1.100",
      "threat_score": 85,
      "request_count": 45,
      "latest_action": "blocked"
    }
  ],
  "time_series_data": [
    {
      "timestamp": "2026-01-19T16:55:00Z",
      "request_count": 12
    }
  ],
  "blocked_ips_count": 3,
  "recent_attack_patterns": [
    {
      "pattern_hash": "0x1234...",
      "severity": 8,
      "ip_count": 25,
      "request_count": 500,
      "detected_at": "2026-01-19T16:30:00Z",
      "blockchain_synced": true
    }
  ],
  "threat_distribution": {
    "low": 120,
    "medium": 45,
    "high": 12
  },
  "last_updated": "2026-01-19T17:00:00Z"
}
```

### 2. Security Statistics
**GET** `/api/security/stats/`

Returns basic security statistics for quick overview.

**Response:**
```json
{
  "total_requests_24h": 1250,
  "blocked_requests_24h": 45,
  "captcha_challenges_24h": 78,
  "active_blocked_ips": 5,
  "attack_patterns_detected": 2
}
```

### 3. Admin Block IP
**POST** `/api/security/block/`

Manually block an IP address with admin privileges. Updates both blockchain and local database.

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "reason": "Manual block by admin",
  "duration_hours": 24
}
```

**Response:**
```json
{
  "success": true,
  "message": "IP 192.168.1.100 has been blocked",
  "blocked_ip": {
    "ip_address": "192.168.1.100",
    "expiry_time": "2026-01-20T17:00:00Z",
    "reason": "Manual block by admin",
    "blockchain_synced": true,
    "tx_hash": "0xabc123..."
  }
}
```

### 4. Admin Unblock IP
**POST** `/api/security/unblock/`

Manually unblock an IP address with admin privileges. Updates both blockchain and local database.

**Request Body:**
```json
{
  "ip_address": "192.168.1.100"
}
```

**Response:**
```json
{
  "success": true,
  "message": "IP 192.168.1.100 has been unblocked",
  "unblocked_ip": {
    "ip_address": "192.168.1.100",
    "original_expiry": "2026-01-20T17:00:00Z",
    "reason": "Manual block by admin",
    "blockchain_synced": true,
    "tx_hash": "0xdef456..."
  }
}
```

### 5. Blocked IPs List
**GET** `/api/security/blocked/`

Returns list of currently blocked IP addresses.

**Response:**
```json
{
  "blocked_ips": [
    {
      "ip_address": "192.168.1.100",
      "block_time": "2026-01-19T17:00:00Z",
      "expiry_time": "2026-01-20T17:00:00Z",
      "reason": "High threat score: 85",
      "is_manual": false,
      "blocked_by": null,
      "blockchain_synced": true
    }
  ],
  "total_count": 1
}
```

## Features

- **Real-time monitoring**: Dashboard updates with current request rates and threat levels
- **Blockchain integration**: All block/unblock operations are synchronized with the blockchain
- **Time-series data**: Historical request data for trend analysis
- **Top threats tracking**: Identifies highest-risk IP addresses
- **Manual admin controls**: Administrators can manually block/unblock IPs
- **Attack pattern detection**: Shows detected coordinated attack patterns

## Requirements Satisfied

- **7.1**: Dashboard displays current request rate across all branches
- **7.3**: Shows top 10 IPs by threat score
- **7.4**: Provides time-series graph data for requests per minute
- **4.6**: Manual block/unblock functionality for administrators
- **7.6**: Admin controls for IP management

## Usage Example

```bash
# Get dashboard data
curl -X GET http://localhost:8000/api/security/dashboard/

# Block an IP manually
curl -X POST http://localhost:8000/api/security/block/ \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "203.0.113.100", "reason": "Suspicious activity", "duration_hours": 12}'

# Unblock an IP
curl -X POST http://localhost:8000/api/security/unblock/ \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "203.0.113.100"}'

# Get blocked IPs list
curl -X GET http://localhost:8000/api/security/blocked/
```

## Notes

- All endpoints return JSON responses
- Block/unblock operations are synchronized with the blockchain
- Redis connection warnings are expected if Redis is not running (caching will be disabled)
- The system continues to function without Redis, but with reduced performance
- All timestamps are in ISO 8601 format