# MediChain Setup Guide

This guide will help you set up the MediChain blockchain healthcare security system on your local machine.

## Prerequisites

Before starting, ensure you have the following installed:

1. **Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **Node.js 18+**
   - Download from: https://nodejs.org/
   - Verify: `node --version`

3. **Redis**
   - **Ubuntu/Debian**: `sudo apt-get install redis-server`
   - **macOS**: `brew install redis`
   - **Windows**: Download from https://redis.io/download or use WSL
   - Verify: `redis-server --version`

4. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/

## Quick Start

### Option 1: Automated Setup (Recommended)

#### Linux/macOS:
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run setup script
./scripts/setup.sh

# Start Redis (in a separate terminal)
redis-server

# Start blockchain (in a separate terminal)
./scripts/start-blockchain.sh

# Update Django settings with contract addresses
python3 scripts/update_contract_addresses.py

# Start Django server
python3 manage.py runserver
```

#### Windows:
```cmd
# Run setup script
scripts\setup.bat

# Start Redis (download and install from https://redis.io/download)
# Or use WSL: wsl redis-server

# Start blockchain (in a separate terminal)
scripts\start-blockchain.bat

# Update Django settings with contract addresses
python scripts\update_contract_addresses.py

# Start Django server
python manage.py runserver
```

### Option 2: Manual Setup

#### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Install Blockchain Dependencies
```bash
cd caregrid_chain
npm install
cd ..
```

#### 3. Create Necessary Directories
```bash
mkdir -p logs
mkdir -p caregrid_chain/deployments
```

#### 4. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 5. Start Redis
```bash
# Linux/macOS
redis-server

# Windows (after installation)
redis-server.exe
```

#### 6. Start Hardhat Blockchain
```bash
cd caregrid_chain
npx hardhat node
```

Keep this terminal open - the blockchain needs to run continuously.

#### 7. Deploy Smart Contracts (in a new terminal)
```bash
cd caregrid_chain
npx hardhat run scripts/deploy-all.ts --network localhost
cd ..
```

#### 8. Update Django Settings
```bash
python scripts/update_contract_addresses.py
```

#### 9. Start Django Server
```bash
python manage.py runserver
```

## Verification

After setup, verify everything is working:

1. **Redis**: `redis-cli ping` should return `PONG`
2. **Blockchain**: Visit http://127.0.0.1:8545 (should show Hardhat node)
3. **Django**: Visit http://127.0.0.1:8000 (should show Django welcome page)
4. **Contracts**: Check `caregrid_chain/deployments/all-contracts.json` for deployed addresses

## Project Structure

```
caregrid/
├── caregrid/              # Django project settings
├── caregrid_chain/        # Blockchain contracts and scripts
│   ├── contracts/         # Solidity smart contracts
│   ├── scripts/           # Deployment scripts
│   ├── deployments/       # Deployed contract addresses
│   └── test/              # Contract tests
├── core/                  # Core Django app (patients, appointments)
├── users/                 # User management
├── firewall/              # Security monitoring
├── logs/                  # Application logs
├── scripts/               # Setup and utility scripts
└── requirements.txt       # Python dependencies
```

## Configuration

### Django Settings (caregrid/settings.py)

Key configuration options:

```python
# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Blockchain Configuration
BLOCKCHAIN_PROVIDER_URL = 'http://127.0.0.1:8545'

# Security Thresholds
THREAT_SCORE_THRESHOLDS = {
    'LOW': 40,
    'MEDIUM': 60,
    'HIGH': 80,
}

# Rate Limits
RATE_LIMITS = {
    'UNAUTHENTICATED': 100,  # requests per minute
    'AUTHENTICATED': 500,     # requests per minute
}
```

### Environment Variables

Create a `.env` file in the project root (optional):

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Blockchain
BLOCKCHAIN_PROVIDER_URL=http://127.0.0.1:8545
```

## Running Tests

### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=firewall --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run property-based tests
pytest tests/property/
```

### Smart Contract Tests
```bash
cd caregrid_chain
npx hardhat test
```

## Troubleshooting

### Redis Connection Error
**Problem**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**:
- Ensure Redis is running: `redis-server`
- Check Redis is listening on port 6379: `redis-cli ping`
- On Windows, you may need to use WSL or install Redis for Windows

### Blockchain Connection Error
**Problem**: `Web3.exceptions.ConnectionError: Could not connect to blockchain`

**Solution**:
- Ensure Hardhat node is running: `npx hardhat node`
- Check the node is accessible at http://127.0.0.1:8545
- Verify contract addresses are updated in Django settings

### Contract Not Deployed
**Problem**: `Contract addresses are empty in settings.py`

**Solution**:
- Deploy contracts: `cd caregrid_chain && npm run deploy`
- Update settings: `python scripts/update_contract_addresses.py`

### Port Already in Use
**Problem**: `Error: listen EADDRINUSE: address already in use :::8545`

**Solution**:
- Kill existing Hardhat process: `pkill -f 'hardhat node'`
- Or use a different port in hardhat.config.ts

### Python Dependencies Error
**Problem**: `ModuleNotFoundError: No module named 'web3'`

**Solution**:
- Install dependencies: `pip install -r requirements.txt`
- Ensure you're using the correct Python version: `python --version`

## Development Workflow

1. **Start Services** (in separate terminals):
   ```bash
   # Terminal 1: Redis
   redis-server
   
   # Terminal 2: Blockchain
   cd caregrid_chain && npx hardhat node
   
   # Terminal 3: Django
   python manage.py runserver
   ```

2. **Make Changes**:
   - Edit Python code in `core/`, `users/`, or `firewall/`
   - Edit smart contracts in `caregrid_chain/contracts/`

3. **Test Changes**:
   ```bash
   # Python tests
   pytest
   
   # Contract tests
   cd caregrid_chain && npx hardhat test
   ```

4. **Redeploy Contracts** (if contracts changed):
   ```bash
   cd caregrid_chain
   npm run deploy
   cd ..
   python scripts/update_contract_addresses.py
   ```

## Next Steps

After setup is complete:

1. Review the [Requirements Document](.kiro/specs/blockchain-healthcare-security/requirements.md)
2. Review the [Design Document](.kiro/specs/blockchain-healthcare-security/design.md)
3. Start implementing tasks from [tasks.md](.kiro/specs/blockchain-healthcare-security/tasks.md)
4. Run tests regularly to ensure correctness

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the design and requirements documents
- Check logs in the `logs/` directory

## License

[Your License Here]
