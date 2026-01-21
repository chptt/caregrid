# MediChain Docker Setup

This document provides instructions for running the MediChain Healthcare Security System using Docker containers.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.0 or higher
- At least 4GB RAM available for containers
- Ports 8000, 8545, and 6379 available on your system

## Quick Start

### Option 1: Using Startup Scripts (Recommended)

**Linux/macOS:**
```bash
# Make scripts executable (Linux/macOS only)
chmod +x scripts/docker-*.sh

# Start the entire system
./scripts/docker-start.sh

# View logs
./scripts/docker-logs.sh

# Stop the system
./scripts/docker-stop.sh
```

**Windows:**
```cmd
# Start the entire system
scripts\docker-start.bat

# Stop the system
scripts\docker-stop.bat

# View logs
docker-compose logs -f
```

### Option 2: Manual Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## System Architecture

The Docker setup includes the following services:

### 1. Redis (`redis`)
- **Purpose**: Caching and rate limiting
- **Port**: 6379
- **Image**: redis:7-alpine
- **Health Check**: Redis ping command

### 2. Hardhat Blockchain (`hardhat`)
- **Purpose**: Local Ethereum blockchain node
- **Port**: 8545
- **Image**: node:18-alpine
- **Command**: `npx hardhat node --hostname 0.0.0.0`

### 3. Contract Deployment (`deploy-contracts`)
- **Purpose**: Deploy smart contracts to blockchain
- **Dependencies**: Hardhat node must be healthy
- **Runs once**: Exits after successful deployment

### 4. Database Migration (`migrate`)
- **Purpose**: Run Django database migrations
- **Dependencies**: Redis must be available
- **Runs once**: Exits after successful migration

### 5. Django Application (`django`)
- **Purpose**: Main web application and API
- **Port**: 8000
- **Dependencies**: Redis, Hardhat, and contract deployment
- **Health Check**: HTTP request to admin endpoint

## Service Dependencies

```
Redis ──┐
        ├─→ Django Application
Hardhat ─┴─→ Contract Deployment ──┘
```

## Environment Variables

The following environment variables are configured in docker-compose.yml:

### Django Service
- `DJANGO_SETTINGS_MODULE=caregrid.settings`
- `REDIS_HOST=redis`
- `REDIS_PORT=6379`
- `BLOCKCHAIN_PROVIDER_URL=http://hardhat:8545`
- `DEBUG=False`
- `ALLOWED_HOSTS=localhost,127.0.0.1,django`

## Volumes

### Persistent Data
- `redis_data`: Redis data persistence
- `hardhat_data`: Node.js modules cache
- `./logs`: Application logs (host-mounted)
- `./db.sqlite3`: SQLite database (host-mounted)

### Read-Only Mounts
- `./caregrid_chain/deployments`: Contract deployment files

## Network Configuration

- **Network**: `medichain_network` (bridge)
- **Subnet**: 172.20.0.0/16
- **Internal Communication**: Services communicate using service names

## Access Points

Once the system is running, you can access:

- **Django Admin**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/
- **Security Dashboard**: http://localhost:8000/api/security/dashboard/
- **Patient API**: http://localhost:8000/api/patients/
- **Appointment API**: http://localhost:8000/api/appointments/
- **Hardhat RPC**: http://localhost:8545
- **Redis**: localhost:6379

## Default Credentials

- **Admin Username**: admin
- **Admin Password**: admin123

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   
   # Stop the conflicting service or change ports in docker-compose.yml
   ```

2. **Container Health Check Failing**
   ```bash
   # Check container logs
   docker-compose logs [service_name]
   
   # Check container status
   docker-compose ps
   ```

3. **Contract Deployment Failed**
   ```bash
   # Check deployment logs
   docker-compose logs deploy-contracts
   
   # Manually redeploy
   docker-compose up deploy-contracts
   ```

4. **Django Migration Issues**
   ```bash
   # Check migration logs
   docker-compose logs migrate
   
   # Manually run migrations
   docker-compose run --rm django python manage.py migrate
   ```

### Useful Commands

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f django

# Restart a specific service
docker-compose restart django

# Execute commands in running container
docker-compose exec django python manage.py shell

# View container resource usage
docker stats

# Clean up everything (including volumes)
docker-compose down -v
docker system prune -a
```

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# Manually test endpoints
curl http://localhost:8000/admin/
curl http://localhost:8545
redis-cli -h localhost ping
```

## Development vs Production

### Development Mode
- Uses SQLite database
- Debug mode enabled in Django
- All services run on localhost
- Logs written to ./logs directory

### Production Considerations
- Replace SQLite with PostgreSQL
- Set DEBUG=False
- Use environment-specific settings
- Implement proper secret management
- Add SSL/TLS termination
- Use production-grade Redis configuration
- Implement log aggregation

## Performance Tuning

### Resource Limits
Add resource limits to docker-compose.yml:

```yaml
services:
  django:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Redis Configuration
For production, tune Redis settings:

```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Security Considerations

1. **Network Isolation**: Services communicate only within Docker network
2. **Non-Root User**: Django runs as non-root user in container
3. **Health Checks**: All services monitored for availability
4. **Secret Management**: Use Docker secrets for production
5. **Image Security**: Base images regularly updated

## Monitoring

### Log Aggregation
```bash
# Centralized logging
docker-compose logs -f --tail=100

# Export logs
docker-compose logs --no-color > medichain.log
```

### Metrics Collection
Consider adding monitoring services:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for log analysis

## Backup and Recovery

### Database Backup
```bash
# Backup SQLite database
docker-compose exec django python manage.py dumpdata > backup.json

# Restore from backup
docker-compose exec django python manage.py loaddata backup.json
```

### Redis Backup
```bash
# Redis data is persisted in redis_data volume
docker run --rm -v medichain_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs using `docker-compose logs`
3. Verify all prerequisites are met
4. Check Docker and Docker Compose versions