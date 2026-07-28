# Complete Setup Guide - MediChain Blockchain Healthcare Security System

This is the complete step-by-step guide to run the MediChain blockchain healthcare security system on your machine.

## 🎯 System Overview

MediChain is a blockchain-integrated healthcare security system that provides:
- **Universal Patient Identification** across hospital branches
- **Advanced DDoS Protection** with multi-factor threat scoring
- **Real-time Security Monitoring** with blockchain-based IP blocklist
- **CAPTCHA Challenges** for suspicious requests
- **Automated IP Blocking** for high-threat scores

## 📋 Prerequisites

Before starting, ensure you have these installed:

### Required Software:
1. **Python 3.11+** - [Download here](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download here](https://nodejs.org/)
3. **Redis Server** - [Download here](https://redis.io/download)
4. **Git** - [Download here](https://git-scm.com/)

### Verify Installation:
```bash
python --version    # Should show 3.11+
node --version      # Should show 18+
git --version       # Should show git version
```

## 🚀 Complete Setup Process

### Step 1: Clone and Navigate to Project
```bash
git clone <repository-url>
cd caregrid
```

### Step 2: Install Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Install Blockchain Dependencies
```bash
cd caregrid_chain
npm install
cd ..
```

### Step 4: Create Required Directories
```bash
mkdir -p logs
mkdir -p caregrid_chain/deployments
```

### Step 5: Setup Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

## 🔧 Running the System

You need to start **4 services** in separate terminals. Follow this exact order:

### Terminal 1: Start Redis Server
```bash
# Windows (if installed via installer):
"C:\Program Files\Redis\redis-server.exe"

# Linux:
redis-server

# macOS:
redis-server

# Verify Redis is running:
redis-cli ping
# Should return: PONG
```

### Terminal 2: Start Blockchain Network
```bash
cd caregrid_chain
npx hardhat node

# Keep this terminal open - you should see:
# Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/
```

### Terminal 3: Deploy Smart Contracts
```bash
# In a new terminal, deploy contracts:
cd caregrid_chain
npx hardhat run scripts/deploy-all.ts --network localhost

# Then update Django settings:
cd ..
python scripts/update_contract_addresses.py
```

### Terminal 4: Start Django Server
```bash
python manage.py runserver

# You should see:
# Starting development server at http://127.0.0.1:8000/
```

## ✅ Verification Steps

### 1. Check All Services Are Running
- **Redis**: `redis-cli ping` → Should return `PONG`
- **Blockchain**: Visit http://127.0.0.1:8545 → Should show Hardhat JSON-RPC
- **Django**: Visit http://127.0.0.1:8000 → Should show Django page
- **Admin Panel**: Visit http://127.0.0.1:8000/admin → Should show login page

### 2. Test API Endpoints
```bash
# Test patient endpoint (should require authentication)
curl http://127.0.0.1:8000/api/patients/

# Test security dashboard
curl http://127.0.0.1:8000/api/security/dashboard/
```

### 3. Check Logs
```bash
# Check Django logs
tail -f logs/caregrid.log

# Look for these success messages:
# - "Redis connection established"
# - "Connected to blockchain network"
# - "SecurityMiddleware initialized"
```

## 🧪 Testing the System

### Run Python Tests
```bash
# All tests
pytest

# With coverage report
pytest --cov=core --cov=firewall --cov-report=html

# Property-based tests only
pytest tests/property/ -v

# Unit tests only
pytest tests/unit/ -v
```

### Run Smart Contract Tests
```bash
cd caregrid_chain
npx hardhat test
```

### Load Test Data (Optional)
```bash
python setup_test_data.py
```

## 🔍 System Features Demo

### 1. Patient Registration
```bash
curl -X POST http://127.0.0.1:8000/api/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "date_of_birth": "1990-01-15",
    "gender": "M",
    "contact_phone": "+1234567890",
    "contact_email": "john.doe@email.com",
    "address": "123 Main St, City, State 12345"
  }'
```

### 2. Security Features Test
```bash
# Generate multiple requests to trigger security middleware
for i in {1..50}; do
  curl -s http://127.0.0.1:8000/api/patients/ > /dev/null &
done
wait

# Check security dashboard
curl http://127.0.0.1:8000/api/security/dashboard/
```

### 3. Blockchain Integration Test
```bash
cd caregrid_chain
npx hardhat console --network localhost

# In Hardhat console:
const registry = await ethers.getContractAt("PatientRegistry", "DEPLOYED_ADDRESS");
const patientCount = await registry.getPatientCount();
console.log("Total patients:", patientCount.toString());
```

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MediChain System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Hospital A    │    │   Hospital B    │    │ Hospital C  │  │
│  │  Django Server  │    │  Django Server  │    │Django Server│  │
│  └─────────┬───────┘    └─────────┬───────┘    └──────┬──────┘  │
│            │                      │                   │         │
│            └──────────────────────┼───────────────────┘         │
│                                   │                             │
│  ┌─────────────────────────────────┼─────────────────────────────┐  │
│  │              Shared Infrastructure                          │  │
│  │                                 │                          │  │
│  │  ┌─────────────┐    ┌──────────▼──────────┐    ┌─────────┐ │  │
│  │  │    Redis    │    │   Hardhat Network   │    │  Logs   │ │  │
│  │  │   Cache     │    │  (Local Blockchain) │    │ Storage │ │  │
│  │  │             │    │                     │    │         │ │  │
│  │  │ • Rate      │    │ • PatientRegistry   │    │ • Audit │ │  │
│  │  │   Limiting  │    │ • BlockedIPRegistry │    │ • Debug │ │  │
│  │  │ • Request   │    │ • AttackSignature   │    │ • Error │ │  │
│  │  │   Tracking  │    │   Registry          │    │         │ │  │
│  │  └─────────────┘    └─────────────────────┘    └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🛡️ Security Features

### Threat Scoring Algorithm
The system calculates threat scores (0-100) based on:

1. **Rate Score (0-20)**: Request frequency per IP
2. **Pattern Score (0-25)**: Endpoint repetition ratio  
3. **Session Score (0-20)**: Cookie/authentication presence
4. **Entropy Score (0-15)**: User-Agent variety
5. **Auth Failure Score (0-10)**: Failed login attempts
6. **Signature Match (0-30)**: Known attack pattern match

### Response Actions:
- **Score < 40**: Allow request (Low threat)
- **Score 40-59**: Require CAPTCHA (Medium threat)
- **Score 60-79**: Block request (High threat)
- **Score ≥ 80**: Auto-block IP on blockchain (Critical threat)

## 🔧 Configuration

### Key Settings (caregrid/settings.py):
```python
# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Blockchain Configuration  
BLOCKCHAIN_PROVIDER_URL = 'http://127.0.0.1:8545'

# Security Thresholds
THREAT_SCORE_THRESHOLDS = {
    'LOW': 0,     # < 40 is LOW threat
    'MEDIUM': 40, # 40-60 is MEDIUM threat  
    'HIGH': 61,   # > 60 is HIGH threat
}

# Rate Limits
RATE_LIMITS = {
    'UNAUTHENTICATED': 100,  # requests per minute
    'AUTHENTICATED': 500,     # requests per minute
}
```

## 🚨 Troubleshooting

### Common Issues and Solutions:

#### 1. Redis Connection Error
**Error**: `Error 10061 connecting to localhost:6379`
**Solution**: 
- Start Redis server: `redis-server` or `"C:\Program Files\Redis\redis-server.exe"`
- Verify with: `redis-cli ping`

#### 2. Blockchain Connection Error  
**Error**: `Could not connect to blockchain`
**Solution**:
- Start Hardhat: `cd caregrid_chain && npx hardhat node`
- Check http://127.0.0.1:8545 is accessible

#### 3. Contract Not Deployed
**Error**: `Contract addresses are empty`
**Solution**:
- Deploy contracts: `cd caregrid_chain && npx hardhat run scripts/deploy-all.ts --network localhost`
- Update settings: `python scripts/update_contract_addresses.py`

#### 4. Port Already in Use
**Error**: `EADDRINUSE: address already in use :::8545`
**Solution**:
- Kill existing process: `pkill -f 'hardhat node'` (Linux/macOS)
- Or restart your computer

#### 5. Python Module Not Found
**Error**: `ModuleNotFoundError: No module named 'web3'`
**Solution**:
- Activate virtual environment: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
- Install dependencies: `pip install -r requirements.txt`

## 📚 API Documentation

### Key Endpoints:

#### Patient Management:
- `POST /api/patients/` - Register new patient
- `GET /api/patients/` - List all patients  
- `GET /api/patients/{id}/` - Get patient details

#### Appointments:
- `POST /api/appointments/` - Create appointment
- `GET /api/appointments/` - List appointments

#### Security:
- `GET /api/security/dashboard/` - Security metrics
- `POST /api/security/block/` - Manually block IP
- `POST /api/security/unblock/` - Unblock IP

#### Authentication:
- `POST /api/auth/login/` - User login
- `GET /api/auth/user/` - Current user info

### Example API Calls:

#### Register Patient:
```bash
curl -X POST http://127.0.0.1:8000/api/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "date_of_birth": "1985-03-15", 
    "gender": "F",
    "contact_phone": "+1555123456",
    "contact_email": "alice@email.com",
    "address": "456 Oak Ave, Springfield, IL"
  }'
```

#### Check Security Dashboard:
```bash
curl http://127.0.0.1:8000/api/security/dashboard/
```

## 🔄 Development Workflow

### Daily Development:
1. Start all services (Redis, Blockchain, Django)
2. Make code changes
3. Run tests: `pytest`
4. Check logs: `tail -f logs/caregrid.log`

### After Contract Changes:
1. Redeploy: `cd caregrid_chain && npx hardhat run scripts/deploy-all.ts --network localhost`
2. Update settings: `python scripts/update_contract_addresses.py`
3. Restart Django: `python manage.py runserver`

## 📁 Project Structure

```
caregrid/
├── caregrid/              # Django project settings
│   └── settings.py        # Main configuration
├── caregrid_chain/        # Blockchain layer
│   ├── contracts/         # Smart contracts (.sol files)
│   ├── scripts/           # Deployment scripts
│   ├── test/              # Contract tests
│   └── deployments/       # Deployed addresses
├── core/                  # Core app (patients, security)
│   ├── models.py          # Database models
│   ├── views.py           # API endpoints
│   ├── middleware.py      # Security middleware
│   ├── blockchain_service.py # Blockchain integration
│   └── threat_calculator.py  # Threat scoring
├── users/                 # User management
├── firewall/              # Security monitoring
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── property/          # Property-based tests
│   └── integration/       # Integration tests
├── scripts/               # Utility scripts
├── logs/                  # Application logs
└── requirements.txt       # Python dependencies
```

## 🎯 Success Indicators

When everything is working correctly, you should see:

### In Django Logs:
```
INFO middleware Redis connection established
INFO blockchain_service Connected to blockchain network. Latest block: X
INFO middleware SecurityMiddleware initialized
```

### In Browser:
- http://127.0.0.1:8000 → Django welcome page
- http://127.0.0.1:8000/admin → Admin login page
- http://127.0.0.1:8000/api/patients/ → Authentication required message

### Performance:
- API responses under 200ms
- Security middleware processing requests
- Threat scores being calculated and logged

## 🎉 You're Ready!

Once all services are running and tests pass, your MediChain system is fully operational with:

✅ **Universal Patient IDs** stored on blockchain  
✅ **Real-time Threat Detection** with multi-factor scoring  
✅ **Automated IP Blocking** for high-threat requests  
✅ **CAPTCHA Challenges** for suspicious activity  
✅ **Security Dashboard** for monitoring  
✅ **Cross-branch Data Sharing** via blockchain  

The system is now ready for production use or further development!

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Review logs in `logs/caregrid.log`
3. Run verification: `python scripts/verify_setup.py`
4. Check existing documentation in the project

---

**Built with Django, Web3.py, Hardhat, and Redis** 🚀