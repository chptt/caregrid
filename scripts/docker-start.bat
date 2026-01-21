@echo off
REM Main startup script for MediChain Docker environment (Windows)
REM This script orchestrates the startup of all services

echo 🏥 Starting MediChain Healthcare Security System
echo ==============================================

REM Clean up any existing containers
echo 🧹 Cleaning up existing containers...
docker-compose down -v

REM Start infrastructure services first
echo 🚀 Starting infrastructure services...
docker-compose up -d redis hardhat

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak > nul

REM Deploy contracts
echo 📜 Deploying smart contracts...
docker-compose up deploy-contracts

REM Run migrations
echo 🗄️ Running database migrations...
docker-compose up migrate

REM Start Django application
echo 🌐 Starting Django application...
docker-compose up -d django

REM Wait for Django to start
echo ⏳ Waiting for Django to start...
timeout /t 20 /nobreak > nul

REM Display service status
echo.
echo 🎉 MediChain system started successfully!
echo ==============================================
echo 📊 Service Status:
docker-compose ps

echo.
echo 🌐 Access Points:
echo   • Django Admin: http://localhost:8000/admin/
echo   • API Endpoints: http://localhost:8000/api/
echo   • Security Dashboard: http://localhost:8000/api/security/dashboard/
echo   • Hardhat Node: http://localhost:8545
echo   • Redis: localhost:6379
echo.
echo 👤 Default Admin Credentials:
echo   • Username: admin
echo   • Password: admin123
echo.
echo 📋 Useful Commands:
echo   • View logs: docker-compose logs -f [service_name]
echo   • Stop system: docker-compose down
echo   • Restart system: docker-compose restart
echo   • View contract addresses: type caregrid_chain\deployments\all-contracts.json
echo.
echo ✅ System is ready for use!

pause