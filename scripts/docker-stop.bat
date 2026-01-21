@echo off
REM Script to gracefully stop MediChain Docker environment (Windows)

echo 🛑 Stopping MediChain Healthcare Security System
echo ==============================================

REM Stop all services
echo ⏹️ Stopping all services...
docker-compose down

echo ✅ MediChain system stopped successfully!
echo.
echo 📋 To restart the system:
echo   scripts\docker-start.bat
echo.
echo 📋 To completely reset (remove all data):
echo   docker-compose down -v

pause