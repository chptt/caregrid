# MediChain API Documentation

## Overview

The MediChain API provides endpoints for patient management, appointment scheduling, and security monitoring. All endpoints return JSON responses and use standard HTTP status codes.

**Base URL:** `http://127.0.0.1:8000`

## Authentication

Most endpoints require authentication using JWT tokens.

### Login
```http
POST /api/auth/login/
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "administrator"
  }
}
```

### Using Authentication
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Patient Management

### Register New Patient

Creates a new patient record and registers their universal ID on the blockchain.

```http
POST /api/patients/
```

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (required)

**Request Body:**
```json
{
  "name": "string (required, max 100 chars)",
  "date_of_birth": "YYYY-MM-DD (required)",
  "gender": "M|F|O (required)",
  "contact_phone": "string (required, max 20 chars)",
  "contact_email": "email (required)",
  "address": "string (required)"
}
```

**Example Request:**
```json
{
  "name": "Alice Johnson",
  "date_of_birth": "1985-03-15",
  "gender": "F",
  "contact_phone": "+1555123456",
  "contact_email": "alice.johnson@email.com",
  "address": "456 Oak Avenue, Springfield, IL 62701"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "date_of_birth": "1985-03-15",
  "gender": "F",
  "contact_phone": "+1555123456",
  "contact_email": "alice.johnson@email.com",
  "address": "456 Oak Avenue, Springfield, IL 62701",
  "blockchain_id": "0x8f4b2c1a9e7d6f3b2a8c5e9f1d4a7b2c8e5f9a1d3b6c9e2f5a8b1c4d7e0f3a6b9c",
  "blockchain_registered": true,
  "registration_tx_hash": "0x1234567890abcdef...",
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data provided
- `401 Unauthorized`: Authentication required
- `409 Conflict`: Patient with same email already exists

### Get Patient Details

Retrieves detailed information about a specific patient, including appointment history.

```http
GET /api/patients/{id}/
```

**Path Parameters:**
- `id` (integer): Patient ID

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "date_of_birth": "1985-03-15",
  "gender": "F",
  "contact_phone": "+1555123456",
  "contact_email": "alice.johnson@email.com",
  "address": "456 Oak Avenue, Springfield, IL 62701",
  "blockchain_id": "0x8f4b2c1a9e7d6f3b2a8c5e9f1d4a7b2c8e5f9a1d3b6c9e2f5a8b1c4d7e0f3a6b9c",
  "blockchain_registered": true,
  "appointments": [
    {
      "id": 1,
      "date": "2024-01-25",
      "time": "10:00:00",
      "doctor": "Dr. Sarah Wilson",
      "department": "General Medicine",
      "notes": "Regular checkup",
      "created_at": "2024-01-15T14:35:00Z"
    }
  ],
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Patient not found

### List All Patients

Retrieves a paginated list of all patients.

```http
GET /api/patients/
```

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20, max: 100)
- `search` (string, optional): Search by name or email
- `gender` (string, optional): Filter by gender (M, F, O)
- `created_after` (date, optional): Filter by creation date (YYYY-MM-DD)

**Example Request:**
```http
GET /api/patients/?page=1&page_size=10&search=alice&gender=F
```

**Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "date_of_birth": "1985-03-15",
      "gender": "F",
      "contact_email": "alice.johnson@email.com",
      "blockchain_id": "0x8f4b2c1a9e7d6f3b...",
      "blockchain_registered": true,
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### Search Patient by Blockchain ID

Finds a patient using their universal blockchain ID.

```http
GET /api/patients/search/
```

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `blockchain_id` (string, required): The patient's blockchain ID

**Example Request:**
```http
GET /api/patients/search/?blockchain_id=0x8f4b2c1a9e7d6f3b2a8c5e9f1d4a7b2c8e5f9a1d3b6c9e2f5a8b1c4d7e0f3a6b9c
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "blockchain_id": "0x8f4b2c1a9e7d6f3b2a8c5e9f1d4a7b2c8e5f9a1d3b6c9e2f5a8b1c4d7e0f3a6b9c",
  "blockchain_registered": true
}
```

## Appointment Management

### Create Appointment

Creates a new appointment for a patient.

```http
POST /api/appointments/
```

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (required)

**Request Body:**
```json
{
  "patient_id": "integer (required)",
  "date": "YYYY-MM-DD (required)",
  "time": "HH:MM:SS (required)",
  "doctor": "string (required, max 100 chars)",
  "department": "string (required, max 100 chars)",
  "notes": "string (optional)"
}
```

**Example Request:**
```json
{
  "patient_id": 1,
  "date": "2024-01-25",
  "time": "10:00:00",
  "doctor": "Dr. Sarah Wilson",
  "department": "General Medicine",
  "notes": "Regular checkup - patient reports feeling well"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "patient": {
    "id": 1,
    "name": "Alice Johnson",
    "blockchain_id": "0x8f4b2c1a9e7d6f3b..."
  },
  "date": "2024-01-25",
  "time": "10:00:00",
  "doctor": "Dr. Sarah Wilson",
  "department": "General Medicine",
  "notes": "Regular checkup - patient reports feeling well",
  "created_at": "2024-01-15T14:35:00Z",
  "updated_at": "2024-01-15T14:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data or patient not found
- `401 Unauthorized`: Authentication required

### List Appointments

Retrieves a paginated list of appointments with filtering options.

```http
GET /api/appointments/
```

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20)
- `patient_id` (integer, optional): Filter by patient ID
- `date` (date, optional): Filter by appointment date (YYYY-MM-DD)
- `date_from` (date, optional): Filter appointments from date
- `date_to` (date, optional): Filter appointments to date
- `doctor` (string, optional): Filter by doctor name
- `department` (string, optional): Filter by department

