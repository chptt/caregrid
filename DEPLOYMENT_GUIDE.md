# MediChain Deployment Guide

This guide covers different deployment scenarios for the MediChain blockchain healthcare security system, from local development to production environments.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Multi-Branch Network Setup](#multi-branch-network-setup)
5. [Testing Procedures](#testing-procedures)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Local Development Setup

### Prerequisites

Ensure you have the following installed:

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Redis Server 6.0+**
- **Git**
- **curl** (for testing)

### Step-by-Step Installation

#### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd caregrid

# Make scripts executable (Linux/macOS)
chmod +x scripts/*.sh

# Run automated setup
./scripts/setup.sh  # Linux/macOS
# OR
scripts\setup.bat   # Windows
```

The setup script will:
- Create Python virtual environment
- Install Python dependencies
- Install Node.js dependencies
- Set up environment variables
- Initialize SQLite database
- Run Django migrations

#### 2. Manual Setup (Alternative)

If the automated setup fails, follow these manual steps:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for blockchain
cd caregrid_chain
npm install
cd ..

# Set up environment variables
cp .env.example .env
# Edit .env file with your settings

# Initialize database
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### 3. Start Services

You need to run multiple services. Open separate terminals for each:

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Blockchain:**
```bash
# Linux/macOS
./scripts/start-blockchain.sh

# Windows
scripts\start-blockchain.bat
```

**Terminal 3 - Deploy Contracts:**
```bash
# Wait for blockchain to start, then deploy contracts
cd caregrid_chain
npm run deploy
cd ..

# Update Django with contract addresses
python scripts/update_contract_addresses.py
```

**Terminal 4 - Django Server:**
```bash
# Activate virtual environment if not already active
source venv/bin/activate  # Linux/macOS

# Start Django development server
python manage.py runserver
```

#### 4. Verify Installation

```bash
# Run verification script
python scripts/verify_setup.py

# Expected output:
# ✅ Python dependencies installed
# ✅ Redis connection working
# ✅ Blockchain network accessible
# ✅ Smart contracts deployed
# ✅ Database migrations applied
```

#### 5. Load Test Data (Optional)

```bash
python setup_test_data.py
```

### Development Workflow

#### Making Changes to Smart Contracts

```bash
# 1. Edit contracts in caregrid_chain/contracts/
# 2. Recompile and deploy
cd caregrid_chain
npm run deploy

# 3. Update Django with new addresses
cd ..
python scripts/update_contract_addresses.py

# 4. Restart Django server
python manage.py runserver
```

#### Running Tests

```bash
# Run all Python tests
pytest

# Run with coverage
pytest --cov=core --cov=firewall --cov-report=html

# Run property-based tests only
pytest tests/property/ -v

# Run smart contract tests
cd caregrid_chain
npx hardhat test
```

## Docker Deployment

Docker deployment provides a consistent environment and is recommended for production-like testing.

### Prerequisites

- **Docker 20.0+**
- **Docker Compose 2.0+**

### Quick Start with Docker

```bash
# Clone repository
git clone <repository-url>
cd caregrid

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Docker Services

The `docker-compose.yml` defines these services:

- **web**: Django application server
- **redis**: Redis cache and rate limiting
- **blockchain**: Hardhat local blockchain network
- **nginx**: Reverse proxy (production only)

### Docker Configuration

#### Environment Variables

Create `.env` file for Docker:

```bash
# Copy example
cp .env.example .env

# Edit for Docker environment
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,web
DATABASE_URL=sqlite:///app/db.sqlite3
REDIS_HOST=redis
REDIS_PORT=6379
BLOCKCHAIN_PROVIDER_URL=http://blockchain:8545
```

#### Custom Docker Build

```bash
# Build custom image
docker build -t medichain:latest .

# Run with custom image
docker run -d \
  --name medichain-web \
  -p 8000:8000 \
  -e REDIS_HOST=redis \
  -e BLOCKCHAIN_PROVIDER_URL=http://blockchain:8545 \
  medichain:latest
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f blockchain

# Execute commands in containers
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Rebuild services
docker-compose build
docker-compose up -d --force-recreate

# Clean up
docker-compose down -v  # Removes volumes
docker system prune     # Clean up unused images
```

### Docker Troubleshooting

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs web

# Access container shell
docker-compose exec web bash

# Restart specific service
docker-compose restart web

# Check network connectivity
docker-compose exec web ping redis
docker-compose exec web ping blockchain
```

## Production Deployment

### Architecture Overview

```
Internet
    ↓
Load Balancer (nginx/AWS ALB)
    ↓
┌─────────────────────────────────────┐
│         Application Tier            │
│  ┌─────────────┐ ┌─────────────┐   │
│  │  Django 1   │ │  Django 2   │   │
│  │  (Branch A) │ │  (Branch B) │   │
│  └─────────────┘ └─────────────┘   │
└─────────────────────────────────────┘
    ↓                    ↓
┌─────────────────────────────────────┐
│          Data Tier                  │
│  ┌─────────────┐ ┌─────────────┐   │
│  │    Redis    │ │ Blockchain  │   │
│  │   Cluster   │ │   Network   │   │
│  └─────────────┘ └─────────────┘   │
└─────────────────────────────────────┘
```

### Production Prerequisites

- **Linux server** (Ubuntu 20.04+ recommended)
- **Python 3.11+**
- **Node.js 18+**
- **Redis 6.0+** (or Redis Cloud)
- **PostgreSQL 13+** (recommended over SQLite)
- **nginx** (reverse proxy)
- **SSL certificate**
- **Domain name**

### Production Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm redis-server postgresql postgresql-contrib nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash medichain
sudo usermod -aG sudo medichain
```

#### 2. Database Setup (PostgreSQL)

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE medichain;
CREATE USER medichain WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE medichain TO medichain;
\q
```

#### 3. Application Deployment

```bash
# Switch to application user
sudo su - medichain

# Clone repository
git clone <repository-url> /home/medichain/caregrid
cd /home/medichain/caregrid

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Install Node.js dependencies
cd caregrid_chain
npm install
cd ..
```

#### 4. Environment Configuration

```bash
# Create production environment file
cat > .env << EOF
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://medichain:secure_password_here@localhost/medichain
REDIS_HOST=localhost
REDIS_PORT=6379
BLOCKCHAIN_PROVIDER_URL=http://localhost:8545
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
EOF
```

#### 5. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

#### 6. Blockchain Setup

```bash
# Start blockchain network
cd caregrid_chain
npm run deploy:prod  # Production deployment script
cd ..

# Update contract addresses
python scripts/update_contract_addresses.py
```

#### 7. Systemd Services

Create systemd service files:

**Django Service (`/etc/systemd/system/medichain.service`):**
```ini
[Unit]
Description=MediChain Django Application
After=network.target

[Service]
User=medichain
Group=medichain
WorkingDirectory=/home/medichain/caregrid
Environment=PATH=/home/medichain/caregrid/venv/bin
EnvironmentFile=/home/medichain/caregrid/.env
ExecStart=/home/medichain/caregrid/venv/bin/gunicorn --workers 3 --bind unix:/home/medichain/caregrid/medichain.sock caregrid.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**Blockchain Service (`/etc/systemd/system/medichain-blockchain.service`):**
```ini
[Unit]
Description=MediChain Blockchain Network
After=network.target

[Service]
User=medichain
Group=medichain
WorkingDirectory=/home/medichain/caregrid/caregrid_chain
ExecStart=/usr/bin/npx hardhat node --hostname 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Background Tasks Service (`/etc/systemd/system/medichain-tasks.service`):**
```ini
[Unit]
Description=MediChain Background Tasks
After=network.target

[Service]
User=medichain
Group=medichain
WorkingDirectory=/home/medichain/caregrid
Environment=PATH=/home/medichain/caregrid/venv/bin
EnvironmentFile=/home/medichain/caregrid/.env
ExecStart=/home/medichain/caregrid/venv/bin/python scripts/run_background_tasks.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 8. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable medichain
sudo systemctl enable medichain-blockchain
sudo systemctl enable medichain-tasks

# Start services
sudo systemctl start medichain-blockchain
sleep 10  # Wait for blockchain to start
sudo systemctl start medichain
sudo systemctl start medichain-tasks

# Check status
sudo systemctl status medichain
sudo systemctl status medichain-blockchain
```

#### 9. Nginx Configuration

Create nginx configuration (`/etc/nginx/sites-available/medichain`):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/medichain/caregrid;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/medichain/caregrid/medichain.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/medichain /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

#### 10. SSL Certificate

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Production Monitoring

#### Log Files

```bash
# Application logs
sudo journalctl -u medichain -f

# Blockchain logs
sudo journalctl -u medichain-blockchain -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application-specific logs
tail -f /home/medichain/caregrid/logs/caregrid.log
```

#### Health Checks

Create health check script (`/home/medichain/health_check.sh`):

```bash
#!/bin/bash

# Check Django application
curl -f http://localhost:8000/api/health/ || exit 1

# Check Redis
redis-cli ping || exit 1

# Check blockchain
curl -f http://localhost:8545/ || exit 1

echo "All services healthy"
```

#### Backup Script

Create backup script (`/home/medichain/backup.sh`):

```bash
#!/bin/bash

BACKUP_DIR="/home/medichain/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump medichain > $BACKUP_DIR/db_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/medichain/caregrid

# Backup blockchain data
tar -czf $BACKUP_DIR/blockchain_$DATE.tar.gz /home/medichain/caregrid/caregrid_chain/deployments

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/medichain/backup.sh >> /home/medichain/backup.log 2>&1
```

## Multi-Branch Network Setup

For healthcare networks with multiple hospital branches, each branch runs its own Django instance but shares the same blockchain network.

### Network Architecture

```
Branch A (Hospital A)          Branch B (Hospital B)
┌─────────────────────┐       ┌─────────────────────┐
│  Django Instance    │       │  Django Instance    │
│  Redis Cache        │       │  Redis Cache        │
└─────────┬───────────┘       └─────────┬───────────┘
          │                             │
          └─────────────┬─────────────────┘
                        │
              ┌─────────▼─────────┐
              │ Shared Blockchain │
              │     Network       │
              └───────────────────┘
```

### Branch Setup

#### 1. Shared Blockchain Network

Set up a central blockchain node that all branches connect to:

```bash
# On central server
cd caregrid_chain
npx hardhat node --hostname 0.0.0.0 --port 8545

# Deploy contracts once
npm run deploy
```

#### 2. Branch Configuration

Each branch configures their Django instance to connect to the shared blockchain:

```bash
# Branch A configuration
BLOCKCHAIN_PROVIDER_URL=http://central-blockchain-server:8545
BRANCH_ID=branch_a
BRANCH_NAME="Hospital A"

# Branch B configuration  
BLOCKCHAIN_PROVIDER_URL=http://central-blockchain-server:8545
BRANCH_ID=branch_b
BRANCH_NAME="Hospital B"
```

#### 3. Contract Address Synchronization

All branches must use the same contract addresses:

```bash
# Copy deployment files to all branches
scp caregrid_chain/deployments/*.json branch-a:/path/to/caregrid/caregrid_chain/deployments/
scp caregrid_chain/deployments/*.json branch-b:/path/to/caregrid/caregrid_chain/deployments/
```

#### 4. Network Security

Configure firewall rules to allow blockchain communication:

```bash
# Allow blockchain port from branch IPs
sudo ufw allow from branch-a-ip to any port 8545
sudo ufw allow from branch-b-ip to any port 8545
```

## Testing Procedures

### Pre-Deployment Testing

#### 1. Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=core --cov=firewall --cov-report=html
```

#### 2. Property-Based Tests

```bash
# Run property tests
pytest tests/property/ -v

# Run specific property test
pytest tests/property/test_patient_properties.py -v
```

#### 3. Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Test API endpoints
python test_patient_endpoint.py
python test_appointment_endpoints.py
```

#### 4. Smart Contract Tests

```bash
cd caregrid_chain
npx hardhat test
```

### Post-Deployment Testing

#### 1. Health Check

```bash
# Check all services
curl http://your-domain.com/api/health/

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok", 
    "blockchain": "ok"
  }
}
```

#### 2. API Testing

```bash
# Test patient registration
curl -X POST http://your-domain.com/api/patients/ \
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

# Test security dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://your-domain.com/api/security/dashboard/
```

#### 3. Security Testing

```bash
# Test rate limiting
for i in {1..150}; do
  curl -s http://your-domain.com/api/patients/ > /dev/null &
done
wait

# Should receive 429 responses after limit

# Test IP blocking
curl -X POST http://your-domain.com/api/security/block/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.1.100", "reason": "Test block"}'
```

#### 4. Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 concurrent requests
ab -n 1000 -c 100 http://your-domain.com/api/patients/

# Test with authentication
ab -n 1000 -c 50 -H "Authorization: Bearer $TOKEN" \
  http://your-domain.com/api/patients/
```

### Performance Testing

#### 1. Database Performance

```bash
# Test database queries
python manage.py shell

>>> from django.test.utils import override_settings
>>> from django.db import connection
>>> from core.models import Patient
>>> 
>>> # Test patient creation performance
>>> import time
>>> start = time.time()
>>> for i in range(100):
...     Patient.objects.create(name=f"Patient {i}", ...)
>>> print(f"Created 100 patients in {time.time() - start:.2f}s")
```

#### 2. Blockchain Performance

```bash
cd caregrid_chain
npx hardhat console --network localhost

# Test contract performance
const registry = await ethers.getContractAt("PatientRegistry", "ADDRESS");

// Test batch registrations
const start = Date.now();
for (let i = 0; i < 100; i++) {
  await registry.registerPatient(ethers.utils.randomBytes(32));
}
console.log(`100 registrations in ${Date.now() - start}ms`);
```

## Monitoring and Maintenance

### System Monitoring

#### 1. Service Status Monitoring

Create monitoring script (`/home/medichain/monitor.sh`):

```bash
#!/bin/bash

# Check systemd services
services=("medichain" "medichain-blockchain" "medichain-tasks" "redis" "postgresql" "nginx")

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        # Send alert (email, Slack, etc.)
    fi
done

# Check disk space
df -h | awk '$5 > 80 {print "⚠️  Disk usage high: " $0}'

# Check memory usage
free -m | awk 'NR==2{printf "Memory usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'
```

#### 2. Application Monitoring

```bash
# Monitor request rates
tail -f /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -nr

# Monitor error rates
grep -c "ERROR" /home/medichain/caregrid/logs/caregrid.log

# Monitor threat scores
python manage.py shell -c "
from firewall.models import SecurityLog
import datetime
recent = datetime.datetime.now() - datetime.timedelta(hours=1)
high_threats = SecurityLog.objects.filter(
    timestamp__gte=recent, 
    threat_level='HIGH'
).count()
print(f'High threats in last hour: {high_threats}')
"
```

### Maintenance Tasks

#### 1. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip list --outdated
pip install -U package_name

# Update Node.js packages
cd caregrid_chain
npm audit
npm update
```

#### 2. Database Maintenance

```bash
# Vacuum PostgreSQL database
sudo -u postgres psql medichain -c "VACUUM ANALYZE;"

# Clean old security logs (keep 30 days)
python manage.py shell -c "
from firewall.models import SecurityLog
import datetime
cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
deleted = SecurityLog.objects.filter(timestamp__lt=cutoff).delete()
print(f'Deleted {deleted[0]} old security logs')
"
```

#### 3. Log Rotation

Configure logrotate (`/etc/logrotate.d/medichain`):

```
/home/medichain/caregrid/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 medichain medichain
    postrotate
        systemctl reload medichain
    endscript
}
```

## Troubleshooting

### Common Issues

#### 1. Django Won't Start

```bash
# Check logs
sudo journalctl -u medichain -f

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
# - Permission issues

# Debug steps:
cd /home/medichain/caregrid
source venv/bin/activate
python manage.py check
python manage.py migrate --check
```

#### 2. Blockchain Connection Issues

```bash
# Check blockchain service
sudo systemctl status medichain-blockchain

# Test connection
curl http://localhost:8545/

# Check contract deployments
ls -la caregrid_chain/deployments/

# Redeploy contracts if needed
cd caregrid_chain
npm run deploy
cd ..
python scripts/update_contract_addresses.py
```

#### 3. Redis Connection Issues

```bash
# Check Redis service
sudo systemctl status redis

# Test connection
redis-cli ping

# Check Redis logs
sudo journalctl -u redis -f

# Clear Redis cache if needed
redis-cli FLUSHALL
```

#### 4. High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Common causes:
# - Too many Gunicorn workers
# - Memory leaks in Django
# - Large Redis cache

# Solutions:
# Reduce Gunicorn workers
# Restart services
sudo systemctl restart medichain

# Clear Redis cache
redis-cli FLUSHALL
```

#### 5. SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test nginx configuration
sudo nginx -t

# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"
```

### Performance Issues

#### 1. Slow API Responses

```bash
# Enable Django debug toolbar (development only)
pip install django-debug-toolbar

# Check database queries
python manage.py shell
>>> from django.db import connection
>>> connection.queries

# Profile with cProfile
python -m cProfile manage.py runserver

# Check for N+1 queries
# Use select_related() and prefetch_related()
```

#### 2. High Threat Scores

```bash
# Check threat calculation logic
python manage.py shell -c "
from core.threat_calculator import ThreatScoreCalculator
from django.test import RequestFactory
import redis

redis_client = redis.Redis()
calculator = ThreatScoreCalculator(redis_client, None)

# Test with sample request
factory = RequestFactory()
request = factory.get('/api/patients/')
score, factors = calculator.calculate_threat_score(request, '127.0.0.1')
print(f'Score: {score}, Factors: {factors}')
"
```

### Emergency Procedures

#### 1. Service Recovery

```bash
# Stop all services
sudo systemctl stop medichain
sudo systemctl stop medichain-blockchain
sudo systemctl stop medichain-tasks

# Clear caches
redis-cli FLUSHALL

# Restart in order
sudo systemctl start medichain-blockchain
sleep 10
sudo systemctl start medichain
sudo systemctl start medichain-tasks

# Verify services
sudo systemctl status medichain
```

#### 2. Database Recovery

```bash
# Restore from backup
sudo -u postgres psql

DROP DATABASE medichain;
CREATE DATABASE medichain;
GRANT ALL PRIVILEGES ON DATABASE medichain TO medichain;
\q

# Restore data
sudo -u postgres psql medichain < /home/medichain/backups/db_YYYYMMDD_HHMMSS.sql

# Run migrations
cd /home/medichain/caregrid
source venv/bin/activate
python manage.py migrate
```

#### 3. Blockchain Recovery

```bash
# Stop blockchain service
sudo systemctl stop medichain-blockchain

# Clear blockchain data (if needed)
rm -rf caregrid_chain/cache/
rm -rf caregrid_chain/artifacts/

# Redeploy contracts
cd caregrid_chain
npm run deploy
cd ..
python scripts/update_contract_addresses.py

# Restart services
sudo systemctl start medichain-blockchain
sudo systemctl restart medichain
```

### Getting Help

#### 1. Log Collection

```bash
# Collect all relevant logs
mkdir -p /tmp/medichain-logs
sudo journalctl -u medichain --since "1 hour ago" > /tmp/medichain-logs/django.log
sudo journalctl -u medichain-blockchain --since "1 hour ago" > /tmp/medichain-logs/blockchain.log
cp /home/medichain/caregrid/logs/*.log /tmp/medichain-logs/
cp /var/log/nginx/error.log /tmp/medichain-logs/

# Create archive
tar -czf medichain-logs-$(date +%Y%m%d_%H%M%S).tar.gz -C /tmp medichain-logs
```

#### 2. System Information

```bash
# Collect system info
cat > /tmp/system-info.txt << EOF
System: $(uname -a)
Python: $(python3 --version)
Node.js: $(node --version)
Redis: $(redis-server --version)
PostgreSQL: $(psql --version)
Nginx: $(nginx -v 2>&1)
Disk Space: $(df -h)
Memory: $(free -h)
Services: $(systemctl list-units --type=service --state=running | grep medichain)
EOF
```

For additional support, include these files when reporting issues.

---

This deployment guide covers the most common scenarios. For specific environments or custom requirements, consult the development team or create an issue in the project repository.