# CareGrid

Blockchain-secured healthcare management system with real-time threat detection, IP-based security, and Ethereum smart contract integration.

## Architecture

```
caregrid/
├── caregrid/              Django project configuration
├── core/                  Main application (patients, appointments, blockchain, security)
├── users/                 Custom user model with 14 hospital roles
├── firewall/              Security monitoring and IP management
├── caregrid_chain/        Solidity smart contracts and Hardhat configuration
├── tests/                 Test suite (unit, property-based, integration, API)
├── scripts/               Deployment and utility scripts
├── docs/                  Project documentation
├── infrastructure/        Infrastructure configuration
├── .github/               CI/CD workflows
├── Dockerfile             Multi-stage production build
├── docker-compose.yml     Full-stack service orchestration
└── manage.py              Django entry point
```

## Technology Stack

| Component       | Technology                         |
|-----------------|------------------------------------|
| Backend         | Django 5.2, Django REST Framework  |
| Database        | SQLite (development)               |
| Cache           | Redis 7                            |
| Blockchain      | Hardhat, Solidity 0.8, web3.py     |
| Smart Contracts | OpenZeppelin, TypeChain, ethers.js  |
| Testing         | pytest, Hypothesis, Forge           |
| Containerization| Docker, docker-compose             |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis Server

### Local Development

```bash
# Clone
git clone https://github.com/your-org/caregrid.git
cd caregrid

# Backend setup
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your values

# Database
python manage.py migrate
python setup_test_data.py

# Blockchain (terminal 1)
cd caregrid_chain && npm install && npx hardhat node

# Deploy contracts (terminal 2)
cd caregrid_chain && npx hardhat run scripts/deploy-all.ts --network localhost

# Django server (terminal 3)
python manage.py runserver
```

### Docker

```bash
docker compose up --build
```

This starts Redis, Hardhat node, contract deployment, database migration, and the Django server.

## API Endpoints

### Patient Management
| Method | Endpoint                          | Description          |
|--------|-----------------------------------|----------------------|
| POST   | `/api/patients/`                  | Register patient     |
| GET    | `/api/patients/search/?q=query`   | Search patients      |
| GET    | `/api/patients/<id>/`             | Get patient details  |

### Appointment Management
| Method | Endpoint                              | Description              |
|--------|---------------------------------------|--------------------------|
| POST   | `/api/appointments/`                  | Create appointment       |
| GET    | `/api/appointments/list/`             | List appointments        |
| GET    | `/api/appointments/<id>/`             | Get appointment details  |
| GET    | `/api/appointments/patient/<id>/`     | Patient appointments     |

### Security
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | `/api/security/captcha/`      | Get CAPTCHA challenge    |
| POST   | `/api/security/captcha/`      | Verify CAPTCHA           |
| GET    | `/api/security/dashboard/`    | Security dashboard data  |
| GET    | `/api/security/stats/`        | Security statistics      |
| POST   | `/api/security/block/`        | Block IP (admin)         |
| POST   | `/api/security/unblock/`      | Unblock IP (admin)       |

## Environment Variables

| Variable                          | Default                            | Description                  |
|-----------------------------------|------------------------------------|------------------------------|
| `DJANGO_SECRET_KEY`               | (insecure dev key)                 | Django secret key            |
| `DEBUG`                           | `False`                            | Debug mode                   |
| `ALLOWED_HOSTS`                   | `127.0.0.1,localhost`              | Comma-separated hosts        |
| `REDIS_HOST`                      | `localhost`                        | Redis host                   |
| `REDIS_PORT`                      | `6379`                             | Redis port                   |
| `BLOCKCHAIN_PROVIDER_URL`         | `http://127.0.0.1:8545`            | Blockchain RPC URL           |
| `LOG_LEVEL`                       | `INFO`                             | Logging level                |

See `.env.example` for the complete list.

## Testing

```bash
# All tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Property-based tests
python -m pytest tests/property/ -v

# API tests
python -m pytest tests/api/ -v
```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [API Documentation](docs/API.md)
- [Security Dashboard](docs/SECURITY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Docker Guide](docs/DOCKER.md)

## License

MIT License. See [LICENSE](LICENSE) for details.