**Example Request:**
```http
GET /api/appointments/?patient_id=1&date_from=2024-01-01&date_to=2024-01-31
```

**Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": {
        "id": 1,
        "name": "Alice Johnson",
        "blockchain_id": "0x8f4b2c1a9e7d6f3b..."
      },
      "date": "2024-01-25",
      "time": "10:00:00",
      "doctor": "Dr. Sarah Wilson",
      "department": "General Medicine",
      "created_at": "2024-01-15T14:35:00Z"
    }
  ]
}
```

### Get Appointment Details

Retrieves detailed information about a specific appointment.

```http
GET /api/appointments/{id}/
```

**Path Parameters:**
- `id` (integer): Appointment ID

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response (200 OK):**
```json
{
  "id": 1,
  "patient": {
    "id": 1,
    "name": "Alice Johnson",
    "blockchain_id": "0x8f4b2c1a9e7d6f3b...",
    "contact_phone": "+1555123456"
  },
  "date": "2024-01-25",
  "time": "10:00:00",
  "doctor": "Dr. Sarah Wilson",
  "department": "General Medicine",
  "notes": "Regular checkup - patient reports feeling well",
  "created_at": "2024-01-15T14:35:00Z",
  "updated_at": "2024-01-15T14:35:00Z"
}
```

## Security Dashboard

### Get Security Metrics

Retrieves real-time security metrics and threat information.

```http
GET /api/security/dashboard/
```

**Headers:**
- `Authorization: Bearer <token>` (required, admin role)

**Response (200 OK):**
```json
{
  "current_request_rate": 45.2,
  "total_requests_last_hour": 2710,
  "blocked_ips_count": 12,
  "active_threats_count": 3,
  "top_threats": [
    {
      "ip_address": "192.168.1.100",
      "threat_score": 85,
      "threat_level": "HIGH",
      "request_count": 150,
      "last_seen": "2024-01-15T10:25:00Z",
      "factors": {
        "rate_score": 20,
        "pattern_score": 25,
        "session_score": 20,
        "entropy_score": 15,
        "auth_failure_score": 5
      }
    }
  ],
  "time_series": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "requests_per_minute": 42,
      "threat_events": 2
    },
    {
      "timestamp": "2024-01-15T10:01:00Z",
      "requests_per_minute": 38,
      "threat_events": 1
    }
  ],
  "recent_blocks": [
    {
      "ip_address": "10.0.0.50",
      "blocked_at": "2024-01-15T09:45:00Z",
      "reason": "Auto-blocked: threat score 82",
      "expires_at": "2024-01-16T09:45:00Z"
    }
  ]
}
```

### Manually Block IP

Manually adds an IP address to the blockchain blocklist.

```http
POST /api/security/block/
```

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (required, admin role)

**Request Body:**
```json
{
  "ip_address": "string (required, valid IP)",
  "reason": "string (required)",
  "duration_hours": "integer (optional, default: 24)"
}
```

**Example Request:**
```json
{
  "ip_address": "192.168.1.100",
  "reason": "Suspicious activity detected by security team",
  "duration_hours": 48
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "IP blocked successfully",
  "ip_address": "192.168.1.100",
  "blockchain_tx": "0xabcdef1234567890...",
  "blocked_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-17T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid IP address or data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Admin role required
- `409 Conflict`: IP already blocked

### Unblock IP

Removes an IP address from the blockchain blocklist.

```http
POST /api/security/unblock/
```

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (required, admin role)

**Request Body:**
```json
{
  "ip_address": "string (required, valid IP)"
}
```

**Example Request:**
```json
{
  "ip_address": "192.168.1.100"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "IP unblocked successfully",
  "ip_address": "192.168.1.100",
  "blockchain_tx": "0x1234567890abcdef...",
  "unblocked_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid IP address
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Admin role required
- `404 Not Found`: IP not currently blocked

### Get Security Logs

Retrieves paginated security event logs.

```http
GET /api/security/logs/
```

**Headers:**
- `Authorization: Bearer <token>` (required, admin role)

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 50)
- `ip_address` (string, optional): Filter by IP address
- `threat_level` (string, optional): Filter by threat level (LOW, MEDIUM, HIGH)
- `date_from` (datetime, optional): Filter from date (ISO format)
- `date_to` (datetime, optional): Filter to date (ISO format)

**Response (200 OK):**
```json
{
  "count": 150,
  "next": "http://127.0.0.1:8000/api/security/logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "ip_address": "192.168.1.100",
      "threat_score": 85,
      "threat_level": "HIGH",
      "endpoint": "/api/patients/",
      "method": "GET",
      "user_agent": "Mozilla/5.0...",
      "action_taken": "blocked",
      "timestamp": "2024-01-15T10:25:00Z",
      "factors": {
        "rate_score": 20,
        "pattern_score": 25,
        "session_score": 20,
        "entropy_score": 15,
        "auth_failure_score": 5
      }
    }
  ]
}
```

## CAPTCHA System

### Generate CAPTCHA

Generates a new CAPTCHA challenge for suspicious requests.

```http
GET /api/captcha/generate/
```

**Response (200 OK):**
```json
{
  "captcha_id": "abc123def456",
  "image_url": "/api/captcha/image/abc123def456/",
  "expires_in": 300
}
```

### Verify CAPTCHA

Verifies a CAPTCHA response.

```http
POST /api/captcha/verify/
```

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "captcha_id": "string (required)",
  "response": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "captcha_token_for_subsequent_requests"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid CAPTCHA response"
}
```

## Error Handling

### Standard HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied (blocked IP or insufficient permissions)
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `429 Too Many Requests`: Rate limit exceeded or CAPTCHA required
- `500 Internal Server Error`: Server error

### Rate Limiting Response

When rate limits are exceeded:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "current_rate": "120 requests/minute",
  "limit": "100 requests/minute"
}
```

### CAPTCHA Required Response

When CAPTCHA verification is required:

```json
{
  "error": "CAPTCHA required",
  "reason": "Suspicious activity detected",
  "threat_score": 45,
  "captcha_url": "/api/captcha/generate/"
}
```

### Blocked IP Response

When requests come from blocked IPs:

```json
{
  "error": "Access denied",
  "reason": "IP blocked due to security policy",
  "blocked_at": "2024-01-15T09:45:00Z",
  "blocked_until": "2024-01-16T09:45:00Z",
  "block_reason": "Auto-blocked: threat score 82"
}
```

### Validation Error Response

When request data is invalid:

```json
{
  "error": "Validation failed",
  "details": {
    "name": ["This field is required."],
    "date_of_birth": ["Enter a valid date."],
    "contact_email": ["Enter a valid email address."]
  }
}
```

## Rate Limits

### Default Limits

- **Unauthenticated requests**: 100 requests per minute per IP
- **Authenticated requests**: 500 requests per minute per user
- **Admin requests**: 1000 requests per minute per user

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Webhooks (Future Feature)

### Security Event Webhook

When significant security events occur, the system can send webhooks to configured endpoints.

**Event Types:**
- `ip_blocked`: IP address was blocked
- `attack_detected`: Coordinated attack detected
- `high_threat`: High threat score detected

**Webhook Payload:**
```json
{
  "event": "ip_blocked",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "ip_address": "192.168.1.100",
    "threat_score": 85,
    "reason": "Auto-blocked: threat score 85",
    "blockchain_tx": "0xabcdef1234567890..."
  }
}
```

## SDK Examples

### Python SDK Example

```python
import requests

class MediChainAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def register_patient(self, patient_data):
        response = requests.post(
            f'{self.base_url}/api/patients/',
            json=patient_data,
            headers=self.headers
        )
        return response.json()
    
    def get_security_dashboard(self):
        response = requests.get(
            f'{self.base_url}/api/security/dashboard/',
            headers=self.headers
        )
        return response.json()

# Usage
api = MediChainAPI('http://127.0.0.1:8000', 'your_token_here')
patient = api.register_patient({
    'name': 'John Doe',
    'date_of_birth': '1990-01-01',
    'gender': 'M',
    'contact_phone': '+1234567890',
    'contact_email': 'john@example.com',
    'address': '123 Main St'
})
```

### JavaScript SDK Example

```javascript
class MediChainAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async registerPatient(patientData) {
        const response = await fetch(`${this.baseUrl}/api/patients/`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(patientData)
        });
        return response.json();
    }
    
    async getSecurityDashboard() {
        const response = await fetch(`${this.baseUrl}/api/security/dashboard/`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const api = new MediChainAPI('http://127.0.0.1:8000', 'your_token_here');
const patient = await api.registerPatient({
    name: 'Jane Doe',
    date_of_birth: '1985-05-15',
    gender: 'F',
    contact_phone: '+1987654321',
    contact_email: 'jane@example.com',
    address: '456 Oak Ave'
});
```

## Testing the API

### Using curl

```bash
# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | \
  jq -r '.token')

# Register patient
curl -X POST http://127.0.0.1:8000/api/patients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Patient",
    "date_of_birth": "1990-01-01",
    "gender": "M",
    "contact_phone": "+1234567890",
    "contact_email": "test@example.com",
    "address": "123 Test St"
  }'

# Get security dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/security/dashboard/
```

### Using Postman

Import the Postman collection (see next section) for a complete set of API requests with examples.

---

For more information, see the [main README](README.md) or contact the development team.